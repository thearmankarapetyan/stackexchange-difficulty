"""Hugging Face metadata-only release packaging."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from stackexchange_difficulty import __version__
from stackexchange_difficulty.provenance import sha256_file, utc_now_iso


class HuggingFaceReleaseError(RuntimeError):
    """Raised when a Hugging Face release action is unsafe or incomplete."""


@dataclass(frozen=True)
class ReleaseFile:
    source: Path
    destination: Path
    content_class: str


@dataclass(frozen=True)
class HuggingFaceReleaseResult:
    release_dir: Path
    manifest: Path
    files: list[str]

    def to_payload(self) -> dict[str, Any]:
        return {
            "ok": True,
            "release_dir": str(self.release_dir),
            "manifest": str(self.manifest),
            "files": self.files,
        }


@dataclass(frozen=True)
class HuggingFaceUploadResult:
    ok: bool
    dry_run: bool
    commands: list[list[str]]

    def to_payload(self) -> dict[str, Any]:
        return {"ok": self.ok, "dry_run": self.dry_run, "commands": self.commands}


CredentialScanner = Callable[[Path], None]
Runner = Callable[..., subprocess.CompletedProcess[str]]
Which = Callable[[str], str | None]

TEXT_SUFFIXES = {".json", ".md", ".txt", ".tsv", ".csv", ".yml", ".yaml", ".sql"}
CREDENTIAL_PATTERNS = (
    re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|hf_token)\s*[:=]\s*\S+"),
    re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
)
SITE_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def pilot_artifact_suffix(*, pilot_date: str, site_slug: str | None = None) -> str:
    if not site_slug:
        return pilot_date
    return f"{normalize_release_site_slug(site_slug)}_{pilot_date}"


def normalize_release_site_slug(value: str) -> str:
    slug = value.strip().lower()
    if not SITE_SLUG_PATTERN.fullmatch(slug) or ".." in slug:
        raise HuggingFaceReleaseError(
            "site slug must contain only letters, digits, and hyphens; "
            "spaces, slashes, dots, and path traversal are not allowed"
        )
    return slug


def prepare_hf_release(
    *,
    project_root: Path,
    pilot_date: str,
    repo_id: str,
    out_dir: Path,
    site_slug: str | None = None,
    scanner: CredentialScanner | None = None,
) -> HuggingFaceReleaseResult:
    if "/" not in repo_id:
        raise HuggingFaceReleaseError("repo-id must use the NAMESPACE/REPO format")
    scanner = scanner or assert_no_credential_markers
    root = project_root.resolve()
    release_dir = out_dir.resolve()
    dataset_dir = root / "reports/datasets/stackexchange-difficulty"
    artifact_suffix = pilot_artifact_suffix(pilot_date=pilot_date, site_slug=site_slug)
    provenance = dataset_dir / f"provenance_sede_pilot_{artifact_suffix}.json"
    audit = dataset_dir / "audits" / f"sede_pilot_{artifact_suffix}.md"
    _require_file(provenance, "dated pilot provenance")
    _require_file(audit, "dated pilot audit")
    provenance_record = json.loads(provenance.read_text(encoding="utf-8"))
    source_site_slug = provenance_record.get("source_site_slug") or (
        normalize_release_site_slug(site_slug) if site_slug else "stackoverflow"
    )
    source_site_name = provenance_record.get("source_site_name") or (
        "Stack Overflow" if not site_slug else source_site_slug
    )

    files = [
        ReleaseFile(
            source=root / "data/processed/stackexchange-difficulty/data_dictionary.tsv",
            destination=Path("data_dictionary.tsv"),
            content_class="data_dictionary",
        ),
        ReleaseFile(
            source=provenance,
            destination=Path("provenance") / provenance.name,
            content_class="provenance",
        ),
        ReleaseFile(
            source=audit,
            destination=Path("audits") / audit.name,
            content_class="aggregate_audit",
        ),
        ReleaseFile(
            source=dataset_dir / "validation_protocol.md",
            destination=Path("docs/validation_protocol.md"),
            content_class="protocol",
        ),
        ReleaseFile(
            source=dataset_dir / "completion_criteria.md",
            destination=Path("docs/completion_criteria.md"),
            content_class="protocol",
        ),
        ReleaseFile(
            source=dataset_dir / "sede_export_checklist.md",
            destination=Path("docs/sede_export_checklist.md"),
            content_class="protocol",
        ),
        ReleaseFile(
            source=root / "reports/stackexchange_exploitation_report.md",
            destination=Path("docs/stackexchange_exploitation_report.md"),
            content_class="methodology_report",
        ),
    ]
    for file in files:
        _require_file(file.source, file.content_class)
        validate_release_source_path(file.source, root)
        scanner(file.source)

    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True)
    release_files: list[ReleaseFile] = []
    for file in files:
        target = release_dir / file.destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file.source, target)
        release_files.append(
            ReleaseFile(
                source=file.source,
                destination=file.destination,
                content_class=file.content_class,
            )
        )

    card_path = release_dir / "README.md"
    card_path.write_text(
        build_dataset_card(
            repo_id=repo_id,
            pilot_date=pilot_date,
            source_site_name=source_site_name,
        ),
        encoding="utf-8",
    )
    scanner(card_path)
    release_files.append(
        ReleaseFile(
            source=card_path,
            destination=Path("README.md"),
            content_class="dataset_card",
        )
    )

    license_notes_path = release_dir / "docs/license_and_attribution_notes.md"
    license_notes_path.write_text(build_license_notes(), encoding="utf-8")
    scanner(license_notes_path)
    release_files.append(
        ReleaseFile(
            source=license_notes_path,
            destination=Path("docs/license_and_attribution_notes.md"),
            content_class="license_attribution_notes",
        )
    )

    manifest_path = release_dir / "hf_release_manifest.json"
    manifest = build_release_manifest(
        repo_id=repo_id,
        pilot_date=pilot_date,
        source_site_slug=source_site_slug,
        source_site_name=source_site_name,
        release_dir=release_dir,
        release_files=release_files,
        project_root=root,
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    scanner(manifest_path)

    relative_files = sorted(
        str(path.relative_to(release_dir))
        for path in release_dir.rglob("*")
        if path.is_file()
    )
    return HuggingFaceReleaseResult(
        release_dir=release_dir,
        manifest=manifest_path,
        files=relative_files,
    )


def upload_hf_release(
    *,
    release_dir: Path,
    repo_id: str,
    apply: bool = False,
    runner: Runner = subprocess.run,
    which: Which = shutil.which,
    commit_message: str = "Publish metadata-only Stack Exchange difficulty release",
) -> HuggingFaceUploadResult:
    if "/" not in repo_id:
        raise HuggingFaceReleaseError("repo-id must use the NAMESPACE/REPO format")
    if not release_dir.exists():
        raise HuggingFaceReleaseError(f"release directory does not exist: {release_dir}")

    commands = [
        ["hf", "auth", "whoami"],
        ["hf", "repos", "create", repo_id, "--type", "dataset", "--private", "--exist-ok"],
        [
            "hf",
            "upload",
            repo_id,
            str(release_dir),
            ".",
            "--type",
            "dataset",
            "--private",
            "--commit-message",
            commit_message,
        ],
    ]
    if not apply:
        return HuggingFaceUploadResult(ok=True, dry_run=True, commands=commands[1:])
    if which("hf") is None:
        raise HuggingFaceReleaseError("hf CLI is not installed or not on PATH")

    for command in commands:
        result = runner(command, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise HuggingFaceReleaseError(
                f"HF command failed: {' '.join(command)}"
                + (f"\n{detail}" if detail else "")
            )
    return HuggingFaceUploadResult(ok=True, dry_run=False, commands=commands)


def build_dataset_card(
    *,
    repo_id: str,
    pilot_date: str,
    source_site_name: str = "Stack Overflow",
) -> str:
    return f"""---
