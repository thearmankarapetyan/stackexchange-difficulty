"""Browser-assisted SEDE pilot workflow orchestration."""

from __future__ import annotations

import csv
import shutil
import subprocess
import time
import webbrowser
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from stackexchange_difficulty.derive import derive_indicators
from stackexchange_difficulty.jsonl import build_threads, write_jsonl
from stackexchange_difficulty.provenance import (
    finalize_processed_hashes,
    load_provenance,
    sha256_file,
    write_provenance_json,
)
from stackexchange_difficulty.sede import normalize_sede_export, validate_sede_export
from stackexchange_difficulty.validation import (
    read_table,
    validate_dataset,
    write_validation_report,
)

SEDE_QUERY_URL = "https://data.stackexchange.com/stackoverflow/query/new"
SUPPORTED_EXPORT_SUFFIXES = {".csv", ".tsv"}
PARTIAL_EXPORT_SUFFIXES = {".crdownload", ".part", ".tmp", ".download"}


class SedePilotError(RuntimeError):
    """Raised when the assisted SEDE pilot cannot continue safely."""


@dataclass(frozen=True)
class SedePilotConfig:
    project_root: Path
    pilot_date: str
    export_path: Path | None = None
    download_dir: Path | None = None
    open_browser: bool = False
    timeout_seconds: float = 1800
    min_rows: int = 5000
    max_rows: int = 10000
    query_url: str = SEDE_QUERY_URL


@dataclass(frozen=True)
class SedePilotResult:
    ok: bool
    raw_export: Path
    provenance: Path
    processed_dir: Path | None
    derived_dir: Path | None
    audit: Path
    rows: int
    issues: list[dict[str, Any]]

    def to_payload(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "raw_export": str(self.raw_export),
            "provenance": str(self.provenance),
            "processed_dir": str(self.processed_dir) if self.processed_dir else None,
            "derived_dir": str(self.derived_dir) if self.derived_dir else None,
            "audit": str(self.audit),
            "rows": self.rows,
            "issues": self.issues,
        }


def resolve_pilot_date(value: str) -> str:
    if value == "auto":
        return datetime.now().date().isoformat()
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise SedePilotError("pilot date must be 'auto' or YYYY-MM-DD") from exc
    return value


def prepare_browser_session(
    *,
    query_url: str = SEDE_QUERY_URL,
    opener: Callable[[str], bool] = webbrowser.open,
) -> dict[str, Any]:
    opened = opener(query_url)
    return {
        "opened": bool(opened),
        "query_url": query_url,
    }


def wait_for_sede_export(
    download_dir: Path,
    *,
    start_time: float,
    timeout_seconds: float,
    poll_interval: float = 1.0,
    stable_seconds: float = 2.0,
) -> Path:
    if not download_dir.is_dir():
        raise SedePilotError(f"download directory does not exist: {download_dir}")
    deadline = time.monotonic() + timeout_seconds
    last_sizes: dict[Path, tuple[int, float]] = {}
    while time.monotonic() < deadline:
        supported, unsupported = _stable_download_candidates(
            download_dir,
            start_time=start_time,
            stable_seconds=stable_seconds,
            last_sizes=last_sizes,
        )
        if len(supported) == 1:
            return supported[0]
        if len(supported) > 1:
            names = ", ".join(path.name for path in supported)
            raise SedePilotError(f"multiple SEDE export candidates found: {names}")
        if unsupported:
            names = ", ".join(path.name for path in unsupported)
            raise SedePilotError(f"new download has unsupported suffix: {names}")
        time.sleep(poll_interval)
    raise SedePilotError("timed out waiting for a SEDE CSV/TSV export")


