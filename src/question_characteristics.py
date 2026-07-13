"""This module calculates the documented fields for one Stack Exchange question.

``build_characteristics.py`` finds the related question, answer, comment, and
acceptance rows.  This module turns those rows into the 49 columns described in
``config/characteristics.tsv``.  Keeping the formulas together supports direct
comparison between the implementation and the data dictionary.

The module is used as a library by ``build_characteristics.py`` and has no
command-line interface.  It requires Beautiful Soup for rendered-HTML parsing;
all source row dictionaries remain unchanged.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from statistics import median
from typing import Any

from bs4 import BeautifulSoup

from stackexchange_xml import (
    describe_row,
    parse_stack_datetime,
    positive_id,
)


TAG_PATTERN = re.compile(r"<([^<>]+)>")
WORD_PATTERN = re.compile(r"\b[^\W_]+(?:[-'][^\W_]+)*\b", re.UNICODE)


def optional_stack_datetime(
    value: str | None, context: str, field: str
) -> datetime | None:
    """Parses an optional Stack Exchange timestamp when it is present."""
    return parse_stack_datetime(value, context, field) if value else None


def optional_integer(value: str | None, context: str, field: str) -> int | None:
    """Parses an optional integer source field."""
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"{context}: invalid integer {field}={value!r}") from None


def optional_count(value: str | None, context: str, field: str) -> int | None:
    """Parses an optional source count and requires a value of zero or greater."""
    parsed = optional_integer(value, context, field)
    if parsed is not None and parsed < 0:
        raise ValueError(f"{context}: {field} must be zero or greater")
    return parsed


def readable_text(html_value: str | None) -> str:
    """Converts rendered HTML into normalized visible text."""
    if not html_value:
        return ""
    soup = BeautifulSoup(html_value, "html.parser")
    return " ".join(soup.get_text(" ", strip=True).split())


def content_measurements(body_html: str | None) -> dict[str, int | str]:
    """Calculates visible text, prose words, code size, links, and images.

    Word counts exclude ``pre`` and ``code`` content.  Code characters include
    the text inside every ``code`` element, including whitespace.  Code lines
    count nonempty lines inside ``pre`` blocks.  Missing HTML produces empty
    text and zero counts; the input string is never modified.
    """
    soup = BeautifulSoup(body_html or "", "html.parser")
    body_text = " ".join(soup.get_text(" ", strip=True).split())
    code_lines = sum(
        1
        for block in soup.find_all("pre")
        for line in block.get_text("\n").splitlines()
        if line.strip()
    )

    prose = BeautifulSoup(body_html or "", "html.parser")
    for element in prose.find_all(["pre", "code"]):
        element.decompose()
    prose_text = " ".join(prose.get_text(" ", strip=True).split())
    return {
        "question_body_text": body_text,
        "question_word_count": len(WORD_PATTERN.findall(prose_text)),
        "code_character_count": sum(
            len(element.get_text()) for element in soup.find_all("code")
        ),
        "code_line_count": code_lines,
        "link_count": len(soup.find_all("a", href=True)),
        "image_count": len(soup.find_all("img")),
    }


def tag_names(raw_tags: str | None) -> list[str]:
    """Extracts names from Stack Exchange's ``<tag><tag>`` notation."""
    return TAG_PATTERN.findall(raw_tags or "")


def non_negative_hours(later: datetime, earlier: datetime, label: str) -> float:
    """Returns elapsed hours and rejects an event that precedes its source."""
    hours = (later - earlier).total_seconds() / 3600
    if hours < 0:
        raise ValueError(
            f"negative {label}: {later.isoformat()} precedes {earlier.isoformat()}"
        )
    return round(hours, 6)


def validated_question(
    question: dict[str, str], posts_path: Path
) -> tuple[str, str, datetime]:
    """Validates one question and returns its context, ID, and creation time."""
    context = describe_row(posts_path, question)
    question_id = positive_id(question.get("Id"), context)
    question_created = parse_stack_datetime(
        question.get("CreationDate"), context, "CreationDate"
    )
    for field in ("LastEditDate", "ClosedDate"):
        event_time = optional_stack_datetime(question.get(field), context, field)
        if event_time is not None:
            non_negative_hours(event_time, question_created, field)
    return context, question_id, question_created


