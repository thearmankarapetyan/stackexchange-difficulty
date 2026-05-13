from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from stackexchange_difficulty.data_dump import (
    DataDumpError,
    DataDumpPilotConfig,
    DataDumpPreflightConfig,
    iter_xml_rows,
    preflight_dump,
    run_data_dump_pilot,
)
from stackexchange_difficulty.validation import read_table

FIXTURE_ROOT = Path("tests/fixtures/data_dump")


def test_iter_xml_rows_streams_row_attributes():
    rows = list(iter_xml_rows(FIXTURE_ROOT / "valid/Posts.xml"))

    assert rows[0]["Id"] == "101"
    assert rows[0]["Body"] == "<p>Synthetic rendered question body 101</p>"


def test_preflight_dump_requires_posts_and_postlinks_for_answerable_profile(tmp_path):
    root, dump_dir = make_project_root(tmp_path, "missing_postlinks")

    result = preflight_dump(
        DataDumpPreflightConfig(
            project_root=root,
            dump_dir=dump_dir,
            site_slug="math",
            site_name="Mathematics",
            dump_date="2026-05-13",
            sample_profile="answerable_pilot",
        )
    )

    assert result.ok is False
    assert any(issue["code"] == "missing_postlinks_for_answerable_pilot" for issue in result.issues)


def test_preflight_dump_requires_posts_xml(tmp_path):
    root, dump_dir = make_project_root(tmp_path, "invalid_missing_posts")

    result = preflight_dump(
        DataDumpPreflightConfig(
            project_root=root,
            dump_dir=dump_dir,
            site_slug="math",
            site_name="Mathematics",
            dump_date="2026-05-13",
            sample_profile="answerable_pilot",
        )
    )

    assert result.ok is False
    assert any(issue["code"] == "missing_required_dump_file" for issue in result.issues)


def test_preflight_dump_requires_post_history_when_requested(tmp_path):
    root, dump_dir = make_project_root(tmp_path, "missing_optional")

    result = preflight_dump(
        DataDumpPreflightConfig(
            project_root=root,
            dump_dir=dump_dir,
            site_slug="math",
            site_name="Mathematics",
            dump_date="2026-05-13",
            sample_profile="answerable_pilot",
            include_post_history=True,
        )
    )

    assert result.ok is False
    assert any(
        issue["code"] == "missing_required_dump_file"
        and "PostHistory.xml" in issue["message"]
        for issue in result.issues
    )


def test_preflight_dump_allows_missing_optional_files(tmp_path):
    root, dump_dir = make_project_root(tmp_path, "missing_optional")

    result = preflight_dump(
        DataDumpPreflightConfig(
            project_root=root,
            dump_dir=dump_dir,
            site_slug="math",
            site_name="Mathematics",
            dump_date="2026-05-13",
            sample_profile="answerable_pilot",
        )
    )

    assert result.ok is True
    assert result.files["Posts.xml"]["present"] is True
    assert result.files["PostLinks.xml"]["present"] is True
    assert any(warning["code"] == "missing_optional_dump_file" for warning in result.warnings)


def test_preflight_dump_skips_post_history_unless_requested(tmp_path):
    root, dump_dir = make_project_root(tmp_path, "valid")

    result = preflight_dump(
        DataDumpPreflightConfig(
            project_root=root,
            dump_dir=dump_dir,
            site_slug="math",
            site_name="Mathematics",
            dump_date="2026-05-13",
            sample_profile="answerable_pilot",
        )
    )

    assert result.ok is True
    assert result.files["PostHistory.xml"]["present"] is True
    assert result.files["PostHistory.xml"]["skipped"] is True
    assert "PostHistory.xml" not in result.raw_file_hashes
    assert "rows" not in result.files["PostHistory.xml"]


