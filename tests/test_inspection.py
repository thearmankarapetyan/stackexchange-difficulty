from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from stackexchange_difficulty.inspection import (
    InspectionError,
    prepare_inspection_files,
    summarize_inspection_labels,
)
from stackexchange_difficulty.validation import Table, read_table


def test_prepare_inspection_is_deterministic_and_covers_available_strata(tmp_path):
    questions, answers, indicators = inspection_tables()
    out_one = tmp_path / "data/processed/stackexchange-difficulty/inspection-one"
    out_two = tmp_path / "data/processed/stackexchange-difficulty/inspection-two"

    first = prepare_inspection_files(
        questions=questions,
        answers=answers,
        indicators=indicators,
        site_slug="math",
        pilot_date="2026-05-13",
        sample_size=6,
        out_dir=out_one,
        seed=7,
    )
    second = prepare_inspection_files(
        questions=questions,
        answers=answers,
        indicators=indicators,
        site_slug="math",
        pilot_date="2026-05-13",
        sample_size=6,
        out_dir=out_two,
        seed=7,
    )

    first_labels = first.labels_path.read_text(encoding="utf-8")
    second_labels = second.labels_path.read_text(encoding="utf-8")
    assert first_labels == second_labels
    assert "unanswered" in first_labels
    assert "closed" in first_labels
    assert "duplicate" in first_labels
    assert "long_latency" in first_labels
    assert "tag_bucket:low" in first_labels


