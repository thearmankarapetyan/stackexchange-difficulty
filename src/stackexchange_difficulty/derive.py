"""Derived indicators for Stack Exchange-like thread records."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime
from html import unescape
from typing import Any

from stackexchange_difficulty.validation import Table, truthy

ERROR_PATTERN = re.compile(r"error|exception|traceback|failed|failure|warning", re.IGNORECASE)
TAG_PATTERN = re.compile(r"<([^<>]+)>")
TAG_SPLIT_PATTERN = re.compile(r"[,;\s]+")
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
CODE_BLOCK_PATTERN = re.compile(r"<pre\b|```", re.IGNORECASE)


def derive_indicators(
    questions: Table,
    answers: Table | None = None,
    comments: Table | None = None,
) -> list[dict[str, Any]]:
    answers_by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if answers:
        for answer in answers.rows:
            answers_by_question[str(answer["question_id"]).strip()].append(answer)

    comments_by_post: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if comments:
        for comment in comments.rows:
            comments_by_post[str(comment["post_id"]).strip()].append(comment)

    tag_counts = Counter(tag for row in questions.rows for tag in parse_tags(row.get("tags", "")))
    indicators: list[dict[str, Any]] = []
    for question in questions.rows:
        question_id = str(question["question_id"]).strip()
        question_answers = sorted(
            answers_by_question.get(question_id, []),
            key=lambda row: parse_datetime(row.get("creation_date")),
        )
        accepted_id = str(question.get("accepted_answer_id", "")).strip()
        accepted_answer = next(
            (
                row
                for row in question_answers
                if str(row.get("answer_id", "")).strip() == accepted_id
            ),
            None,
        )
        first_answer = question_answers[0] if question_answers else None
        question_created = parse_datetime(question.get("creation_date"))
        first_answer_time = (
            parse_datetime(first_answer.get("creation_date")) if first_answer else None
        )
        accepted_time = (
            parse_datetime(accepted_answer.get("creation_date")) if accepted_answer else None
        )
        tags = parse_tags(question.get("tags", ""))
        body_html = str(question.get("body_html", ""))

        indicators.append(
            {
                "question_id": question_id,
                "has_answer": bool(question_answers),
                "has_accepted_answer": accepted_answer is not None,
                "is_unanswered": not question_answers,
                "is_closed": bool(str(question.get("closed_date", "")).strip()),
                "is_duplicate": truthy(question.get("is_duplicate")),
                "time_to_first_answer_hours": elapsed_hours(question_created, first_answer_time),
                "time_to_accepted_answer_hours": elapsed_hours(question_created, accepted_time),
                "comment_count_before_first_answer": count_comments_before(
                    comments_by_post.get(question_id, []),
                    first_answer_time,
                ),
                "tag_popularity_bucket": tag_popularity_bucket(tags, tag_counts),
                "rare_tag_flag": bool(tags) and all(tag_counts[tag] == 1 for tag in tags),
                "question_length": len(strip_html(body_html).split()),
                "code_block_count": len(CODE_BLOCK_PATTERN.findall(body_html)),
                "contains_error_message": bool(ERROR_PATTERN.search(strip_html(body_html))),
            }
        )
    return indicators


def parse_datetime(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        try:
            return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None


def elapsed_hours(start: datetime | None, end: datetime | None) -> float | None:
    if start is None or end is None:
        return None
    return round((end - start).total_seconds() / 3600, 4)


def parse_tags(value: Any) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    bracketed = TAG_PATTERN.findall(text)
    if bracketed:
        return [tag.strip().lower() for tag in bracketed if tag.strip()]
    return [tag.strip().lower() for tag in TAG_SPLIT_PATTERN.split(text) if tag.strip()]


def tag_popularity_bucket(tags: list[str], tag_counts: Counter[str]) -> str:
    if not tags:
        return "none"
    maximum = max(tag_counts[tag] for tag in tags)
    if maximum >= 3:
        return "high"
    if maximum == 2:
        return "medium"
    return "low"


def count_comments_before(comments: list[dict[str, Any]], cutoff: datetime | None) -> int:
    if cutoff is None:
        return 0
    count = 0
    for comment in comments:
        created = parse_datetime(comment.get("creation_date"))
        if created is not None and created < cutoff:
            count += 1
    return count


def strip_html(value: str) -> str:
    return unescape(HTML_TAG_PATTERN.sub(" ", value)).strip()