def test_run_data_dump_pilot_writes_canonical_outputs_without_post_history_by_default(tmp_path):
    root, dump_dir = make_project_root(tmp_path, "valid")

    result = run_data_dump_pilot(
        DataDumpPilotConfig(
            project_root=root,
            dump_dir=dump_dir,
            site_slug="math",
            site_name="Mathematics",
            pilot_slug="math-answerable",
            dump_date="2026-05-13",
            sample_profile="answerable_pilot",
            sample_size=3,
        )
    )

    assert result.ok is True
    assert result.decision == "data_dump_parser_validated"
    assert result.selected_questions == 3
    assert result.processed_dir is not None
    assert result.derived_dir is not None

    questions = read_table(result.processed_dir / "questions.tsv", name="questions")
    answers = read_table(result.processed_dir / "answers.tsv", name="answers")
    comments = read_table(result.processed_dir / "comments.tsv", name="comments")
    assert len(questions.rows) == 3
    assert len(answers.rows) == 4
    assert len(comments.rows) == 2
    assert set(questions.columns) >= {
        "question_id",
        "title",
        "body_html",
        "accepted_answer_id",
        "is_duplicate",
        "content_license",
    }
    assert "<p>Synthetic rendered question body" in questions.rows[0]["body_html"]
    processed_manifest = (result.processed_dir / "processed-output.sha256").read_text(
        encoding="utf-8"
    )
    assert "questions.tsv" in processed_manifest
    assert "answers.tsv" in processed_manifest
    assert "comments.tsv" in processed_manifest
    assert "post_links.tsv" in processed_manifest
    assert "tags.tsv" in processed_manifest
    assert not (result.processed_dir / "post_history.tsv").exists()

    threads = [
        json.loads(line)
        for line in (result.derived_dir / "threads.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    provenance = json.loads((result.provenance).read_text(encoding="utf-8"))
    assert len(threads) == 3
    assert "pending" not in provenance["output_hash"]
    assert "pending" not in threads[0]["provenance"]["output_hash"]

    audit = result.audit.read_text(encoding="utf-8")
    assert "Decision: data_dump_parser_validated" in audit
    assert "Artificial ID exclusions: 1" in audit
    assert "Closed question exclusions: 1" in audit
    assert "No accepted-answer exclusions: 1" in audit
    assert "Missing accepted-answer exclusions: 1" in audit
    assert "Accepted-answer parent mismatch exclusions: 1" in audit
    assert "Duplicate-link exclusions: 1" in audit
    assert "Synthetic question title" not in audit
    assert "Synthetic rendered answer body" not in audit


def test_run_data_dump_pilot_writes_post_history_only_when_requested(tmp_path):
    root, dump_dir = make_project_root(tmp_path, "valid")

    result = run_data_dump_pilot(
        DataDumpPilotConfig(
            project_root=root,
            dump_dir=dump_dir,
            site_slug="math",
            site_name="Mathematics",
            pilot_slug="math-answerable",
            dump_date="2026-05-13",
            sample_profile="answerable_pilot",
            sample_size=3,
            include_post_history=True,
        )
    )

    assert result.processed_dir is not None
    post_history = read_table(result.processed_dir / "post_history.tsv", name="post_history")
    assert len(post_history.rows) == 2
    assert "Synthetic raw markdown for selected question" in post_history.rows[0]["text"]
    processed_manifest = (result.processed_dir / "processed-output.sha256").read_text(
        encoding="utf-8"
    )
    assert "post_history.tsv" in processed_manifest


def test_run_data_dump_pilot_fails_when_sample_size_is_unavailable(tmp_path):
    root, dump_dir = make_project_root(tmp_path, "missing_optional")

    result = run_data_dump_pilot(
        DataDumpPilotConfig(
            project_root=root,
            dump_dir=dump_dir,
            site_slug="math",
            site_name="Mathematics",
            pilot_slug="math-answerable",
            dump_date="2026-05-13",
            sample_profile="answerable_pilot",
            sample_size=2,
        )
    )

    assert result.ok is False
    assert result.decision == "data_dump_sampling_failed"
    assert result.selected_questions == 0


def test_run_data_dump_pilot_reports_incomplete_duplicate_filtering(tmp_path):
    root, dump_dir = make_project_root(tmp_path, "missing_postlinks")

    result = run_data_dump_pilot(
        DataDumpPilotConfig(
            project_root=root,
            dump_dir=dump_dir,
            site_slug="math",
            site_name="Mathematics",
            pilot_slug="math-answerable",
            dump_date="2026-05-13",
            sample_profile="answerable_pilot",
            sample_size=1,
        )
    )

    assert result.ok is False
    assert result.decision == "data_dump_duplicate_filter_incomplete"
    assert "Decision: data_dump_duplicate_filter_incomplete" in result.audit.read_text(
        encoding="utf-8"
    )


def test_run_data_dump_pilot_sampling_is_deterministic(tmp_path):
    root_a, dump_dir_a = make_project_root(tmp_path / "a", "valid")
    root_b, dump_dir_b = make_project_root(tmp_path / "b", "valid")

    result_a = run_data_dump_pilot(
        DataDumpPilotConfig(
            project_root=root_a,
            dump_dir=dump_dir_a,
            site_slug="math",
            site_name="Mathematics",
            pilot_slug="math-answerable",
            dump_date="2026-05-13",
            sample_profile="answerable_pilot",
            sample_size=2,
            sample_seed=20260513,
        )
    )
    result_b = run_data_dump_pilot(
        DataDumpPilotConfig(
            project_root=root_b,
            dump_dir=dump_dir_b,
            site_slug="math",
            site_name="Mathematics",
            pilot_slug="math-answerable",
            dump_date="2026-05-13",
            sample_profile="answerable_pilot",
            sample_size=2,
            sample_seed=20260513,
        )
    )

    assert result_a.processed_dir is not None
    assert result_b.processed_dir is not None
    ids_a = [
        row["question_id"]
        for row in read_table(result_a.processed_dir / "questions.tsv", name="questions").rows
    ]
    ids_b = [
        row["question_id"]
        for row in read_table(result_b.processed_dir / "questions.tsv", name="questions").rows
    ]
    assert ids_a == ids_b


def test_run_data_dump_pilot_rejects_existing_outputs(tmp_path):
    root, dump_dir = make_project_root(tmp_path, "valid")
    existing = root / "data/processed/stackexchange-difficulty/dump-math-answerable-2026-05-13"
    existing.mkdir(parents=True)

    with pytest.raises(DataDumpError, match="already exists"):
        run_data_dump_pilot(
            DataDumpPilotConfig(
                project_root=root,
                dump_dir=dump_dir,
                site_slug="math",
                site_name="Mathematics",
                pilot_slug="math-answerable",
                dump_date="2026-05-13",
                sample_profile="answerable_pilot",
                sample_size=3,
            )
        )


def test_preflight_dump_cli_prints_aggregate_json_without_post_text(tmp_path):
    root, dump_dir = make_project_root(tmp_path, "valid")

    result = run_cli(
        [
            "preflight-dump",
            "--dump-dir",
            str(dump_dir),
            "--site-slug",
            "math",
            "--site-name",
            "Mathematics",
            "--dump-date",
            "2026-05-13",
            "--sample-profile",
            "answerable_pilot",
            "--project-root",
            str(root),
        ]
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["ok"] is True
    assert "Posts.xml" in payload["raw_file_hashes"]
    assert "Synthetic question title" not in result.stdout
    assert "Synthetic rendered question body" not in result.stdout


def test_preflight_dump_cli_out_writes_aggregate_json(tmp_path):
    root, dump_dir = make_project_root(tmp_path, "valid")
    out = root / "reports/datasets/stackexchange-difficulty/data_dump_preflight_math.json"

    result = run_cli(
        [
            "preflight-dump",
            "--dump-dir",
            str(dump_dir),
            "--site-slug",
            "math",
            "--site-name",
            "Mathematics",
            "--dump-date",
            "2026-05-13",
            "--sample-profile",
            "answerable_pilot",
            "--out",
            str(out),
            "--project-root",
            str(root),
        ]
    )

    assert result.returncode == 0
    assert out.is_file()
    assert "Synthetic question title" not in out.read_text(encoding="utf-8")


def test_run_data_dump_pilot_cli_does_not_print_post_text(tmp_path):
    root, dump_dir = make_project_root(tmp_path, "valid")

    result = run_cli(
        [
            "run-data-dump-pilot",
            "--dump-dir",
            str(dump_dir),
            "--site-slug",
            "math",
            "--site-name",
            "Mathematics",
            "--pilot-slug",
            "math-answerable",
            "--dump-date",
            "2026-05-13",
            "--sample-profile",
            "answerable_pilot",
            "--sample-size",
            "3",
            "--project-root",
            str(root),
        ]
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["decision"] == "data_dump_parser_validated"
    assert "Synthetic question title" not in result.stdout
    assert "Synthetic rendered answer body" not in result.stdout


def test_data_dump_cli_help_commands_work():
    for command in ("preflight-dump", "run-data-dump-pilot"):
        result = run_cli([command, "--help"])
        assert result.returncode == 0
        assert command in result.stdout


def test_data_dump_paths_are_ignored_by_git():
    paths = [
        "data/raw/stackexchange-difficulty/data-dump/math-2026-05-13/Posts.xml",
        "data/raw/stackexchange-difficulty/data-dump/math-2026-05-13/PostLinks.xml",
        "data/processed/stackexchange-difficulty/dump-math-answerable-2026-05-13/questions.tsv",
        "data/processed/stackexchange-difficulty/dump-math-answerable-2026-05-13/comments.tsv",
        "data/processed/stackexchange-difficulty/dump-math-answerable-2026-05-13/post_history.tsv",
        "data/processed/stackexchange-difficulty/dump-math-answerable-2026-05-13-derived/threads.jsonl",
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


def make_project_root(tmp_path: Path, fixture_name: str) -> tuple[Path, Path]:
    root = tmp_path / "project"
    dump_dir = root / "data/raw/stackexchange-difficulty/data-dump/math-2026-05-13"
    report_dir = root / "reports/datasets/stackexchange-difficulty"
    (report_dir / "audits").mkdir(parents=True)
    (root / "data/processed/stackexchange-difficulty").mkdir(parents=True)
    shutil.copytree(FIXTURE_ROOT / fixture_name, dump_dir, dirs_exist_ok=True)
    (report_dir / "provenance_data_dump_template.json").write_text(
        json.dumps(
            {
                "dataset_name": "stackexchange-difficulty",
                "source_method": "stack_exchange_data_dump",
                "access_date": "2026-05-13",
                "license": "CC BY-SA",
                "transformation_steps": [],
                "output_hash": "sha256:pending-before-processing",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return root, dump_dir


def run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path.cwd() / "src")
    return subprocess.run(
        [sys.executable, "-m", "stackexchange_difficulty", *args],
        cwd=Path.cwd(),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