def run_sede_pilot(config: SedePilotConfig) -> SedePilotResult:
    root = config.project_root.resolve()
    query_path = root / "reports/datasets/stackexchange-difficulty/sede_pilot_query.sql"
    template_path = (
        root
        / "reports/datasets/stackexchange-difficulty/provenance_sede_pilot_template.json"
    )
    audit_path = (
        root
        / f"reports/datasets/stackexchange-difficulty/audits/"
        f"sede_pilot_{config.pilot_date}.md"
    )
    provenance_path = (
        root
        / f"reports/datasets/stackexchange-difficulty/"
        f"provenance_sede_pilot_{config.pilot_date}.json"
    )

    source_export = _resolve_source_export(config, query_path)
    raw_export = _copy_raw_export(source_export, root, config.pilot_date)
    raw_hash = sha256_file(raw_export)
    _write_hash_manifest(raw_export.with_name(f"{raw_export.name}.sha256"), [raw_export])

    export = read_table(raw_export, name="sede_export")
    preflight_issues = validate_sede_export(export)
    row_issue = _row_count_issue(len(export.rows), config.min_rows, config.max_rows)
    issues = [issue.__dict__ for issue in preflight_issues]
    if row_issue:
        issues.append(row_issue)
    if issues:
        _write_audit(
            audit_path,
            _build_audit(
                pilot_date=config.pilot_date,
                raw_export=raw_export,
                provenance_path=provenance_path,
                raw_hash=raw_hash,
                rows=len(export.rows),
                export_rows=export.rows,
                processed_dir=None,
                derived_dir=None,
                validation_report=None,
                derived_rows=[],
                issues=issues,
                decision="not ready; preflight failed before ingestion",
                root=root,
            ),
        )
        return SedePilotResult(
            ok=False,
            raw_export=raw_export,
            provenance=provenance_path,
            processed_dir=None,
            derived_dir=None,
            audit=audit_path,
            rows=len(export.rows),
            issues=issues,
        )

    provenance = _build_pilot_provenance(
        template_path,
        pilot_date=config.pilot_date,
        raw_export=raw_export,
        raw_hash=raw_hash,
        root=root,
    )
    write_provenance_json(provenance, provenance_path)

    processed_dir = (
        root / f"data/processed/stackexchange-difficulty/pilot-{config.pilot_date}"
    )
    processed_dir.mkdir(parents=True, exist_ok=True)
    questions, answers, comments = normalize_sede_export(export)
    validation_report = validate_dataset(
        questions,
        answers=answers,
        comments=comments,
        provenance=provenance,
    )
    write_validation_report(validation_report, processed_dir / "validation_report.json")
    if not validation_report.ok:
        issues = [issue.__dict__ for issue in validation_report.issues]
        _write_audit(
            audit_path,
            _build_audit(
                pilot_date=config.pilot_date,
                raw_export=raw_export,
                provenance_path=provenance_path,
                raw_hash=raw_hash,
                rows=len(export.rows),
                export_rows=export.rows,
                processed_dir=processed_dir,
                derived_dir=None,
                validation_report=validation_report.to_dict(),
                derived_rows=[],
                issues=issues,
                decision="not ready; normalized validation failed",
                root=root,
            ),
        )
        return SedePilotResult(
            ok=False,
            raw_export=raw_export,
            provenance=provenance_path,
            processed_dir=processed_dir,
            derived_dir=None,
            audit=audit_path,
            rows=len(export.rows),
            issues=issues,
        )

    _write_tsv(questions.rows, processed_dir / "questions.tsv", list(questions.columns))
    _write_tsv(answers.rows, processed_dir / "answers.tsv", list(answers.columns))
    _write_tsv(comments.rows, processed_dir / "comments.tsv", list(comments.columns))
    write_provenance_json(provenance, processed_dir / "provenance.json")
    processed_manifest = processed_dir / "processed-output.sha256"
    _write_hash_manifest(
        processed_manifest,
        [
            processed_dir / "questions.tsv",
            processed_dir / "answers.tsv",
            processed_dir / "comments.tsv",
            processed_dir / "validation_report.json",
        ],
    )

    finalized_provenance = finalize_processed_hashes(provenance, processed_manifest)
    finalized_provenance["processed_hash_manifest"] = _display_path(
        processed_manifest, root
    )
    write_provenance_json(finalized_provenance, provenance_path)
    write_provenance_json(finalized_provenance, processed_dir / "provenance.json")

    finalized_report = validate_dataset(
        questions,
        answers=answers,
        comments=comments,
        provenance=finalized_provenance,
    )
    derived_dir = (
        root / f"data/processed/stackexchange-difficulty/pilot-{config.pilot_date}-derived"
    )
    derived_dir.mkdir(parents=True, exist_ok=True)
    write_validation_report(finalized_report, derived_dir / "validation_report.json")
    if not finalized_report.ok:
        issues = [issue.__dict__ for issue in finalized_report.issues]
        _write_audit(
            audit_path,
            _build_audit(
                pilot_date=config.pilot_date,
                raw_export=raw_export,
                provenance_path=provenance_path,
                raw_hash=raw_hash,
                rows=len(export.rows),
                export_rows=export.rows,
                processed_dir=processed_dir,
                derived_dir=derived_dir,
                validation_report=finalized_report.to_dict(),
                derived_rows=[],
                issues=issues,
                decision="not ready; finalized provenance validation failed",
                root=root,
            ),
        )
        return SedePilotResult(
            ok=False,
            raw_export=raw_export,
            provenance=provenance_path,
            processed_dir=processed_dir,
            derived_dir=derived_dir,
            audit=audit_path,
            rows=len(export.rows),
            issues=issues,
        )

    indicators = derive_indicators(questions, answers=answers, comments=comments)
    _write_tsv(
        indicators,
        derived_dir / "derived_thread_indicators.tsv",
        list(indicators[0]) if indicators else [],
    )
    threads = build_threads(
        questions,
        answers=answers,
        comments=comments,
        indicators=indicators,
        provenance=finalized_provenance,
    )
    write_jsonl(threads, derived_dir / "threads.jsonl")
    _write_hash_manifest(
        derived_dir / "derived-output.sha256",
        [
            derived_dir / "derived_thread_indicators.tsv",
            derived_dir / "threads.jsonl",
            derived_dir / "validation_report.json",
        ],
    )

    _write_audit(
        audit_path,
        _build_audit(
            pilot_date=config.pilot_date,
            raw_export=raw_export,
            provenance_path=provenance_path,
            raw_hash=raw_hash,
            rows=len(export.rows),
            export_rows=export.rows,
            processed_dir=processed_dir,
            derived_dir=derived_dir,
            validation_report=finalized_report.to_dict(),
            derived_rows=indicators,
            issues=[],
            decision=(
                "pipeline complete; manual inspection still required before larger "
                "Data Dump planning"
            ),
            root=root,
        ),
    )
    return SedePilotResult(
        ok=True,
        raw_export=raw_export,
        provenance=provenance_path,
        processed_dir=processed_dir,
        derived_dir=derived_dir,
        audit=audit_path,
        rows=len(export.rows),
        issues=[],
    )


