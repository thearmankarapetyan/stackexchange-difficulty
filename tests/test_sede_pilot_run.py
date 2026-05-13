from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

import stackexchange_difficulty.sede_pilot as sede_pilot_module
from stackexchange_difficulty.sede import validate_sede_export
from stackexchange_difficulty.sede_pilot import (
    SedePilotConfig,
    SedePilotError,
    build_sede_pilot_context,
    normalize_site_slug,
    prepare_browser_session,
    run_sede_pilot,
    wait_for_sede_export,
)
from stackexchange_difficulty.validation import read_table


def test_wait_for_sede_export_detects_new_csv(tmp_path):
    start = time.time() - 1
    export = tmp_path / "query-results.csv"
    export.write_text("question_id,title\n1,Example\n", encoding="utf-8")

    found = wait_for_sede_export(
        tmp_path,
        start_time=start,
        timeout_seconds=1,
        poll_interval=0.01,
        stable_seconds=0,
    )

    assert found == export


def test_wait_for_sede_export_detects_new_tsv(tmp_path):
    start = time.time() - 1
    export = tmp_path / "query-results.tsv"
    export.write_text("question_id\ttitle\n1\tExample\n", encoding="utf-8")

    found = wait_for_sede_export(
        tmp_path,
        start_time=start,
        timeout_seconds=1,
        poll_interval=0.01,
        stable_seconds=0,
    )

    assert found == export


def test_wait_for_sede_export_ignores_partial_download_then_finds_csv(tmp_path):
    start = time.time() - 1
    partial = tmp_path / "query-results.csv.crdownload"
    partial.write_text("partial", encoding="utf-8")
    final = tmp_path / "query-results.csv"

    def finish_download() -> None:
        time.sleep(0.05)
        final.write_text("question_id,title\n1,Example\n", encoding="utf-8")

    thread = threading.Thread(target=finish_download)
    thread.start()
    try:
        found = wait_for_sede_export(
            tmp_path,
            start_time=start,
            timeout_seconds=1,
            poll_interval=0.01,
            stable_seconds=0,
        )
    finally:
        thread.join()

    assert found == final


def test_wait_for_sede_export_fails_on_timeout(tmp_path):
    with pytest.raises(SedePilotError, match="timed out"):
        wait_for_sede_export(
            tmp_path,
            start_time=time.time(),
            timeout_seconds=0.02,
            poll_interval=0.01,
            stable_seconds=0,
        )


def test_wait_for_sede_export_fails_when_download_directory_is_missing(tmp_path):
    with pytest.raises(SedePilotError, match="download directory does not exist"):
        wait_for_sede_export(
            tmp_path / "missing",
            start_time=time.time(),
            timeout_seconds=1,
            poll_interval=0.01,
            stable_seconds=0,
        )


def test_wait_for_sede_export_fails_on_multiple_candidates(tmp_path):
    start = time.time() - 1
    (tmp_path / "one.csv").write_text("a\n", encoding="utf-8")
    (tmp_path / "two.tsv").write_text("a\n", encoding="utf-8")

    with pytest.raises(SedePilotError, match="multiple"):
        wait_for_sede_export(
            tmp_path,
            start_time=start,
            timeout_seconds=1,
            poll_interval=0.01,
            stable_seconds=0,
        )


def test_wait_for_sede_export_fails_on_unsupported_suffix(tmp_path):
    start = time.time() - 1
    (tmp_path / "query-results.xlsx").write_text("not a csv", encoding="utf-8")

    with pytest.raises(SedePilotError, match="unsupported suffix"):
        wait_for_sede_export(
            tmp_path,
            start_time=start,
            timeout_seconds=1,
            poll_interval=0.01,
            stable_seconds=0,
        )


def test_prepare_browser_session_opens_query_page():
    opened: list[str] = []

    result = prepare_browser_session(
        query_url="https://example.test/query",
        opener=lambda url: opened.append(url) is None,
    )

    assert result["opened"] is True
    assert result["query_url"] == "https://example.test/query"
    assert opened == ["https://example.test/query"]


