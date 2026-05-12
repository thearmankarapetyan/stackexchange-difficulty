from __future__ import annotations

import json

from stackexchange_difficulty.derive import derive_indicators
from stackexchange_difficulty.jsonl import build_threads, write_jsonl
from stackexchange_difficulty.provenance import load_provenance
from stackexchange_difficulty.validation import read_table


def test_derived_indicators_match_expected_fixture_values():
    questions = read_table("tests/fixtures/questions.tsv", name="questions")
    answers = read_table("tests/fixtures/answers.tsv", name="answers")
    comments = read_table("tests/fixtures/comments.tsv", name="comments")

    by_question = {
        row["question_id"]: row
        for row in derive_indicators(questions, answers=answers, comments=comments)
    }

    assert by_question["101"]["has_answer"] is True
    assert by_question["101"]["has_accepted_answer"] is True
    assert by_question["101"]["is_unanswered"] is False
    assert by_question["101"]["is_closed"] is False
    assert by_question["101"]["is_duplicate"] is False
    assert by_question["101"]["time_to_first_answer_hours"] == 2.0
    assert by_question["101"]["time_to_accepted_answer_hours"] == 2.0
    assert by_question["101"]["comment_count_before_first_answer"] == 1
    assert by_question["101"]["code_block_count"] == 1
    assert by_question["101"]["contains_error_message"] is True

    assert by_question["102"]["has_answer"] is False
    assert by_question["102"]["is_unanswered"] is True
    assert by_question["102"]["is_closed"] is True
    assert by_question["102"]["is_duplicate"] is True


def test_jsonl_output_contains_one_grouped_thread_per_question(tmp_path):
    questions = read_table("tests/fixtures/questions.tsv", name="questions")
    answers = read_table("tests/fixtures/answers.tsv", name="answers")
    comments = read_table("tests/fixtures/comments.tsv", name="comments")
    provenance = load_provenance("tests/fixtures/provenance.json")
    indicators = derive_indicators(questions, answers=answers, comments=comments)

    threads = build_threads(
        questions,
        answers=answers,
        comments=comments,
        indicators=indicators,
        provenance=provenance,
    )
    out = tmp_path / "threads.jsonl"
    write_jsonl(threads, out)

    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 3
    first = rows[0]
    assert first["question_id"] == "101"
    assert len(first["answers"]) == 1
    assert len(first["comments"]) == 2
    assert "indicators" in first
    assert "validation" in first
    assert first["provenance"]["source_method"] == "synthetic_fixture"
