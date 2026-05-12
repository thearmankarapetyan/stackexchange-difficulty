from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

from stackexchange_difficulty.hf_release import (
    HuggingFaceReleaseError,
    validate_release_source_path,
)


def test_prepare_hf_release_cli_writes_metadata_only_package(tmp_path):
    project_root = make_release_project(tmp_path)
    release_dir = tmp_path / "release"

    result = run_cli(
        [
            "prepare-hf-release",
            "--pilot-date",
            "2026-05-12",
            "--repo-id",
            "namespace/stackexchange-difficulty",
            "--out-dir",
            str(release_dir),
            "--project-root",
            str(project_root),
        ]
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["ok"] is True
    assert (release_dir / "README.md").exists()
    assert (release_dir / "hf_release_manifest.json").exists()
    assert (release_dir / "docs/license_and_attribution_notes.md").exists()
    assert not (release_dir / "threads.jsonl").exists()

    card = (release_dir / "README.md").read_text(encoding="utf-8")
    assert "metadata-only release" in card
    assert "Licensing And Attribution" in card
    assert "raw SEDE exports" in card
    assert "Synthetic post title" not in card

    manifest = json.loads((release_dir / "hf_release_manifest.json").read_text(encoding="utf-8"))
    assert manifest["repo_id"] == "namespace/stackexchange-difficulty"
    assert manifest["release_policy"] == "metadata_only_private_first"
    paths = {row["path"] for row in manifest["files"]}
    assert "README.md" in paths
    assert "data_dictionary.tsv" in paths
    assert "docs/license_and_attribution_notes.md" in paths
    assert "provenance/provenance_sede_pilot_2026-05-12.json" in paths
    assert all(row["sha256"].startswith("sha256:") for row in manifest["files"])


def test_prepare_hf_release_missing_audit_or_provenance_fails(tmp_path):
    project_root = make_release_project(tmp_path)
    audit = (
        project_root
        / "reports/datasets/stackexchange-difficulty/audits/sede_pilot_2026-05-12.md"
    )
    audit.unlink()

    result = run_cli(
        [
            "prepare-hf-release",
            "--pilot-date",
            "2026-05-12",
            "--repo-id",
            "namespace/repo",
            "--out-dir",
            str(tmp_path / "release"),
            "--project-root",
            str(project_root),
        ]
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["ok"] is False
    assert "missing required dated pilot audit" in payload["error"]


def test_prepare_hf_release_rejects_credential_like_source_text(tmp_path):
    project_root = make_release_project(tmp_path)
    audit = (
        project_root
        / "reports/datasets/stackexchange-difficulty/audits/sede_pilot_2026-05-12.md"
    )
    audit.write_text("aggregate only\napi_key=abc123\n", encoding="utf-8")

    result = run_cli(
        [
            "prepare-hf-release",
            "--pilot-date",
            "2026-05-12",
            "--repo-id",
            "namespace/repo",
            "--out-dir",
            str(tmp_path / "release"),
            "--project-root",
            str(project_root),
        ]
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert "credential-like marker" in payload["error"]


def test_release_source_path_rejects_raw_and_processed_content(tmp_path):
    root = tmp_path / "project"
    raw = root / "data/raw/stackexchange-difficulty/sede-pilot.csv"
    processed = root / "data/processed/stackexchange-difficulty/threads.jsonl"
    dictionary = root / "data/processed/stackexchange-difficulty/data_dictionary.tsv"

    try:
        validate_release_source_path(raw, root)
    except HuggingFaceReleaseError as exc:
        assert "raw data file" in str(exc)
    else:
        raise AssertionError("raw path was not rejected")

    try:
        validate_release_source_path(processed, root)
    except HuggingFaceReleaseError as exc:
        assert "processed data file" in str(exc)
    else:
        raise AssertionError("processed path was not rejected")

    validate_release_source_path(dictionary, root)


def test_upload_hf_release_dry_run_does_not_require_hf(tmp_path):
    release_dir = tmp_path / "release"
    release_dir.mkdir()

    result = run_cli(
        [
            "upload-hf-release",
            "--release-dir",
            str(release_dir),
            "--repo-id",
            "namespace/repo",
        ]
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["dry_run"] is True
    assert [
        "hf",
        "repos",
        "create",
        "namespace/repo",
        "--type",
        "dataset",
        "--private",
        "--exist-ok",
    ] in payload["commands"]


def test_upload_hf_release_apply_fails_when_hf_missing(tmp_path):
    release_dir = tmp_path / "release"
    release_dir.mkdir()

    result = run_cli(
        [
            "upload-hf-release",
            "--release-dir",
            str(release_dir),
            "--repo-id",
            "namespace/repo",
            "--apply",
        ],
        env_updates={"PATH": ""},
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert "hf CLI is not installed" in payload["error"]


def test_upload_hf_release_apply_fails_when_auth_fails(tmp_path):
    release_dir = tmp_path / "release"
    release_dir.mkdir()
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    hf = fake_bin / "hf"
    hf.write_text("#!/bin/sh\necho auth failed >&2\nexit 7\n", encoding="utf-8")
    hf.chmod(hf.stat().st_mode | stat.S_IXUSR)

    result = run_cli(
        [
            "upload-hf-release",
            "--release-dir",
            str(release_dir),
            "--repo-id",
            "namespace/repo",
            "--apply",
        ],
        env_updates={"PATH": str(fake_bin)},
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert "HF command failed: hf auth whoami" in payload["error"]


def test_upload_hf_release_apply_uses_hf_cli_without_live_network(tmp_path):
    release_dir = tmp_path / "release"
    release_dir.mkdir()
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    log = tmp_path / "hf.log"
    hf = fake_bin / "hf"
    hf.write_text(
        "#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$HF_FAKE_LOG\"\nexit 0\n",
        encoding="utf-8",
    )
    hf.chmod(hf.stat().st_mode | stat.S_IXUSR)

    result = run_cli(
        [
            "upload-hf-release",
            "--release-dir",
            str(release_dir),
            "--repo-id",
            "namespace/repo",
            "--apply",
        ],
        env_updates={"PATH": str(fake_bin), "HF_FAKE_LOG": str(log)},
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["dry_run"] is False
    logged = log.read_text(encoding="utf-8")
    assert "auth whoami" in logged
    assert "repos create namespace/repo --type dataset --private --exist-ok" in logged
    assert "upload namespace/repo" in logged


def test_hf_dist_release_path_is_ignored_by_git():
    result = subprocess.run(
        ["git", "check-ignore", "dist/huggingface/stackexchange-difficulty-2026-05-12/README.md"],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0


def make_release_project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    dataset = root / "reports/datasets/stackexchange-difficulty"
    (dataset / "audits").mkdir(parents=True)
    (root / "data/processed/stackexchange-difficulty").mkdir(parents=True)
    (root / "reports").mkdir(parents=True, exist_ok=True)

    (root / "data/processed/stackexchange-difficulty/data_dictionary.tsv").write_text(
        "field\tdescription\nquestion_id\tSynthetic identifier only\n",
        encoding="utf-8",
    )
    (dataset / "provenance_sede_pilot_2026-05-12.json").write_text(
        json.dumps(
            {
                "source_method": "sede_pilot_export",
                "access_date": "2026-05-12",
                "license": "CC BY-SA by per-record ContentLicense",
                "transformation_steps": ["aggregate metadata only"],
                "output_hash": "sha256:abc",
                "query_or_dump_file": (
                    "reports/datasets/stackexchange-difficulty/sede_pilot_query.sql"
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (dataset / "audits/sede_pilot_2026-05-12.md").write_text(
        "# SEDE Pilot Audit\n\nAggregate counts only.\n",
        encoding="utf-8",
    )
    (dataset / "validation_protocol.md").write_text("# Validation\n", encoding="utf-8")
    (dataset / "completion_criteria.md").write_text("# Completion\n", encoding="utf-8")
    (dataset / "sede_export_checklist.md").write_text("# Checklist\n", encoding="utf-8")
    (root / "reports/stackexchange_exploitation_report.md").write_text(
        "# Methodological report\n\nProtocol text only.\n",
        encoding="utf-8",
    )
    return root


def run_cli(
    args: list[str],
    *,
    env_updates: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path.cwd() / "src")
    if env_updates:
        env.update(env_updates)
    return subprocess.run(
        [sys.executable, "-m", "stackexchange_difficulty", *args],
        cwd=Path.cwd(),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