license: other
pretty_name: Stack Exchange Difficulty Corpus Metadata Release
tags:
- stack-exchange
- question-answering
- corpus-construction
- reproducibility
- technical-question-difficulty
---

# Stack Exchange Difficulty Corpus Metadata Release

This private-first dataset repository package documents a Stack Exchange
difficulty corpus pilot for `{repo_id}`. It is a metadata-only release for the
{source_site_name} pilot dated `{pilot_date}`.

## Contents

The release contains provenance, aggregate audit material, a data dictionary,
validation/completion protocols, and the methodological report. It does not
contain raw SEDE exports, processed Stack Exchange post text, JSONL thread
records, comments, usernames, credentials, or browser-download artifacts.

## Methodology

The project follows the report protocol: a {source_site_name} SEDE pilot
validates field availability, sampling strata, provenance, and audit checks
before any larger Data Dump planning. API access remains enrichment-only, and
HTML scraping is excluded by default.

## Licensing And Attribution

Stack Exchange user contributions are governed by the applicable Stack Exchange
terms and per-post Creative Commons Attribution-ShareAlike `ContentLicense`.
Because this v1 package is metadata-only, it does not redistribute post bodies
or answers. Any future content-bearing release must preserve attribution and
license metadata at record level before upload.

## Limitations

