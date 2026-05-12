from __future__ import annotations

from stackexchange_difficulty.provenance import load_provenance
from stackexchange_difficulty.validation import Table, read_table, validate_dataset


def fixture_table(name: str):
    return read_table(f"tests/fixtures/{name}.tsv", name=name)


def test_complete_fixture_dataset_validates_successfully():
    report = validate_dataset(
        fixture_table("questions"),
        answers=fixture_table("answers"),
        comments=fixture_table("comments"),
        provenance=load_provenance("tests/fixtures/provenance.json"),
    )

    assert report.ok
    assert report.issues == []
    assert report.row_counts == {"questions": 3, "answers": 2, "comments": 2}


def test_missing_required_columns_fail():
    table = fixture_table("questions")
    broken = Table(
        name="questions",
        rows=table.rows,
        columns=tuple(c for c in table.columns if c != "tags"),
    )

    report = validate_dataset(broken)

    assert not report.ok
    assert report.issues[0].code == "missing_required_columns"
    assert "tags" in report.issues[0].message


def test_duplicate_question_id_fails():
    table = fixture_table("questions")
    duplicate = Table(name="questions", rows=[*table.rows, table.rows[0]], columns=table.columns)

    report = validate_dataset(duplicate)

    assert not report.ok
    assert any(issue.code == "duplicate_question_id" for issue in report.issues)


def test_artificial_post_ids_fail_for_both_documented_ids():
    table = fixture_table("questions")
    rows = [
        {**table.rows[0], "question_id": "1000000001"},
        {**table.rows[1], "question_id": "1000000010"},
    ]
    broken = Table(name="questions", rows=rows, columns=table.columns)

    report = validate_dataset(broken)

    assert not report.ok
    artificial_ids = {
        issue.row_id for issue in report.issues if issue.code == "artificial_post_id"
    }
    assert artificial_ids == {"1000000001", "1000000010"}


def test_missing_accepted_answer_fails():
    questions = fixture_table("questions")
    rows = [
        {**row, "accepted_answer_id": "999"} if row["question_id"] == "101" else row
        for row in questions.rows
    ]
    broken = Table(name="questions", rows=rows, columns=questions.columns)

    report = validate_dataset(broken, answers=fixture_table("answers"))

    assert not report.ok
    assert any(issue.code == "accepted_answer_missing" for issue in report.issues)


def test_incomplete_provenance_rejected():
    report = validate_dataset(
        fixture_table("questions"),
        answers=fixture_table("answers"),
        provenance={"source_method": "synthetic_fixture"},
    )

    assert not report.ok
    codes = {issue.code for issue in report.issues}
    assert "provenance_missing_required_key" in codes
    assert "provenance_missing_source_identifier" in codes
