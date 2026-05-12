"""JSONL export for thread-level analysis."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from stackexchange_difficulty.validation import Table


def build_threads(
    questions: Table,
    answers: Table | None = None,
    comments: Table | None = None,
    indicators: list[dict[str, Any]] | None = None,
    provenance: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    answers_by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    answer_to_question: dict[str, str] = {}
    if answers:
        for answer in answers.rows:
            question_id = str(answer["question_id"]).strip()
            answers_by_question[question_id].append(answer)
            answer_to_question[str(answer["answer_id"]).strip()] = question_id

    comments_by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if comments:
        for comment in comments.rows:
            post_id = str(comment["post_id"]).strip()
            question_id = (
                post_id
                if post_id in answers_by_question
                else answer_to_question.get(post_id, post_id)
            )
            comments_by_question[question_id].append(comment)

    indicators_by_question = {
        str(indicator["question_id"]).strip(): indicator for indicator in indicators or []
    }

    threads: list[dict[str, Any]] = []
    for question in questions.rows:
        question_id = str(question["question_id"]).strip()
        threads.append(
            {
                "question_id": question_id,
                "question": question,
                "answers": answers_by_question.get(question_id, []),
                "comments": comments_by_question.get(question_id, []),
                "indicators": indicators_by_question.get(question_id, {}),
                "validation": {},
                "provenance": provenance or {},
            }
        )
    return threads


def write_jsonl(rows: list[dict[str, Any]], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
