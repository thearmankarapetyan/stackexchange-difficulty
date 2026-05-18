from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from stackexchange_difficulty.puzzling import (
    PUZZLING_QUALITATIVE_CODE_COLUMNS,
    PuzzlingError,
    prepare_puzzling_qualitative_sample,
    summarize_puzzling_qualitative_coding,
)
from stackexchange_difficulty.schema import (
    ANSWER_REQUIRED_COLUMNS,
    COMMENT_REQUIRED_COLUMNS,
    DERIVED_COLUMNS,
    QUESTION_REQUIRED_COLUMNS,
)
from stackexchange_difficulty.validation import Table, read_table


def test_prepare_puzzling_qualitative_sample_filters_recent_dates_and_writes_templates(tmp_path):
    questions, answers, comments, indicators = puzzling_tables()
    out_dir = tmp_path / "data/processed/stackexchange-difficulty/puzzling-qual"

    result = prepare_puzzling_qualitative_sample(
        questions=questions,
        answers=answers,
        comments=comments,
        indicators=indicators,
        date_from="2025-05-01",
        date_to="2026-04-21",
        sample_size=4,
        out_dir=out_dir,
        seed=20260518,
    )

    assert result.selected_records == 4
    assert result.review_path.name == "qualitative_review.tsv"
    assert result.codes_path.name == "qualitative_codes.tsv"
    review = read_table(result.review_path, name="review")
    codes = read_table(result.codes_path, name="codes")
    assert len(review.rows) == 4
    assert len(codes.rows) == 4
    assert set(row["sample_group"] for row in review.rows) <= {
        "clear_direct",
        "ordinary_intermediate",
        "high_effort_or_ambiguous",
        "language_or_lateral",
    }
    assert tuple(codes.columns) == PUZZLING_QUALITATIVE_CODE_COLUMNS
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["recent_candidate_count"] == 5
    assert manifest["selected_records"] == 4


def test_prepare_puzzling_qualitative_sample_allows_partial_but_rejects_too_small(tmp_path):
    questions, answers, comments, indicators = puzzling_tables(row_count=35)
    out_dir = tmp_path / "data/processed/stackexchange-difficulty/partial"

    result = prepare_puzzling_qualitative_sample(
        questions=questions,
        answers=answers,
        comments=comments,
        indicators=indicators,
        date_from="2025-05-01",
        date_to="2026-04-21",
        sample_size=50,
        out_dir=out_dir,
        seed=1,
    )

    assert result.selected_records == 35
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["partial_sample"] is True

    small_questions, small_answers, small_comments, small_indicators = puzzling_tables(row_count=29)
    with pytest.raises(PuzzlingError, match="fewer than minimum qualitative records"):
        prepare_puzzling_qualitative_sample(
            questions=small_questions,
            answers=small_answers,
            comments=small_comments,
            indicators=small_indicators,
            date_from="2025-05-01",
            date_to="2026-04-21",
            sample_size=50,
            out_dir=tmp_path / "data/processed/stackexchange-difficulty/small",
            seed=1,
        )