def _resolve_source_export(config: SedePilotConfig, query_path: Path) -> Path:
    if config.export_path:
        return config.export_path
    if not config.open_browser:
        raise SedePilotError("run-sede-pilot requires --export or --open-browser")
    prepare_browser_session(
        query_url=config.query_url,
    )
    print(f"SEDE query file: {query_path}")
    print("Paste the SQL from that file into the SEDE editor after the page opens.")
    print(f"Opened SEDE query page: {config.query_url}")
    download_dir = config.download_dir or Path.home() / "Downloads"
    return wait_for_sede_export(
        download_dir,
        start_time=time.time(),
        timeout_seconds=config.timeout_seconds,
    )


def _copy_raw_export(source_export: Path, root: Path, pilot_date: str) -> Path:
    source = source_export.resolve()
    if source.suffix.lower() not in SUPPORTED_EXPORT_SUFFIXES:
        raise SedePilotError("SEDE export must use a .csv or .tsv suffix")
    target = (
        root
        / "data/raw/stackexchange-difficulty"
        / f"sede-pilot-{pilot_date}{source.suffix.lower()}"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    if source == target.resolve():
        return target
    if target.exists():
        raise SedePilotError(f"raw pilot export already exists: {target}")
    shutil.copy2(source, target)
    return target


def _build_pilot_provenance(
    template_path: Path,
    *,
    pilot_date: str,
    raw_export: Path,
    raw_hash: str,
    root: Path,
) -> dict[str, Any]:
    record = load_provenance(template_path)
    record["dataset_version"] = f"sede-pilot-{pilot_date}"
    record["source_method"] = "sede_pilot_export"
    record["source_version"] = "SEDE snapshot visible at export time"
    record["query_or_dump_file"] = (
        "reports/datasets/stackexchange-difficulty/sede_pilot_query.sql"
    )
    record["export_identifier"] = _display_path(raw_export, root)
    record["access_date"] = pilot_date
    record["official_source_checked_at"] = pilot_date
    record["source_url_checked_at"] = {
        "stack_exchange_api_docs": pilot_date,
        "stack_exchange_data_dump_help": pilot_date,
        "stack_exchange_licensing_help": pilot_date,
        "stack_exchange_schema_meta": pilot_date,
        "stack_exchange_sede_help": pilot_date,
    }
    record["license"] = "CC BY-SA, version determined by each exported post ContentLicense"
    record["raw_export_hash"] = f"sha256:{raw_hash}"
    record["processed_output_hash"] = "sha256:pending-before-processing"
    record["output_hash"] = "sha256:pending-before-processing"
    return record


def _row_count_issue(rows: int, min_rows: int, max_rows: int) -> dict[str, Any] | None:
    if min_rows <= rows <= max_rows:
        return None
    return {
        "code": "row_count_out_of_range",
        "message": f"SEDE export row count {rows} is outside {min_rows}-{max_rows}.",
        "row_id": None,
    }


def _stable_download_candidates(
    download_dir: Path,
    *,
    start_time: float,
    stable_seconds: float,
    last_sizes: dict[Path, tuple[int, float]],
) -> tuple[list[Path], list[Path]]:
    supported: list[Path] = []
    unsupported: list[Path] = []
    now = time.monotonic()
    for path in download_dir.iterdir():
        if not path.is_file() or path.suffix.lower() in PARTIAL_EXPORT_SUFFIXES:
            continue
        if path.stat().st_mtime < start_time:
            continue
        size = path.stat().st_size
        previous_size, previous_seen = last_sizes.get(path, (-1, now))
        if previous_size != size:
            last_sizes[path] = (size, now)
            continue
        if now - previous_seen < stable_seconds:
            continue
        if path.suffix.lower() in SUPPORTED_EXPORT_SUFFIXES:
            supported.append(path)
        else:
            unsupported.append(path)
    return sorted(supported), sorted(unsupported)


def _write_hash_manifest(path: Path, files: list[Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{sha256_file(file_path)}  {file_path}\n" for file_path in files]
    path.write_text("".join(lines), encoding="utf-8")


def _write_tsv(rows: list[dict[str, Any]], path: Path, fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _write_audit(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _build_audit(
    *,
    pilot_date: str,
    raw_export: Path,
    provenance_path: Path,
    raw_hash: str,
    rows: int,
    export_rows: list[dict[str, Any]],
    processed_dir: Path | None,
    derived_dir: Path | None,
    validation_report: dict[str, Any] | None,
    derived_rows: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    decision: str,
    root: Path,
) -> str:
    issue_counts = Counter(issue["code"] for issue in issues)
    validation_issues = Counter(
        issue["code"] for issue in (validation_report or {}).get("issues", [])
    )
    all_issue_counts = issue_counts + validation_issues
    row_count_inside_target = (
        "yes" if "row_count_out_of_range" not in issue_counts else "no"
    )
    accepted_answer_failures = (
        all_issue_counts["accepted_answer_missing"]
        + all_issue_counts["accepted_answer_parent_mismatch"]
        + all_issue_counts["accepted_answer_flag_mismatch"]
    )
    provenance_failures = (
        all_issue_counts["provenance_missing_required_key"]
        + all_issue_counts["provenance_missing_source_identifier"]
    )
    source_distributions = _source_distribution_summary(export_rows)
    distributions = _distribution_summary(derived_rows)
    processed_questions = processed_dir / "questions.tsv" if processed_dir else None
    derived_jsonl = derived_dir / "threads.jsonl" if derived_dir else None
    derived_indicators = (
        derived_dir / "derived_thread_indicators.tsv" if derived_dir else None
    )
    derived_hash = derived_dir / "derived-output.sha256" if derived_dir else None
    return "\n".join(
        [
            "# SEDE Pilot Audit",
            "",
            f"Pilot date: `{pilot_date}`",
            "",
            "## Source And Scope",
            "",
            "- Source: Stack Overflow SEDE.",
            "- Query file: "
            "`reports/datasets/stackexchange-difficulty/sede_pilot_query.sql`.",
            f"- Raw export: `{_display_path(raw_export, root)}`.",
            f"- Provenance file: `{_display_path(provenance_path, root)}`.",
            f"- Raw export hash: `sha256:{raw_hash}`.",
            "- No API crawling, HTML scraping, Data Dump download, credential "
            "handling, or real corpus release was performed for this pilot.",
            "",
            "## Preflight",
            "",
            f"- Raw export suffix: `{raw_export.suffix}`.",
            f"- Row count: {rows}.",
            f"- Expected columns matched: {'yes' if not issue_counts else 'no'}.",
            f"- Row count inside target: {row_count_inside_target}.",
            f"- Raw export ignored by Git: {_git_ignore_text(raw_export, root)}.",
            "- Processed question table ignored by Git: "
            f"{_git_ignore_text(processed_questions, root)}.",
            f"- Derived JSONL ignored by Git: {_git_ignore_text(derived_jsonl, root)}.",
            "",
            "## Validation Summary",
            "",
            f"- Question rows: {_row_count(validation_report, 'questions')}.",
            f"- Answer rows: {_row_count(validation_report, 'answers')}.",
            f"- Comment rows: {_row_count(validation_report, 'comments')}.",
            f"- Duplicate `question_id` failures: {all_issue_counts['duplicate_question_id']}.",
            f"- Artificial post ID failures: {all_issue_counts['artificial_post_id']}.",
            f"- Accepted-answer consistency failures: {accepted_answer_failures}.",
            f"- Missing-column failures: {all_issue_counts['missing_required_columns']}.",
            f"- Provenance failures: {provenance_failures}.",
            "",
            "## Distribution Summary",
            "",
            f"- Answered/unanswered balance: {distributions['answered']}.",
            f"- Accepted/no-accepted balance: {distributions['accepted']}.",
            f"- Closure coverage: {distributions['closed']}.",
            f"- Duplicate coverage: {distributions['duplicate']}.",
            f"- Tag-family distribution: {source_distributions['tag_family']}.",
            f"- Tag-popularity buckets: {distributions['tag_buckets']}.",
            f"- Time-period distribution: {source_distributions['time_period']}.",
            f"- Timing coverage: {distributions['timing']}.",
            "",
            "## Derived Outputs",
            "",
            "- Pending provenance output hashes finalized before derivation: "
            f"{'yes' if derived_dir else 'no'}.",
            f"- `derived_thread_indicators.tsv` produced: {_exists_text(derived_indicators)}.",
            f"- `threads.jsonl` produced: {_exists_text(derived_jsonl)}.",
            "- Derived output hash summary: "
            f"`{_display_path(derived_hash, root) if derived_hash else 'not produced'}`.",
            "",
            "## Manual Inspection",
            "",
            "Manual inspection is not automated. Inspect at least 100 local records "
            "before using this pilot as a scaling decision. This tracked audit must "
            "not include real titles, post bodies, answer text, code snippets, "
            "comments, usernames, credentials, or other copied user content.",
            "",
            "- Comments included in this pilot export: no; the current SEDE pilot "
            "path writes an empty comments table unless a separate comment export "
            "is documented.",
            "",
            "## Decision",
            "",
            f"- Decision: {decision}.",
            "",
        ]
    )


def _source_distribution_summary(rows: list[dict[str, Any]]) -> dict[str, str]:
    if not rows:
        return {
            "tag_family": "not produced",
            "time_period": "not produced",
        }
    return {
        "tag_family": _format_counter(
            Counter(str(row.get("tag_family", "") or "missing") for row in rows)
        ),
        "time_period": _format_counter(
            Counter(str(row.get("time_period", "") or "missing") for row in rows)
        ),
    }


def _distribution_summary(rows: list[dict[str, Any]]) -> dict[str, str]:
    if not rows:
        return {
            "answered": "not produced",
            "accepted": "not produced",
            "closed": "not produced",
            "duplicate": "not produced",
            "tag_buckets": "not produced",
            "timing": "not produced",
        }
    answered = Counter(_bool_text(row.get("has_answer")) for row in rows)
    accepted = Counter(_bool_text(row.get("has_accepted_answer")) for row in rows)
    closed = Counter(_bool_text(row.get("is_closed")) for row in rows)
    duplicate = Counter(_bool_text(row.get("is_duplicate")) for row in rows)
    tag_buckets = Counter(str(row.get("tag_popularity_bucket", "")) for row in rows)
    timing_available = sum(
        1 for row in rows if row.get("time_to_first_answer_hours") not in {None, ""}
    )
    return {
        "answered": _format_counter(answered),
        "accepted": _format_counter(accepted),
        "closed": _format_counter(closed),
        "duplicate": _format_counter(duplicate),
        "tag_buckets": _format_counter(tag_buckets),
        "timing": f"{timing_available}/{len(rows)} with first-answer timing",
    }


def _format_counter(counter: Counter[str]) -> str:
    return ", ".join(f"{key}={value}" for key, value in sorted(counter.items()))


def _bool_text(value: Any) -> str:
    return str(bool(value)).lower() if isinstance(value, bool) else str(value).lower()


def _row_count(validation_report: dict[str, Any] | None, table: str) -> str:
    if not validation_report:
        return "not produced"
    return str(validation_report.get("row_counts", {}).get(table, "not produced"))


def _exists_text(path: Path | None) -> str:
    return "yes" if path and path.exists() else "no"


def _git_ignore_text(path: Path | None, root: Path) -> str:
    if path is None:
        return "not produced"
    result = subprocess.run(
        ["git", "check-ignore", str(path)],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    return "yes" if result.returncode == 0 else "no"


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)
