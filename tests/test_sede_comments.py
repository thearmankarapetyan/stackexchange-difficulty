from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from stackexchange_difficulty.sede import normalize_sede_export
from stackexchange_difficulty.sede_comments import (
    SedeCommentConfig,
    SedeCommentError,
    normalize_sede_comment_export,
    render_comment_query,
    resolve_download_dir,
    run_sede_comment_enrichment,
    validate_sede_comment_export,
)
from stackexchange_difficulty.validation import Table, read_table


def test_render_comment_query_uses_actual_pilot_ids_and_no_content():
    questions, answers = pilot_tables()
    template = Path(
        "reports/datasets/stackexchange-difficulty/sede_comments_query_template.sql"
    ).read_text(encoding="utf-8")

    query = render_comment_query(questions=questions, answers=answers, template=template)

    assert "(501)" in query
    assert "(502)" in query
    assert "(701, 501)" in query
    assert "Synthetic SEDE CSV parsing" not in query
    assert "Use a parser fixture" not in query


def test_validate_sede_comment_export_accepts_synthetic_export():
    questions, answers = pilot_tables()
    comments = read_table("tests/fixtures/sede_comments_export.tsv", name="comments")

    issues = validate_sede_comment_export(comments, questions=questions, answers=answers)
    normalized = normalize_sede_comment_export(comments)

    assert issues == []
    assert normalized.columns == (
        "comment_id",
        "post_id",
        "question_id",
        "post_type_id",
        "text",
        "score",
        "creation_date",
        "content_license",
    )
    assert len(normalized.rows) == 2


def test_validate_sede_comment_export_missing_columns_fails():
    questions, answers = pilot_tables()
    comments = read_table("tests/fixtures/sede_comments_export.tsv", name="comments")
    broken = Table(
        name=comments.name,
        rows=comments.rows,
        columns=tuple(column for column in comments.columns if column != "content_license"),
    )

    issues = validate_sede_comment_export(broken, questions=questions, answers=answers)

    assert len(issues) == 1
    assert issues[0].code == "missing_required_columns"
    assert "content_license" in issues[0].message


def test_validate_sede_comment_export_rejects_duplicate_comment_id(tmp_path):
    questions, answers = pilot_tables()
    export = tmp_path / "comments.tsv"
    rows = read_comment_rows()
    rows[1]["comment_id"] = rows[0]["comment_id"]
    write_rows(export, rows)

    issues = validate_sede_comment_export(
        read_table(export, name="comments"),
        questions=questions,
        answers=answers,
    )

    assert any(issue.code == "duplicate_comment_id" for issue in issues)


def test_validate_sede_comment_export_rejects_unknown_question(tmp_path):
    questions, answers = pilot_tables()
    export = tmp_path / "comments.tsv"
    rows = read_comment_rows()
    rows[0]["question_id"] = "999"
    write_rows(export, rows)

    issues = validate_sede_comment_export(
        read_table(export, name="comments"),
        questions=questions,
        answers=answers,
    )

    assert any(issue.code == "comment_question_missing" for issue in issues)


def test_validate_sede_comment_export_rejects_unknown_post(tmp_path):
    questions, answers = pilot_tables()
    export = tmp_path / "comments.tsv"
    rows = read_comment_rows()
    rows[0]["post_id"] = "999"
    write_rows(export, rows)

    issues = validate_sede_comment_export(
        read_table(export, name="comments"),
        questions=questions,
        answers=answers,
    )

    assert any(issue.code == "comment_post_missing" for issue in issues)


def test_validate_sede_comment_export_rejects_empty_when_pilot_has_comments():
    questions, answers = pilot_tables()
    comments = Table(
        name="comments",
        rows=[],
        columns=(
            "comment_id",
            "post_id",
            "question_id",
            "post_type_id",
            "text",
            "score",
            "creation_date",
            "content_license",
        ),
    )

    issues = validate_sede_comment_export(comments, questions=questions, answers=answers)

    assert any(issue.code == "comment_export_empty" for issue in issues)