def test_prepare_puzzling_qualitative_cli_does_not_print_sampled_content(tmp_path):
    questions, answers, comments, indicators = puzzling_tables()
    questions_path = tmp_path / "questions.tsv"
    answers_path = tmp_path / "answers.tsv"
    comments_path = tmp_path / "comments.tsv"
    indicators_path = tmp_path / "derived_thread_indicators.tsv"
    write_table(questions_path, questions)
    write_table(answers_path, answers)
    write_table(comments_path, comments)
    write_table(indicators_path, indicators)
    out_dir = tmp_path / "data/processed/stackexchange-difficulty/puzzling-qual"

    result = run_cli(
        [
            "prepare-puzzling-qualitative-sample",
            "--questions",
            str(questions_path),
            "--answers",
            str(answers_path),
            "--comments",
            str(comments_path),
            "--indicators",
            str(indicators_path),
            "--date-from",
            "2025-05-01",
            "--date-to",
            "2026-04-21",
            "--sample-size",
            "4",
            "--out-dir",
            str(out_dir),
        ]
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["selected_records"] == 4
    assert "Sensitive puzzle title" not in result.stdout
    assert "Sensitive puzzle body" not in result.stdout
    assert "Sensitive solution body" not in result.stdout


def test_summarize_puzzling_qualitative_coding_writes_aggregate_memo(tmp_path):
    codes_path = tmp_path / "qualitative_codes.tsv"
    manifest_path = write_manifest(tmp_path, selected_records=6)
    write_codes(codes_path, rows=6)
    out = tmp_path / "qualitative_puzzling_riddle_recent_2026-04-21.md"

    result = summarize_puzzling_qualitative_coding(
        codes=read_table(codes_path, name="qualitative_codes"),
        manifest_path=manifest_path,
        output_path=out,
        labeler="llm_assisted_xhigh",
    )

    text = out.read_text(encoding="utf-8")
    assert result.coded_records == 6
    assert result.unsafe_content_markers == 0
    assert "# Qualitative Analysis Of Recent Puzzling/Riddle Threads - 2026-04-21" in text
    assert "llm_assisted_xhigh" in text
    assert "model_evaluation_suitability: good=4, diagnostic_only=2" in text
    assert "puzzle_type: lateral_thinking=2, riddle=2, wordplay=2" in text
    assert (
        "Puzzling accepted answers are treated as accepted or intended solution candidates"
        in text
    )
    assert "question_id" not in text
    assert "body_html" not in text
    assert "Sensitive puzzle" not in text


def test_summarize_puzzling_qualitative_coding_rejects_invalid_values_and_unsafe_notes(
    tmp_path,
):
    codes_path = tmp_path / "qualitative_codes.tsv"
    manifest_path = write_manifest(tmp_path, selected_records=1)
    write_codes(codes_path, rows=1)
    rows = read_rows(codes_path)
    rows[0]["puzzle_type"] = "math"
    write_rows(codes_path, PUZZLING_QUALITATIVE_CODE_COLUMNS, rows)

    with pytest.raises(PuzzlingError, match="invalid puzzle_type"):
        summarize_puzzling_qualitative_coding(
            codes=read_table(codes_path, name="qualitative_codes"),
            manifest_path=manifest_path,
            output_path=tmp_path / "memo.md",
            labeler="llm_assisted_xhigh",
        )

    rows[0]["puzzle_type"] = "riddle"
    rows[0]["analytic_note"] = "<p>copied puzzle text</p>"
    write_rows(codes_path, PUZZLING_QUALITATIVE_CODE_COLUMNS, rows)
    with pytest.raises(PuzzlingError, match="unsafe analytic_note"):
        summarize_puzzling_qualitative_coding(
            codes=read_table(codes_path, name="qualitative_codes"),
            manifest_path=manifest_path,
            output_path=tmp_path / "memo.md",
            labeler="llm_assisted_xhigh",
        )


def test_summarize_puzzling_qualitative_cli_writes_safe_memo(tmp_path):
    codes_path = tmp_path / "qualitative_codes.tsv"
    manifest_path = write_manifest(tmp_path, selected_records=3)
    write_codes(codes_path, rows=3)
    out = tmp_path / "memo.md"

    result = run_cli(
        [
            "summarize-puzzling-qualitative-coding",
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
    assert "Sensitive puzzle" not in result.stdout
    assert "Sensitive puzzle" not in text
    assert "## Discussion Points For Supervisor" in text


def puzzling_tables(row_count: int = 6) -> tuple[Table, Table, Table, Table]:
    question_rows = []
    answer_rows = []
    comment_rows = []
    indicator_rows = []
    for index in range(1, row_count + 1):
        question_id = str(100 + index)
        answer_id = str(200 + index)
        is_old = index == row_count and row_count <= 10
        created = "2025-04-30T00:00:00" if is_old else f"2025-06-{(index % 25) + 1:02d}T00:00:00"
        tags = "<riddle><wordplay>" if index % 2 else "<lateral-thinking>"
        latency = "0.5" if index % 4 == 0 else "8" if index % 4 == 1 else "72"
        answer_count = "1" if index % 3 == 0 else "3"
        comment_count = "0" if index % 3 == 0 else "4" if index % 3 == 1 else "8"
        question_rows.append(
            {
                "question_id": question_id,
                "title": f"Sensitive puzzle title {question_id}",
                "body_html": f"<p>Sensitive puzzle body {question_id}</p>",
                "tags": tags,
                "creation_date": created,
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
                "question_id": question_id,
                "body_html": f"<p>Sensitive solution body {question_id}</p>",
                "score": "1",
                "creation_date": created,
                "is_accepted": "true",
            }
        )
        comment_rows.append(
            {
                "comment_id": str(300 + index),
                "post_id": question_id,
                "text": f"Sensitive hint comment {question_id}",
                "score": "0",
                "creation_date": created,
                "content_license": "CC BY-SA 4.0",
            }
        )
        indicator_rows.append(
            {
                "question_id": question_id,
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
                "question_length": str(100 + index),
                "code_block_count": "0",
                "contains_error_message": "false",
            }
        )
    return (
        Table("questions", question_rows, QUESTION_REQUIRED_COLUMNS),
        Table("answers", answer_rows, ANSWER_REQUIRED_COLUMNS),
        Table("comments", comment_rows, (*COMMENT_REQUIRED_COLUMNS, "content_license")),
        Table("indicators", indicator_rows, DERIVED_COLUMNS),
    )


def write_manifest(tmp_path: Path, *, selected_records: int) -> Path:
    manifest = {
        "site_slug": "puzzling",
        "source_slug": "puzzling-riddle-clean",
        "date_from": "2025-05-01",
        "date_to": "2026-04-21",
        "selected_records": selected_records,
        "partial_sample": False,
        "sample_group_counts": {
            "clear_direct": 1,
            "ordinary_intermediate": 1,
            "high_effort_or_ambiguous": 1,
            "language_or_lateral": max(0, selected_records - 3),
        },
    }
    path = tmp_path / "sample_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def write_codes(path: Path, *, rows: int) -> None:
    values = [
        ("riddle", "good", "unique_solution", "direct_inference"),
        ("wordplay", "diagnostic_only", "multiple_plausible_solutions", "semantic_association"),
        ("lateral_thinking", "good", "unique_solution", "lateral_inference"),
    ]
    output = []
    for index in range(rows):
        puzzle_type, suitability, clarity, reasoning = values[index % len(values)]
        output.append(
            {
                "record_index": str(index + 1),
                "sample_group": "language_or_lateral"
                if puzzle_type != "riddle"
                else "clear_direct",
                "puzzle_type": puzzle_type,
                "qualitative_difficulty": ("low", "medium", "high")[index % 3],
                "solution_clarity": clarity,
                "reasoning_type": reasoning,
                "language_dependence": ("low", "medium", "high")[index % 3],
                "misdirection_level": ("none", "mild", "strong")[index % 3],
                "outside_knowledge_needed": "no",
                "answer_explanation_quality": "explicit",
                "comments_or_hints_role": "not_needed",
                "model_evaluation_suitability": suitability,
                "corpus_design_implication": "keep_riddle_clean_profile",
                "analytic_note": "",
            }
        )
    write_rows(path, PUZZLING_QUALITATIVE_CODE_COLUMNS, output)


def write_rows(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_table(path: Path, table: Table) -> None:
    write_rows(path, table.columns, table.rows)


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