This package is not a complete corpus and is not suitable for model training.
It supports reproducibility review of the construction workflow and pilot audit
only. Public or gated release requires a later explicit decision.
"""


def build_license_notes() -> str:
    return """# License And Attribution Notes

This Hugging Face package is metadata-only. It does not redistribute Stack
Exchange question bodies, answer bodies, comments, usernames, code snippets, or
JSONL thread records.

Future content-bearing releases must preserve the applicable Stack Exchange
terms, per-record `ContentLicense`, attribution fields, source URL, source
site, post identifiers, retrieval/export date, transformation history, and
hashes before upload.

Publicly accessible Stack Exchange user contributions are licensed under
Creative Commons Attribution-ShareAlike, with the applicable version determined
by contribution date. The project audit must confirm that attribution and
license metadata are complete before any non-metadata release.
"""


def build_release_manifest(
    *,
    repo_id: str,
    pilot_date: str,
    source_site_slug: str,
    source_site_name: str,
    release_dir: Path,
    release_files: list[ReleaseFile],
    project_root: Path,
) -> dict[str, Any]:
    files = []
    for file in release_files:
        target = release_dir / file.destination
        files.append(
            {
                "path": str(file.destination),
                "source_path": _display_path(file.source, project_root),
                "content_class": file.content_class,
                "sha256": f"sha256:{sha256_file(target)}",
                "bytes": target.stat().st_size,
            }
        )
    return {
        "repo_id": repo_id,
        "pilot_date": pilot_date,
        "source_site_slug": source_site_slug,
        "source_site_name": source_site_name,
        "created_at": utc_now_iso(),
        "package_version": __version__,
        "git_commit": current_git_commit(project_root),
        "release_policy": "metadata_only_private_first",
        "files": sorted(files, key=lambda row: row["path"]),
    }


def validate_release_source_path(path: Path, project_root: Path) -> None:
    try:
        relative = path.resolve().relative_to(project_root.resolve())
    except ValueError:
        return
    text = relative.as_posix()
    if text.startswith("data/raw/"):
        raise HuggingFaceReleaseError(f"raw data file cannot be staged: {relative}")
    if text.startswith("data/processed/") and text != (
        "data/processed/stackexchange-difficulty/data_dictionary.tsv"
    ):
        raise HuggingFaceReleaseError(f"processed data file cannot be staged: {relative}")


def assert_no_credential_markers(path: Path) -> None:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return
    for pattern in CREDENTIAL_PATTERNS:
        if pattern.search(text):
            raise HuggingFaceReleaseError(f"credential-like marker found in {path}")


def current_git_commit(project_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def _display_path(path: Path, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path)


def _require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise HuggingFaceReleaseError(f"missing required {label}: {path}")


def command_list_to_json(commands: Sequence[Sequence[str]]) -> str:
    return json.dumps([list(command) for command in commands], sort_keys=True)