def test_run_sede_comment_enrichment_with_export_completes_pipeline(tmp_path):
    project_root = make_project_root(tmp_path)
    seed_pilot_files(project_root)
    fixture = Path.cwd() / "tests/fixtures/sede_comments_export.tsv"

    result = run_cli(
        [
            "run-sede-comment-enrichment",
            "--export",
            str(fixture),
            "--pilot-date",
            "2026-05-13",
            "--site-slug",
            "math",
            "--site-name",
            "Mathematics",
            "--questions",
            "data/processed/stackexchange-difficulty/pilot-math-2026-05-13/questions.tsv",
            "--answers",
            "data/processed/stackexchange-difficulty/pilot-math-2026-05-13/answers.tsv",
            "--project-root",
            str(project_root),
        ]
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["ok"] is True
    assert payload["comments"] == 2
    assert payload["covered_questions"] == 1
    assert payload["covered_answer_posts"] == 1
    assert payload["query_file"].endswith(
        "pilot-math-2026-05-13-comment-enrichment/sede_comments_query.sql"
    )

    query = Path(payload["query_file"]).read_text(encoding="utf-8")
    assert "(501)" in query
    assert "Synthetic SEDE CSV parsing" not in query

    provenance = json.loads(Path(payload["provenance"]).read_text(encoding="utf-8"))
    assert provenance["source_method"] == "sede_comment_export"
    assert "pending" not in provenance["output_hash"]

    derived = Path(payload["derived_dir"])
    rows = [
        json.loads(line)
        for line in (derived / "threads.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    first = next(row for row in rows if row["question_id"] == "501")
    assert len(first["comments"]) == 2
    assert first["indicators"]["comment_count_before_first_answer"] == 1

    audit_text = Path(payload["audit"]).read_text(encoding="utf-8")
    assert "## Comment Enrichment" in audit_text
    assert "Comment rows: 2" in audit_text
    assert "Please clarify the synthetic setup" not in audit_text
    assert "Synthetic SEDE CSV parsing" not in audit_text


def test_run_sede_comment_enrichment_rejects_bad_export_before_outputs(tmp_path):
    project_root = make_project_root(tmp_path)
    seed_pilot_files(project_root)
    bad_export = tmp_path / "bad.tsv"
    rows = read_comment_rows()
    rows[0]["post_id"] = "999"
    write_rows(bad_export, rows)

    result = run_cli(
        [
            "run-sede-comment-enrichment",
            "--export",
            str(bad_export),
            "--pilot-date",
            "2026-05-13",
            "--site-slug",
            "math",
            "--questions",
            "data/processed/stackexchange-difficulty/pilot-math-2026-05-13/questions.tsv",
            "--answers",
            "data/processed/stackexchange-difficulty/pilot-math-2026-05-13/answers.tsv",
            "--project-root",
            str(project_root),
        ]
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["ok"] is False
    assert any(issue["code"] == "comment_post_missing" for issue in payload["issues"])
    assert payload["processed_dir"] is None


def test_run_sede_comment_enrichment_accepts_csv_export(tmp_path):
    project_root = make_project_root(tmp_path)
    seed_pilot_files(project_root)
    csv_export = tmp_path / "comments.csv"
    write_rows(csv_export, read_comment_rows(), delimiter=",")

    result = run_cli(
        [
            "run-sede-comment-enrichment",
            "--export",
            str(csv_export),
            "--pilot-date",
            "2026-05-13",
            "--site-slug",
            "math",
            "--questions",
            "data/processed/stackexchange-difficulty/pilot-math-2026-05-13/questions.tsv",
            "--answers",
            "data/processed/stackexchange-difficulty/pilot-math-2026-05-13/answers.tsv",
            "--project-root",
            str(project_root),
        ]
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["raw_export"].endswith(".csv")


def test_resolve_download_dir_auto_checks_localized_directory(tmp_path, monkeypatch):
    home = tmp_path / "home"
    downloads = home / "T\u00e9l\u00e9chargements"
    downloads.mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.delenv("XDG_DOWNLOAD_DIR", raising=False)

    assert resolve_download_dir("auto") == downloads


def test_comment_enrichment_paths_are_ignored_by_git():
    paths = [
        "data/raw/stackexchange-difficulty/sede-comments-math-2026-05-13.csv",
        (
            "data/processed/stackexchange-difficulty/"
            "pilot-math-2026-05-13-comment-enrichment/sede_comments_query.sql"
        ),
        (
            "data/processed/stackexchange-difficulty/"
            "pilot-math-2026-05-13-comment-enriched/comments.tsv"
        ),
        (
            "data/processed/stackexchange-difficulty/"
            "pilot-math-2026-05-13-comment-enriched-derived/threads.jsonl"
        ),
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


def test_run_sede_comment_enrichment_browser_mode_uses_generated_query(
    tmp_path,
    monkeypatch,
    capsys,
):
    project_root = make_project_root(tmp_path)
    seed_pilot_files(project_root)
    fixture = Path.cwd() / "tests/fixtures/sede_comments_export.tsv"
    opened_urls: list[str] = []

    def fake_open(query_url):
        opened_urls.append(query_url)
        return {"opened": True, "query_url": query_url}

    def fake_wait(*args, **kwargs):
        return fixture

    import stackexchange_difficulty.sede_comments as module

    monkeypatch.setattr(module, "prepare_browser_session", fake_open)
    monkeypatch.setattr(module, "wait_for_sede_export", fake_wait)

    result = run_sede_comment_enrichment(
        SedeCommentConfig(
            project_root=project_root,
            pilot_date="2026-05-13",
            site_slug="math",
            site_name="Mathematics",
            questions_path=(
                project_root
                / "data/processed/stackexchange-difficulty/"
                "pilot-math-2026-05-13/questions.tsv"
            ),
            answers_path=(
                project_root
                / "data/processed/stackexchange-difficulty/"
                "pilot-math-2026-05-13/answers.tsv"
            ),
            open_browser=True,
            download_dir=tmp_path,
        )
    )

    stdout = capsys.readouterr().out
    assert result.ok is True
    assert opened_urls == ["https://data.stackexchange.com/math/query/new"]
    assert str(result.query_file) in stdout
    assert "Please clarify the synthetic setup" not in stdout


def pilot_tables() -> tuple[Table, Table]:
    export = read_table("tests/fixtures/sede_pilot_export.tsv", name="sede_export")
    questions, answers, _comments = normalize_sede_export(export)
    return questions, answers


def make_project_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    report_dir = root / "reports/datasets/stackexchange-difficulty"
    (report_dir / "audits").mkdir(parents=True)
    (root / "data/raw/stackexchange-difficulty").mkdir(parents=True)
    (root / "data/processed/stackexchange-difficulty").mkdir(parents=True)
    (root / "src/stackexchange_difficulty").mkdir(parents=True)
    (report_dir / "sede_comments_query_template.sql").write_text(
        Path("reports/datasets/stackexchange-difficulty/sede_comments_query_template.sql")
        .read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (report_dir / "audits/sede_pilot_math_2026-05-13.md").write_text(
        "# SEDE Pilot Audit\n\n## Decision\n\n- Decision: needs_comment_enrichment.\n",
        encoding="utf-8",
    )
    return root


def seed_pilot_files(project_root: Path) -> None:
    questions, answers = pilot_tables()
    out = project_root / "data/processed/stackexchange-difficulty/pilot-math-2026-05-13"
    out.mkdir(parents=True)
    write_rows(out / "questions.tsv", questions.rows)
    write_rows(out / "answers.tsv", answers.rows)


def read_comment_rows() -> list[dict[str, str]]:
    with Path("tests/fixtures/sede_comments_export.tsv").open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_rows(path: Path, rows: list[dict[str, str]], delimiter: str = "\t") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)


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


def test_render_comment_query_rejects_non_numeric_ids():
    questions = Table(
        name="questions",
        rows=[{"question_id": "not-an-id"}],
        columns=("question_id",),
    )
    answers = Table(name="answers", rows=[], columns=("answer_id", "question_id"))

    with pytest.raises(SedeCommentError, match="numeric"):
        render_comment_query(questions=questions, answers=answers, template="{question_values}")
