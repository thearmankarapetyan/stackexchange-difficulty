from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from stackexchange_difficulty.qualitative import (
    QUALITATIVE_CODE_COLUMNS,
    QUALITATIVE_REVIEW_COLUMNS,
    QualitativeError,
    prepare_qualitative_sample,
    summarize_qualitative_coding,
)
from stackexchange_difficulty.validation import Table, read_table


def test_prepare_qualitative_sample_filters_dates_and_groups_deterministically(tmp_path):
    questions, answers, comments, indicators = qualitative_tables()
    out_one = tmp_path / "data/processed/stackexchange-difficulty/qual-one"
    out_two = tmp_path / "data/processed/stackexchange-difficulty/qual-two"

    first = prepare_qualitative_sample(
        questions=questions,
        answers=answers,
        comments=comments,
        indicators=indicators,
        site_slug="math",
        source_slug="math-answerable-clean-100k",
        date_from="2025-05-01",
        date_to="2026-04-20",
        sample_size=6,
        out_dir=out_one,
        seed=11,
    )
    second = prepare_qualitative_sample(
        questions=questions,
        answers=answers,
        comments=comments,
        indicators=indicators,
        site_slug="math",
        source_slug="math-answerable-clean-100k",
        date_from="2025-05-01",
        date_to="2026-04-20",
        sample_size=6,
        out_dir=out_two,
        seed=11,
    )

    first_review = read_table(first.review_path, name="review")
    second_review = read_table(second.review_path, name="review")
    manifest = json.loads(first.manifest_path.read_text(encoding="utf-8"))
    groups = {row["sample_group"] for row in first_review.rows}

    assert first.selected_records == 6
    assert [row["record_index"] for row in first_review.rows] == [
        row["record_index"] for row in second_review.rows
    ]
    assert first_review.columns == QUALITATIVE_REVIEW_COLUMNS
    assert read_table(first.codes_path, name="codes").columns == QUALITATIVE_CODE_COLUMNS
    assert groups == {"clear_direct", "ordinary_intermediate", "high_effort_or_ambiguous"}
    assert all(row["creation_date"] >= "2025-05-01" for row in first_review.rows)
    assert all(row["creation_date"] <= "2026-04-20" for row in first_review.rows)
    assert all(row["question_id"] != "999" for row in first_review.rows)
    assert manifest["selected_records"] == 6
    assert manifest["date_from"] == "2025-05-01"
    assert manifest["date_to"] == "2026-04-20"
    assert manifest["sample_group_counts"]["clear_direct"] == 2
    assert manifest["sample_group_counts"]["ordinary_intermediate"] == 2
    assert manifest["sample_group_counts"]["high_effort_or_ambiguous"] == 2


def test_prepare_qualitative_sample_redistributes_when_group_is_small(tmp_path):
    questions, answers, comments, indicators = qualitative_tables(clear_count=1)
    out_dir = tmp_path / "data/processed/stackexchange-difficulty/qual"

    result = prepare_qualitative_sample(
        questions=questions,
        answers=answers,
        comments=comments,
        indicators=indicators,
        site_slug="math",
        source_slug="math-answerable-clean-100k",
        date_from="2025-05-01",
        date_to="2026-04-20",
        sample_size=6,
        out_dir=out_dir,
        seed=3,
    )

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert result.selected_records == 6
    assert manifest["sample_group_counts"]["clear_direct"] == 1
    assert sum(manifest["sample_group_counts"].values()) == 6


def test_prepare_qualitative_sample_rejects_too_few_recent_records(tmp_path):
    questions, answers, comments, indicators = qualitative_tables()

    with pytest.raises(QualitativeError, match="fewer than requested sample size"):
        prepare_qualitative_sample(
            questions=questions,
            answers=answers,
            comments=comments,
            indicators=indicators,
            site_slug="math",
            source_slug="math-answerable-clean-100k",
            date_from="2026-04-21",
            date_to="2026-04-30",
            sample_size=2,
            out_dir=tmp_path / "data/processed/stackexchange-difficulty/qual",
            seed=1,
        )


