"""SEDE pilot export normalization."""

from __future__ import annotations

from typing import Any

from stackexchange_difficulty.schema import COMMENT_REQUIRED_COLUMNS, SEDE_PILOT_REQUIRED_COLUMNS
from stackexchange_difficulty.validation import Table, ValidationIssue, validate_required_columns


def validate_sede_export(table: Table) -> list[ValidationIssue]:
    return validate_required_columns(table, SEDE_PILOT_REQUIRED_COLUMNS)


def normalize_sede_export(table: Table) -> tuple[Table, Table, Table]:
    """Convert a SEDE pilot export into canonical question/answer/comment tables."""
    questions: list[dict[str, Any]] = []
    answers: list[dict[str, Any]] = []
    seen_answers: set[str] = set()

    for row in table.rows:
        question_id = _clean(row.get("question_id"))
        accepted_answer_id = _clean(row.get("accepted_answer_id"))
        questions.append(
            {
                "question_id": question_id,
                "title": _clean(row.get("title")),
                "body_html": _clean(row.get("body_html")),
                "tags": _clean(row.get("tags")),
                "creation_date": _clean(row.get("creation_date")),
                "score": _clean(row.get("score")),
                "view_count": _clean(row.get("view_count")),
                "answer_count": _clean(row.get("answer_count")),
                "comment_count": _clean(row.get("comment_count")),
                "closed_date": _clean(row.get("closed_date")),
                "accepted_answer_id": accepted_answer_id,
                "is_duplicate": _clean(row.get("is_duplicate")),
                "content_license": _clean(row.get("content_license")),
            }
        )

        _append_answer(
            answers,
            seen_answers,
            answer_id=_clean(row.get("first_answer_id")),
            question_id=question_id,
            body_html=_clean(row.get("first_answer_body_html")),
            score=_clean(row.get("first_answer_score")),
            creation_date=_clean(row.get("first_answer_creation_date")),
            is_accepted=_clean(row.get("first_answer_id")) == accepted_answer_id,
        )
        _append_answer(
            answers,
            seen_answers,
            answer_id=accepted_answer_id,
            question_id=question_id,
            body_html=_clean(row.get("accepted_answer_body_html")),
            score=_clean(row.get("accepted_answer_score")),
            creation_date=_clean(row.get("accepted_answer_creation_date")),
            is_accepted=bool(accepted_answer_id),
        )

    return (
        Table(name="questions", rows=questions, columns=tuple(questions[0]) if questions else ()),
        Table(name="answers", rows=answers, columns=_answer_columns()),
        Table(name="comments", rows=[], columns=COMMENT_REQUIRED_COLUMNS),
    )


def _append_answer(
    answers: list[dict[str, Any]],
    seen_answers: set[str],
    *,
    answer_id: str,
    question_id: str,
    body_html: str,
    score: str,
    creation_date: str,
    is_accepted: bool,
) -> None:
    if not answer_id or answer_id in seen_answers:
        return
    answers.append(
        {
            "answer_id": answer_id,
            "question_id": question_id,
            "body_html": body_html,
            "score": score,
            "creation_date": creation_date,
            "is_accepted": str(is_accepted).lower(),
        }
    )
    seen_answers.add(answer_id)


def _answer_columns() -> tuple[str, ...]:
    return ("answer_id", "question_id", "body_html", "score", "creation_date", "is_accepted")


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()