def test_run_sede_pilot_export_path_completes_pipeline_without_pending_provenance(tmp_path):
    project_root = make_project_root(tmp_path)
    fixture = Path.cwd() / "tests/fixtures/sede_pilot_export.tsv"

    result = run_cli(
        [
            "run-sede-pilot",
            "--export",
            str(fixture),
            "--pilot-date",
            "2026-05-12",
            "--min-rows",
            "1",
            "--max-rows",
            "10",
            "--project-root",
            str(project_root),
        ]
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["ok"] is True
    provenance = json.loads(Path(payload["provenance"]).read_text(encoding="utf-8"))
    assert "pending" not in provenance["output_hash"]
    assert provenance["export_identifier"] == (
        "data/raw/stackexchange-difficulty/sede-pilot-2026-05-12.tsv"
    )
    assert provenance["processed_hash_manifest"] == (
        "data/processed/stackexchange-difficulty/pilot-2026-05-12/"
        "processed-output.sha256"
    )

    threads_path = (
        project_root
        / "data/processed/stackexchange-difficulty/pilot-2026-05-12-derived/threads.jsonl"
    )
    rows = [
        json.loads(line)
        for line in threads_path.read_text(encoding="utf-8").splitlines()
    ]
    assert len(rows) == 2
    assert rows[0]["indicators"]["has_answer"] is True
    assert rows[0]["indicators"]["has_accepted_answer"] is True
    assert rows[1]["indicators"]["is_unanswered"] is True
    assert rows[1]["indicators"]["is_closed"] is True
    assert rows[1]["indicators"]["is_duplicate"] is True
    assert rows[0]["indicators"]["time_to_first_answer_hours"] == 1.0
    assert "pending" not in rows[0]["provenance"]["output_hash"]

    audit_text = Path(payload["audit"]).read_text(encoding="utf-8")
    assert "Synthetic SEDE CSV parsing" not in audit_text
    assert "Use a parser fixture" not in audit_text
    assert "No API crawling" in audit_text
    assert "Tag-family distribution: javascript=1, python=1" in audit_text
    assert "Time-period distribution: recent=2" in audit_text
    assert str(project_root) not in audit_text


def test_run_sede_pilot_site_slug_uses_site_specific_names_and_metadata(tmp_path):
    project_root = make_project_root(tmp_path)
    fixture = Path.cwd() / "tests/fixtures/sede_pilot_export.tsv"
    query_file = (
        "reports/datasets/stackexchange-difficulty/"
        "sede_pilot_query_site_generic.sql"
    )

    result = run_cli(
        [
            "run-sede-pilot",
            "--export",
            str(fixture),
            "--pilot-date",
            "2026-05-12",
            "--site-slug",
            "math",
            "--site-name",
            "Mathematics",
            "--query-file",
            query_file,
            "--min-rows",
            "1",
            "--max-rows",
            "10",
            "--project-root",
            str(project_root),
        ]
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["ok"] is True
    assert payload["source_site_slug"] == "math"
    assert payload["source_site_name"] == "Mathematics"
    assert payload["query_url"] == "https://data.stackexchange.com/math/query/new"
    assert payload["raw_export"].endswith("sede-pilot-math-2026-05-12.tsv")
    assert payload["processed_dir"].endswith("pilot-math-2026-05-12")
    assert payload["derived_dir"].endswith("pilot-math-2026-05-12-derived")
    assert payload["audit"].endswith("sede_pilot_math_2026-05-12.md")
    assert payload["provenance"].endswith(
        "provenance_sede_pilot_math_2026-05-12.json"
    )

    provenance = json.loads(Path(payload["provenance"]).read_text(encoding="utf-8"))
    assert provenance["source_site_slug"] == "math"
    assert provenance["source_site_name"] == "Mathematics"
    assert provenance["query_url"] == "https://data.stackexchange.com/math/query/new"
    assert provenance["query_or_dump_file"] == query_file
    assert provenance["transformation_steps"][0] == (
        "exported Mathematics pilot rows manually through SEDE"
    )

    audit_text = Path(payload["audit"]).read_text(encoding="utf-8")
    assert "- Source: Mathematics SEDE." in audit_text
    assert f"- Query file: `{query_file}`." in audit_text
    assert "- Query URL: `https://data.stackexchange.com/math/query/new`." in audit_text


def test_run_sede_pilot_auto_detects_project_under_workspace_projects(tmp_path):
    project_root = make_project_root(tmp_path)
    workspace = tmp_path / "workspace"
    projects = workspace / "projects"
    projects.mkdir(parents=True)
    (projects / "stackexchange-difficulty").symlink_to(
        project_root,
        target_is_directory=True,
    )
    fixture = Path.cwd() / "tests/fixtures/sede_pilot_export.tsv"

    result = run_cli(
        [
            "run-sede-pilot",
            "--export",
            str(fixture),
            "--pilot-date",
            "2026-05-12",
            "--site-slug",
            "math",
            "--site-name",
            "Mathematics",
            "--query-file",
            "reports/datasets/stackexchange-difficulty/sede_pilot_query_site_generic.sql",
            "--min-rows",
            "1",
            "--max-rows",
            "10",
        ],
        cwd=workspace,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["ok"] is True
    assert Path(payload["raw_export"]).resolve() == (
        project_root
        / "data/raw/stackexchange-difficulty/sede-pilot-math-2026-05-12.tsv"
    )


def test_build_sede_context_derives_math_query_url_and_query_file(tmp_path):
    project_root = make_project_root(tmp_path)
    query_file = Path(
        "reports/datasets/stackexchange-difficulty/sede_pilot_query_site_generic.sql"
    )

    context = build_sede_pilot_context(
        SedePilotConfig(
            project_root=project_root,
            pilot_date="2026-05-12",
            site_slug="math",
            site_name="Mathematics",
            query_file=query_file,
        )
    )

    assert context.site_slug == "math"
    assert context.site_name == "Mathematics"
    assert context.query_url == "https://data.stackexchange.com/math/query/new"
    assert context.query_file == (project_root / query_file).resolve()
    assert context.raw_stem == "sede-pilot-math-2026-05-12"


def test_run_sede_pilot_browser_mode_uses_site_url_and_query_file(
    tmp_path,
    monkeypatch,
    capsys,
):
    project_root = make_project_root(tmp_path)
    fixture = Path.cwd() / "tests/fixtures/sede_pilot_export.tsv"
    query_file = Path(
        "reports/datasets/stackexchange-difficulty/sede_pilot_query_site_generic.sql"
    )
    opened_urls: list[str] = []

    def fake_prepare_browser_session(query_url):
        opened_urls.append(query_url)
        return {"opened": True, "query_url": query_url}

    def fake_wait_for_sede_export(*args, **kwargs):
        return fixture

    monkeypatch.setattr(
        sede_pilot_module,
        "prepare_browser_session",
        fake_prepare_browser_session,
    )
    monkeypatch.setattr(
        sede_pilot_module,
        "wait_for_sede_export",
        fake_wait_for_sede_export,
    )

    result = run_sede_pilot(
        SedePilotConfig(
            project_root=project_root,
            pilot_date="2026-05-12",
            open_browser=True,
            min_rows=1,
            max_rows=10,
            site_slug="math",
            site_name="Mathematics",
            query_file=query_file,
        )
    )

    stdout = capsys.readouterr().out
    assert result.ok is True
    assert opened_urls == ["https://data.stackexchange.com/math/query/new"]
    assert str((project_root / query_file).resolve()) in stdout
    assert "https://data.stackexchange.com/math/query/new" in stdout


@pytest.mark.parametrize("bad_slug", ["math site", "math/site", "../math", "math.site"])
def test_site_slug_rejects_path_like_values(bad_slug):
    with pytest.raises(SedePilotError, match="site slug"):
        normalize_site_slug(bad_slug)


def test_run_sede_pilot_missing_required_columns_fails_before_ingestion(tmp_path):
    project_root = make_project_root(tmp_path)
    export = tmp_path / "missing.tsv"
    rows = read_fixture_rows()
    for row in rows:
        row.pop("body_html")
    write_rows(export, rows)

    result = run_cli(
        [
            "run-sede-pilot",
            "--export",
            str(export),
            "--pilot-date",
            "2026-05-12",
            "--min-rows",
            "1",
            "--max-rows",
            "10",
            "--project-root",
            str(project_root),
        ]
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert any(issue["code"] == "missing_required_columns" for issue in payload["issues"])
    assert not (
        project_root / "data/processed/stackexchange-difficulty/pilot-2026-05-12/questions.tsv"
    ).exists()


def test_validate_sede_export_rejects_duplicate_and_missing_accepted_answer(tmp_path):
    duplicate_export = tmp_path / "duplicate.tsv"
    duplicate_rows = read_fixture_rows()
    duplicate_rows[1]["question_id"] = duplicate_rows[0]["question_id"]
    write_rows(duplicate_export, duplicate_rows)

    duplicate_issues = validate_sede_export(read_table(duplicate_export, name="sede_export"))
    assert any(issue.code == "duplicate_question_id" for issue in duplicate_issues)

    missing_export = tmp_path / "missing-accepted.tsv"
    missing_rows = read_fixture_rows()
    missing_rows[0]["accepted_answer_id"] = "999"
    missing_rows[0]["first_answer_id"] = ""
    missing_rows[0]["accepted_answer_body_html"] = ""
    missing_rows[0]["accepted_answer_creation_date"] = ""
    write_rows(missing_export, missing_rows)

    missing_issues = validate_sede_export(read_table(missing_export, name="sede_export"))
    assert any(issue.code == "accepted_answer_missing" for issue in missing_issues)


def test_real_data_paths_are_ignored_by_git():
    paths = [
        "data/raw/stackexchange-difficulty/sede-pilot-2026-05-12.csv",
        "data/raw/stackexchange-difficulty/sede-pilot-math-2026-05-12.csv",
        "data/processed/stackexchange-difficulty/pilot-2026-05-12/questions.tsv",
        "data/processed/stackexchange-difficulty/pilot-math-2026-05-12/questions.tsv",
        "data/processed/stackexchange-difficulty/pilot-2026-05-12-derived/threads.jsonl",
        "data/processed/stackexchange-difficulty/pilot-math-2026-05-12-derived/threads.jsonl",
        "downloads/query-results.csv.crdownload",
    ]
    for path in paths:
        result = subprocess.run(
            ["git", "check-ignore", path],
            cwd=Path.cwd(),
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, path


def make_project_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    report_dir = root / "reports/datasets/stackexchange-difficulty"
    (report_dir / "audits").mkdir(parents=True)
    (root / "data/raw/stackexchange-difficulty").mkdir(parents=True)
    (root / "data/processed/stackexchange-difficulty").mkdir(parents=True)
    (root / "src/stackexchange_difficulty").mkdir(parents=True)
    (report_dir / "sede_pilot_query.sql").write_text("select 1;\n", encoding="utf-8")
    (report_dir / "sede_pilot_query_site_generic.sql").write_text(
        "select 1;\n",
        encoding="utf-8",
    )
    (report_dir / "provenance_sede_pilot_template.json").write_text(
        json.dumps(
            {
                "dataset_name": "stackexchange-difficulty",
                "dataset_version": "sede-pilot-YYYY-MM-DD",
                "source_method": "sede_pilot_export",
                "source_version": "SEDE snapshot visible at export time",
                "query_or_dump_file": (
                    "reports/datasets/stackexchange-difficulty/sede_pilot_query.sql"
                ),
                "export_identifier": "data/raw/stackexchange-difficulty/sede-pilot-YYYY-MM-DD.tsv",
                "access_date": "YYYY-MM-DD",
                "official_source_checked_at": "YYYY-MM-DD",
                "source_url_checked_at": {},
                "license": "CC BY-SA",
                "transformation_steps": ["synthetic test export"],
                "raw_export_hash": "sha256:<raw>",
                "processed_output_hash": "sha256:pending-before-processing",
                "output_hash": "sha256:pending-before-processing",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return root


def read_fixture_rows() -> list[dict[str, str]]:
    with Path("tests/fixtures/sede_pilot_export.tsv").open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def run_cli(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path.cwd() / "src")
    return subprocess.run(
        [sys.executable, "-m", "stackexchange_difficulty", *args],
        cwd=cwd or Path.cwd(),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