def test_prepare_qualitative_cli_does_not_print_sampled_content(tmp_path):
    questions, answers, comments, indicators = qualitative_tables()
    questions_path = tmp_path / "questions.tsv"
    answers_path = tmp_path / "answers.tsv"
    comments_path = tmp_path / "comments.tsv"
    indicators_path = tmp_path / "derived_thread_indicators.tsv"
    write_table(questions_path, questions)
    write_table(answers_path, answers)
    write_table(comments_path, comments)
    write_table(indicators_path, indicators)
    out_dir = tmp_path / "data/processed/stackexchange-difficulty/qual"

    result = run_cli(
        [
            "prepare-qualitative-sample",
            "--questions",
            str(questions_path),
            "--answers",
            str(answers_path),
            "--comments",
            str(comments_path),
            "--indicators",
            str(indicators_path),
            "--site-slug",
            "math",
            "--source-slug",
            "math-answerable-clean-100k",
            "--date-from",
            "2025-05-01",
            "--date-to",
            "2026-04-20",
            "--sample-size",
            "6",
            "--out-dir",
            str(out_dir),
        ]
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["ok"] is True
    assert payload["selected_records"] == 6
    assert "Sensitive qualitative title" not in result.stdout
    assert "Sensitive qualitative body" not in result.stdout
    assert "Sensitive qualitative answer" not in result.stdout
    assert "Sensitive qualitative comment" not in result.stdout


def test_summarize_qualitative_coding_writes_aggregate_memo(tmp_path):
    codes_path = tmp_path / "codes.tsv"
    manifest_path = write_manifest(tmp_path, selected_records=6)
    write_codes(codes_path, rows=6)
    out = tmp_path / "qualitative_recent_math_threads_2026-05-18.md"

    result = summarize_qualitative_coding(
        codes=read_table(codes_path, name="qualitative_codes"),
        manifest_path=manifest_path,
        output_path=out,
        labeler="llm_assisted_xhigh",
    )

    text = out.read_text(encoding="utf-8")
    assert result.coded_records == 6
    assert result.unsafe_content_markers == 0
    assert "# Qualitative Analysis Of Recent Mathematics Threads - 2026-05-18" in text
    assert "2025-05-01" in text
    assert "2026-04-20" in text
    assert "math-answerable-clean-100k" in text
    assert "qualitative_difficulty: high=2, low=2, medium=2" in text
    assert "answerability_clarity: clear=4, partially_clear=2" in text
    assert "question_id" not in text
    assert "title" not in text
    assert "body_html" not in text
    assert "answers_for_review" not in text
    assert "comments_for_review" not in text
    assert "Sensitive qualitative" not in text


def test_summarize_qualitative_coding_rejects_invalid_values_and_unsafe_notes(tmp_path):
    codes_path = tmp_path / "codes.tsv"
    manifest_path = write_manifest(tmp_path, selected_records=1)
    write_codes(codes_path, rows=1)
    rows = read_rows(codes_path)
    rows[0]["qualitative_difficulty"] = "very_hard"
    write_rows(codes_path, QUALITATIVE_CODE_COLUMNS, rows)

    with pytest.raises(QualitativeError, match="invalid qualitative_difficulty"):
        summarize_qualitative_coding(
            codes=read_table(codes_path, name="qualitative_codes"),
            manifest_path=manifest_path,
            output_path=tmp_path / "memo.md",
            labeler="llm_assisted_xhigh",
        )

    rows[0]["qualitative_difficulty"] = "high"
    rows[0]["analytic_note"] = "<p>copied record text</p>"
    write_rows(codes_path, QUALITATIVE_CODE_COLUMNS, rows)
    with pytest.raises(QualitativeError, match="unsafe analytic_note"):
        summarize_qualitative_coding(
            codes=read_table(codes_path, name="qualitative_codes"),
            manifest_path=manifest_path,
            output_path=tmp_path / "memo.md",
            labeler="llm_assisted_xhigh",
        )


def test_summarize_qualitative_cli_writes_safe_memo(tmp_path):
    codes_path = tmp_path / "codes.tsv"
    manifest_path = write_manifest(tmp_path, selected_records=3)
    write_codes(codes_path, rows=3)
    out = tmp_path / "memo.md"

    result = run_cli(
        [
            "summarize-qualitative-coding",
            "--codes",
            str(codes_path),
            "--manifest",
            str(manifest_path),
            "--out",
            str(out),
            "--labeler",
            "llm_assisted_xhigh",
        ]
    )

    payload = json.loads(result.stdout)
    text = out.read_text(encoding="utf-8")
    assert result.returncode == 0
    assert payload["ok"] is True
    assert payload["coded_records"] == 3
    assert payload["unsafe_content_markers"] == 0
    assert "Sensitive qualitative" not in result.stdout
    assert "Sensitive qualitative" not in text
    assert "## Discussion Points For Supervisor Meeting" in text


def qualitative_tables(clear_count: int = 3) -> tuple[Table, Table, Table, Table]:
    question_rows = []
    answer_rows = []
    comment_rows = []
    indicator_rows = []
    specs = [
        *[("clear", index) for index in range(clear_count)],
        *[("ordinary", index) for index in range(3)],
        *[("high", index) for index in range(4)],
        ("old", 0),
    ]
    for offset, (group, _index) in enumerate(specs, start=1):
        question_id = str(100 + offset)
        answer_id = str(200 + offset)
        if group == "old":
            creation_date = "2025-04-30T00:00:00"
        else:
            creation_date = f"2025-06-{offset:02d}T00:00:00"
        if group == "clear":
            latency = "0.5"
            comment_count = "1"
            answer_count = "1"
            length = "120"
            contains_error = "false"
        elif group == "ordinary":
            latency = "5"
            comment_count = "2"
            answer_count = "2"
            length = "250"
            contains_error = "false"
        elif group == "high":
            latency = "48"
            comment_count = "8"
            answer_count = "3"
            length = "1000"
            contains_error = "false"
        else:
            latency = "0.5"
            comment_count = "1"
            answer_count = "1"
            length = "100"
            contains_error = "false"
        question_rows.append(
            {
                "question_id": question_id if group != "old" else "999",
                "title": f"Sensitive qualitative title {question_id}",
                "body_html": f"<p>Sensitive qualitative body {question_id}</p>",
                "tags": "<calculus>",
                "creation_date": creation_date,
                "score": "2",
                "view_count": "1000",
                "answer_count": answer_count,
                "comment_count": comment_count,
                "closed_date": "",
                "accepted_answer_id": answer_id,
                "is_duplicate": "false",
                "content_license": "CC BY-SA 4.0",
            }
        )
        answer_rows.append(
            {
                "answer_id": answer_id,
                "question_id": question_id if group != "old" else "999",
                "body_html": f"<p>Sensitive qualitative answer {question_id}</p>",
                "score": "1",
                "creation_date": creation_date,
                "is_accepted": "true",
            }
        )
        comment_rows.append(
            {
                "comment_id": str(300 + offset),
                "post_id": question_id if group != "old" else "999",
                "text": f"Sensitive qualitative comment {question_id}",
                "score": "0",
                "creation_date": creation_date,
                "content_license": "CC BY-SA 4.0",
            }
        )
        indicator_rows.append(
            {
                "question_id": question_id if group != "old" else "999",
                "has_answer": "true",
                "has_accepted_answer": "true",
                "is_unanswered": "false",
                "is_closed": "false",
                "is_duplicate": "false",
                "time_to_first_answer_hours": latency,
                "time_to_accepted_answer_hours": latency,
                "comment_count_before_first_answer": "0",
                "tag_popularity_bucket": "high",
                "rare_tag_flag": "false",
                "question_length": length,
                "code_block_count": "0",
                "contains_error_message": contains_error,
            }
        )
    return (
        Table("questions", question_rows, QUESTIONS_COLUMNS),
        Table("answers", answer_rows, ANSWERS_COLUMNS),
        Table("comments", comment_rows, COMMENTS_COLUMNS),
        Table("indicators", indicator_rows, INDICATOR_COLUMNS),
    )


def write_manifest(tmp_path: Path, *, selected_records: int) -> Path:
    manifest = {
        "site_slug": "math",
        "source_slug": "math-answerable-clean-100k",
        "date_from": "2025-05-01",
        "date_to": "2026-04-20",
        "selected_records": selected_records,
        "sample_group_counts": {
            "clear_direct": 1,
            "ordinary_intermediate": 1,
            "high_effort_or_ambiguous": max(0, selected_records - 2),
        },
    }
    path = tmp_path / "sample_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def write_codes(path: Path, *, rows: int) -> None:
    values = [
        (
            "low",
            "clear",
            "conceptual",
            "direct_solution",
            "no_comments_needed",
            "none",
            "no",
            "keep_main_clean_corpus",
        ),
        (
            "medium",
            "clear",
            "proof_based",
            "proof",
            "comments_not_available_or_not_needed",
            "minor",
            "no",
            "keep_main_clean_corpus",
        ),
        (
            "high",
            "partially_clear",
            "multi_step_reasoning",
            "explanation",
            "comments_clarify_question",
            "significant",
            "yes",
            "add_diagnostic_subset",
        ),
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUALITATIVE_CODE_COLUMNS, delimiter="\t")
        writer.writeheader()
        for index in range(1, rows + 1):
            row_values = values[(index - 1) % len(values)]
            writer.writerow(
                {
                    "record_index": str(index),
                    "sample_group": sample_group_for_index(index),
                    "qualitative_difficulty": row_values[0],
                    "answerability_clarity": row_values[1],
                    "source_of_difficulty": row_values[2],
                    "answer_type": row_values[3],
                    "interaction_role": row_values[4],
                    "notation_or_formulation_issue": row_values[5],
                    "comments_needed": row_values[6],
                    "corpus_design_implication": row_values[7],
                    "analytic_note": "",
                }
            )


def sample_group_for_index(index: int) -> str:
    if index % 3 == 1:
        return "clear_direct"
    if index % 3 == 2:
        return "ordinary_intermediate"
    return "high_effort_or_ambiguous"


def write_table(path: Path, table: Table) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table.columns), delimiter="\t")
        writer.writeheader()
        writer.writerows(table.rows)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_rows(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), delimiter="\t")
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


QUESTIONS_COLUMNS = (
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
)
ANSWERS_COLUMNS = (
    "answer_id",
    "question_id",
    "body_html",
    "score",
    "creation_date",
    "is_accepted",
)
COMMENTS_COLUMNS = (
    "comment_id",
    "post_id",
    "text",
    "score",
    "creation_date",
    "content_license",
)
INDICATOR_COLUMNS = (
    "question_id",
    "has_answer",
    "has_accepted_answer",
    "is_unanswered",
    "is_closed",
    "is_duplicate",
    "time_to_first_answer_hours",
    "time_to_accepted_answer_hours",
    "comment_count_before_first_answer",
    "tag_popularity_bucket",
    "rare_tag_flag",
    "question_length",
    "code_block_count",
    "contains_error_message",
)