def test_prepare_inspection_cli_does_not_print_sampled_content(tmp_path):
    questions, answers, indicators = inspection_tables()
    questions_path = tmp_path / "questions.tsv"
    answers_path = tmp_path / "answers.tsv"
    indicators_path = tmp_path / "derived_thread_indicators.tsv"
    write_table(questions_path, questions)
    write_table(answers_path, answers)
    write_table(indicators_path, indicators)
    out_dir = tmp_path / "data/processed/stackexchange-difficulty/inspection"

    result = run_cli(
        [
            "prepare-inspection",
            "--questions",
            str(questions_path),
            "--answers",
            str(answers_path),
            "--indicators",
            str(indicators_path),
            "--site-slug",
            "math",
            "--pilot-date",
            "2026-05-13",
            "--sample-size",
            "4",
            "--out-dir",
            str(out_dir),
        ]
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["ok"] is True
    assert "Sensitive synthetic title" not in result.stdout
    assert "Sensitive synthetic body" not in result.stdout
    assert "Sensitive synthetic answer" not in result.stdout
    labels = read_table(payload["labels"], name="labels")
    assert "question_id" not in labels.columns
    assert "title" not in labels.columns
    assert "body_html" not in labels.columns


def test_prepare_inspection_rejects_tracked_looking_out_dir(tmp_path):
    questions, answers, indicators = inspection_tables()

    with pytest.raises(InspectionError, match="data/processed/stackexchange-difficulty"):
        prepare_inspection_files(
            questions=questions,
            answers=answers,
            indicators=indicators,
            site_slug="math",
            pilot_date="2026-05-13",
            sample_size=2,
            out_dir=tmp_path / "reports/inspection",
        )


def test_summarize_inspection_updates_audit_with_aggregate_counts_only(tmp_path):
    labels_path = tmp_path / "labels.tsv"
    labels_path.write_text(
        "\t".join(
            [
                "record_index",
                "sample_stratum",
                "suitable",
                "answerability_clear",
                "math_notation_readable",
                "needs_comments",
                "reason_code",
                "notes",
            ]
        )
        + "\n"
        + "1\tanswered\tyes\tyes\tyes\tno\tgood\tDo not leak this title\n"
        + "2\tunanswered\tno\tno\tyes\tyes\tneeds_comments\tAnother copied note\n",
        encoding="utf-8",
    )
    audit = tmp_path / "audit.md"
    audit.write_text(
        "# SEDE Pilot Audit\n\n"
        "## Manual Inspection\n\n"
        "Pending.\n\n"
        "## Decision\n\n"
        "- Decision: pending.\n",
        encoding="utf-8",
    )

    result = summarize_inspection_labels(
        labels=read_table(labels_path, name="inspection_labels"),
        audit_path=audit,
    )

    text = audit.read_text(encoding="utf-8")
    assert result.inspected == 2
    assert "## Manual Inspection Summary" in text
    assert "Suitable records: yes=1, no=1, uncertain=0" in text
    assert "Top reason codes: good=1, needs_comments=1" in text
    assert "Do not leak this title" not in text
    assert "Another copied note" not in text


def test_summarize_inspection_missing_columns_fails(tmp_path):
    labels = tmp_path / "labels.tsv"
    labels.write_text("record_index\tsuitable\n1\tyes\n", encoding="utf-8")
    audit = tmp_path / "audit.md"
    audit.write_text("# Audit\n", encoding="utf-8")

    with pytest.raises(InspectionError, match="missing required columns"):
        summarize_inspection_labels(
            labels=read_table(labels, name="inspection_labels"),
            audit_path=audit,
        )


def test_summarize_inspection_rejects_free_text_reason_codes(tmp_path):
    labels = tmp_path / "labels.tsv"
    labels.write_text(
        "\t".join(
            [
                "record_index",
                "sample_stratum",
                "suitable",
                "answerability_clear",
                "math_notation_readable",
                "needs_comments",
                "reason_code",
                "notes",
            ]
        )
        + "\n1\tanswered\tyes\tyes\tyes\tno\tcopied sentence here\t\n",
        encoding="utf-8",
    )
    audit = tmp_path / "audit.md"
    audit.write_text("# Audit\n", encoding="utf-8")

    with pytest.raises(InspectionError, match="reason_code"):
        summarize_inspection_labels(
            labels=read_table(labels, name="inspection_labels"),
            audit_path=audit,
        )


def test_inspection_paths_are_ignored_by_git():
    paths = [
        "data/processed/stackexchange-difficulty/pilot-math-2026-05-13-inspection/review.tsv",
        "data/processed/stackexchange-difficulty/pilot-math-2026-05-13-inspection/labels.tsv",
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


def inspection_tables() -> tuple[Table, Table, Table]:
    questions = Table(
        name="questions",
        columns=(
            "question_id",
            "title",
            "body_html",
            "tags",
            "creation_date",
            "score",
            "view_count",
            "answer_count",
            "comment_count",
            "closed_date",
            "accepted_answer_id",
            "is_duplicate",
            "content_license",
        ),
        rows=[
            question("101", answer_count="1", accepted_answer_id="201", tags="<algebra>"),
            question("102", answer_count="0", tags="<topology>", closed_date="2026-01-02"),
            question("103", answer_count="1", tags="<logic>", is_duplicate="true"),
            question("104", answer_count="1", tags="<rare>"),
            question("105", answer_count="1", tags="<analysis>"),
            question("106", answer_count="1", tags="<geometry>"),
            question("107", answer_count="1", tags="<number-theory>"),
            question("108", answer_count="0", tags="<probability>"),
        ],
    )
    answers = Table(
        name="answers",
        columns=("answer_id", "question_id", "body_html", "score", "creation_date", "is_accepted"),
        rows=[
            answer("201", "101", is_accepted="true"),
            answer("203", "103"),
            answer("204", "104"),
            answer("205", "105"),
            answer("206", "106"),
            answer("207", "107"),
        ],
    )
    indicators = Table(
        name="derived_thread_indicators",
        columns=(
            "question_id",
            "has_answer",
            "has_accepted_answer",
            "is_unanswered",
            "is_closed",
            "is_duplicate",
            "time_to_first_answer_hours",
            "tag_popularity_bucket",
        ),
        rows=[
            indicator("101", has_answer="True", accepted="True", bucket="high"),
            indicator("102", has_answer="False", closed="True", timing="", bucket="medium"),
            indicator("103", duplicate="True", timing="48", bucket="low"),
            indicator("104", bucket="low"),
            indicator("105", bucket="medium"),
            indicator("106", bucket="high"),
            indicator("107", bucket="high"),
            indicator("108", has_answer="False", timing="", bucket="none"),
        ],
    )
    return questions, answers, indicators


def question(
    question_id: str,
    *,
    answer_count: str,
    accepted_answer_id: str = "",
    tags: str,
    closed_date: str = "",
    is_duplicate: str = "false",
) -> dict[str, str]:
    return {
        "question_id": question_id,
        "title": f"Sensitive synthetic title {question_id}",
        "body_html": f"<p>Sensitive synthetic body {question_id}</p>",
        "tags": tags,
        "creation_date": "2026-01-01T00:00:00+00:00",
        "score": "1",
        "view_count": "10",
        "answer_count": answer_count,
        "comment_count": "0",
        "closed_date": closed_date,
        "accepted_answer_id": accepted_answer_id,
        "is_duplicate": is_duplicate,
        "content_license": "CC BY-SA 4.0",
    }


def answer(answer_id: str, question_id: str, *, is_accepted: str = "false") -> dict[str, str]:
    return {
        "answer_id": answer_id,
        "question_id": question_id,
        "body_html": f"<p>Sensitive synthetic answer {answer_id}</p>",
        "score": "2",
        "creation_date": "2026-01-01T01:00:00+00:00",
        "is_accepted": is_accepted,
    }


def indicator(
    question_id: str,
    *,
    has_answer: str = "True",
    accepted: str = "False",
    closed: str = "False",
    duplicate: str = "False",
    timing: str = "1",
    bucket: str,
) -> dict[str, str]:
    return {
        "question_id": question_id,
        "has_answer": has_answer,
        "has_accepted_answer": accepted,
        "is_unanswered": str(has_answer == "False"),
        "is_closed": closed,
        "is_duplicate": duplicate,
        "time_to_first_answer_hours": timing,
        "tag_popularity_bucket": bucket,
    }


def write_table(path: Path, table: Table) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table.columns), delimiter="\t")
        writer.writeheader()
        writer.writerows(table.rows)


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