def question_fields(
    question: dict[str, str],
    context: str,
    question_id: str,
    question_created: datetime,
    site: str,
    dump_date: date,
) -> dict[str, Any]:
    """Returns source fields and content measurements for one question."""
    tags = tag_names(question.get("Tags"))
    measurements = content_measurements(question.get("Body"))
    measurements["tag_count"] = len(tags)
    stackexchange_answer_count = optional_count(
        question.get("AnswerCount"), context, "AnswerCount"
    )
    fields: dict[str, Any] = {
        "site": site,
        "dump_snapshot_date": dump_date.isoformat(),
        "question_id": question_id,
        "question_url": f"https://{site}/questions/{question_id}",
        "question_creation_datetime": question.get("CreationDate"),
        "question_last_edit_datetime": question.get("LastEditDate"),
        "question_title": question.get("Title"),
        "question_body_html": question.get("Body"),
        "question_tags_raw": question.get("Tags"),
        "question_tags": ";".join(tags),
        "question_content_license": question.get("ContentLicense"),
        "owner_user_id": question.get("OwnerUserId"),
        "owner_display_name": question.get("OwnerDisplayName"),
        "question_score": optional_integer(question.get("Score"), context, "Score"),
        "question_view_count": optional_count(
            question.get("ViewCount"), context, "ViewCount"
        ),
        "stackexchange_answer_count": stackexchange_answer_count,
        "has_stackexchange_answer": (
            stackexchange_answer_count > 0
            if stackexchange_answer_count is not None
            else None
        ),
        "stackexchange_comment_count": optional_count(
            question.get("CommentCount"), context, "CommentCount"
        ),
        "closed_datetime": question.get("ClosedDate"),
        "observation_days_at_dump": (dump_date - question_created.date()).days,
    }
    fields.update(measurements)
    return fields


def answer_response_fields(
    answers: list[dict[str, str]],
    question_created: datetime,
    posts_path: Path,
) -> tuple[dict[str, Any], datetime | None, list[int]]:
    """Returns response fields plus values needed by later calculations."""
    answer_times: list[float] = []
    answer_scores: list[int | None] = []
    answer_creation_times: list[datetime] = []

    for answer in answers:
        answer_context = describe_row(posts_path, answer)
        answer_created = parse_stack_datetime(
            answer.get("CreationDate"), answer_context, "CreationDate"
        )
        answer_creation_times.append(answer_created)
        answer_times.append(
            non_negative_hours(
                answer_created, question_created, "answer response time"
            )
        )
        answer_scores.append(optional_integer(answer.get("Score"), answer_context, "Score"))

    first_answer = answers[0] if answers else None
    first_answer_created = answer_creation_times[0] if answer_creation_times else None
    available_scores = [score for score in answer_scores if score is not None]
    fields = {
        "available_answer_count": len(answers),
        "has_available_answer": bool(answers),
        "first_answer_id": first_answer.get("Id") if first_answer else None,
        "first_answer_creation_datetime": (
            first_answer.get("CreationDate") if first_answer else None
        ),
        "time_to_first_answer_hours": answer_times[0] if answer_times else None,
        "median_answer_response_hours": (
            round(median(answer_times), 6) if answer_times else None
        ),
        "answer_score_spread": (
            max(available_scores) - min(available_scores)
            if available_scores
            else None
        ),
    }
    return fields, first_answer_created, available_scores


def find_accepted_answer(
    question: dict[str, str],
    answers: list[dict[str, str]],
    context: str,
) -> tuple[str | None, dict[str, str] | None]:
    """Returns the accepted-answer ID and its available answer row."""
    accepted_answer_id = question.get("AcceptedAnswerId")
    if accepted_answer_id:
        accepted_answer_id = positive_id(
            accepted_answer_id, context, "AcceptedAnswerId"
        )
    accepted_answer = next(
        (answer for answer in answers if answer.get("Id") == accepted_answer_id), None
    )
    return accepted_answer_id, accepted_answer


def acceptance_event_fields(
    accepted_answer_id: str | None,
    accepted_answer_created: datetime | None,
    acceptance_dates: dict[str, date],
    question_created: datetime,
    context: str,
) -> dict[str, str | int | None]:
    """Returns the acceptance date and validates its order."""
    acceptance_date = acceptance_dates.get(accepted_answer_id or "")
    days_to_acceptance = (
        (acceptance_date - question_created.date()).days
        if acceptance_date is not None
        else None
    )
    if days_to_acceptance is not None and days_to_acceptance < 0:
        raise ValueError(f"{context}: acceptance date precedes question creation date")
    if (
        acceptance_date is not None
        and accepted_answer_created is not None
        and acceptance_date < accepted_answer_created.date()
    ):
        raise ValueError(
            f"{context}: acceptance date precedes accepted-answer post date"
        )
    return {
        "acceptance_date": acceptance_date.isoformat() if acceptance_date else None,
        "days_to_acceptance": days_to_acceptance,
    }


def accepted_answer_fields(
    question: dict[str, str],
    answers: list[dict[str, str]],
    acceptance_dates: dict[str, date],
    available_scores: list[int],
    question_created: datetime,
    context: str,
    site: str,
    posts_path: Path,
) -> dict[str, Any]:
    """Returns fields describing the selected answer and its acceptance event."""
    accepted_answer_id, accepted_answer = find_accepted_answer(
        question, answers, context
    )
    accepted_context = (
        describe_row(posts_path, accepted_answer) if accepted_answer else ""
    )
    accepted_answer_created = (
        parse_stack_datetime(
            accepted_answer.get("CreationDate"), accepted_context, "CreationDate"
        )
        if accepted_answer
        else None
    )
    accepted_score = (
        optional_integer(accepted_answer.get("Score"), accepted_context, "Score")
        if accepted_answer
        else None
    )
    fields: dict[str, Any] = {
        "accepted_answer_id": accepted_answer_id,
        "accepted_answer_available": accepted_answer is not None,
        "accepted_answer_creation_datetime": (
            accepted_answer.get("CreationDate") if accepted_answer else None
        ),
        "accepted_answer_url": (
            f"https://{site}/a/{accepted_answer_id}"
            if accepted_answer_id
            else None
        ),
        "accepted_answer_owner_user_id": (
            accepted_answer.get("OwnerUserId") if accepted_answer else None
        ),
        "accepted_answer_owner_display_name": (
            accepted_answer.get("OwnerDisplayName") if accepted_answer else None
        ),
        "accepted_answer_content_license": (
            accepted_answer.get("ContentLicense") if accepted_answer else None
        ),
        "time_to_eventually_accepted_answer_post_hours": (
            non_negative_hours(
                accepted_answer_created,
                question_created,
                "eventually accepted-answer posting time",
            )
            if accepted_answer_created is not None
            else None
        ),
        "accepted_answer_score": accepted_score,
        "accepted_answer_body_text": (
            readable_text(accepted_answer.get("Body")) if accepted_answer else None
        ),
        "accepted_answer_score_rank": (
            1 + sum(score > accepted_score for score in available_scores)
            if accepted_score is not None
            else None
        ),
    }
    fields.update(
        acceptance_event_fields(
            accepted_answer_id,
            accepted_answer_created,
            acceptance_dates,
            question_created,
            context,
        )
    )
    return fields


def question_comment_fields(
    comments: list[dict[str, str]],
    question_created: datetime,
    first_answer_created: datetime | None,
    comments_path: Path,
) -> dict[str, int | None]:
    """Returns direct-question comment counts and validates their timestamps."""
    comment_times = [
        parse_stack_datetime(
            comment.get("CreationDate"),
            describe_row(comments_path, comment),
            "CreationDate",
        )
        for comment in comments
    ]
    for comment_time in comment_times:
        non_negative_hours(comment_time, question_created, "question-comment time")
    comments_before_first = (
        sum(created < first_answer_created for created in comment_times)
        if first_answer_created is not None
        else None
    )
    return {
        "available_question_comment_count": len(comments),
        "comments_before_first_answer": comments_before_first,
    }


def build_characteristic_row(
    question: dict[str, str],
    answers: list[dict[str, str]],
    comments: list[dict[str, str]],
    acceptance_dates: dict[str, date],
    site: str,
    dump_date: date,
    posts_path: Path,
    comments_path: Path,
) -> dict[str, Any]:
    """Creates one documented 49-field row for one question.

    Related answers and direct question comments must already be ordered.  Each
    helper below handles one understandable part of the row.  Invalid source
    values or events preceding the question raise contextual ``ValueError``.
    Input rows remain unchanged.
    """
    context, question_id, question_created = validated_question(question, posts_path)
    response_fields, first_answer_created, available_scores = answer_response_fields(
        answers, question_created, posts_path
    )

    row = question_fields(
        question,
        context,
        question_id,
        question_created,
        site,
        dump_date,
    )
    row.update(response_fields)
    row.update(
        accepted_answer_fields(
            question,
            answers,
            acceptance_dates,
            available_scores,
            question_created,
            context,
            site,
            posts_path,
        )
    )
    row.update(
        question_comment_fields(
            comments, question_created, first_answer_created, comments_path
        )
    )
    return row
