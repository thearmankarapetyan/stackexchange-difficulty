"""Content-safe local manual inspection helpers."""

from __future__ import annotations

import csv
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from stackexchange_difficulty.validation import Table, truthy

LABEL_COLUMNS = (
    "record_index",
    "sample_stratum",
    "suitable",
    "answerability_clear",
    "math_notation_readable",
    "needs_comments",
    "reason_code",
    "notes",
)

REVIEW_COLUMNS = (
    "record_index",
    "sample_stratum",
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
    "indicator_has_answer",
    "indicator_has_accepted_answer",
    "indicator_is_unanswered",
    "indicator_is_closed",
    "indicator_is_duplicate",
    "indicator_time_to_first_answer_hours",
    "indicator_tag_popularity_bucket",
    "answers_for_review",
)

INSPECTION_SECTION_HEADING = "## Manual Inspection Summary"
REASON_CODE_PATTERN = re.compile(r"^[a-z0-9_-]+$")


class InspectionError(RuntimeError):
    """Raised when inspection preparation or summary cannot continue safely."""


@dataclass(frozen=True)
class InspectionPrepareResult:
    review_path: Path
    labels_path: Path
    readme_path: Path
    sample_size: int
    site_slug: str
    pilot_date: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "ok": True,
            "review": str(self.review_path),
            "labels": str(self.labels_path),
            "readme": str(self.readme_path),
            "sample_size": self.sample_size,
            "site_slug": self.site_slug,
            "pilot_date": self.pilot_date,
        }


@dataclass(frozen=True)
class InspectionSummaryResult:
    audit_path: Path
    inspected: int
    recommendation: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "ok": True,
            "audit": str(self.audit_path),
            "inspected": self.inspected,
            "recommendation": self.recommendation,
        }


def prepare_inspection_files(
    *,
    questions: Table,
    answers: Table,
    indicators: Table,
    site_slug: str,
    pilot_date: str,
    sample_size: int,
    out_dir: Path,
    seed: int = 20260513,
) -> InspectionPrepareResult:
    if sample_size <= 0:
        raise InspectionError("sample size must be positive")
    _require_ignored_processed_out_dir(out_dir)

    merged = _merge_records(questions, answers, indicators)
    if not merged:
        raise InspectionError("cannot prepare inspection sample from empty questions table")
    sample = _stratified_sample(merged, sample_size=sample_size, seed=seed)

    out_dir.mkdir(parents=True, exist_ok=True)
    review_path = out_dir / "review.tsv"
    labels_path = out_dir / "labels.tsv"
    readme_path = out_dir / "README.md"

    _write_review(review_path, sample)
    _write_labels_template(labels_path, sample)
    readme_path.write_text(
        "\n".join(
            [
                "# Local Manual Inspection",
                "",
                "This directory is ignored by Git because `review.tsv` may contain real "
                "Stack Exchange post text.",
                "",
                "Fill `labels.tsv` using controlled labels only. Do not copy post text, "
                "answer text, usernames, URLs, credentials, or comments into labels.",
                "",
                "Suggested label values are `yes`, `no`, and `uncertain`.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return InspectionPrepareResult(
        review_path=review_path,
        labels_path=labels_path,
        readme_path=readme_path,
        sample_size=len(sample),
        site_slug=site_slug,
        pilot_date=pilot_date,
    )


def summarize_inspection_labels(*, labels: Table, audit_path: Path) -> InspectionSummaryResult:
    missing = [column for column in LABEL_COLUMNS if column not in labels.columns]
    if missing:
        raise InspectionError(f"inspection labels missing required columns: {', '.join(missing)}")

    rows = labels.rows
    reason_counts: Counter[str] = Counter()
    suitable = Counter(_judgment(row.get("suitable")) for row in rows)
    answerability = Counter(_judgment(row.get("answerability_clear")) for row in rows)
    notation = Counter(_judgment(row.get("math_notation_readable")) for row in rows)
    needs_comments = Counter(_judgment(row.get("needs_comments")) for row in rows)
    for row in rows:
        reason = str(row.get("reason_code", "")).strip().lower()
        if not reason:
            continue
        if not REASON_CODE_PATTERN.fullmatch(reason):
            raise InspectionError(
                "reason_code values must use only lowercase letters, digits, "
                "hyphens, and underscores"
            )
        reason_counts[reason] += 1

    recommendation = _recommendation(
        inspected=len(rows),
        suitable=suitable,
        needs_comments=needs_comments,
    )
    summary = _summary_markdown(
        inspected=len(rows),
        suitable=suitable,
        answerability=answerability,
        notation=notation,
        needs_comments=needs_comments,
        reason_counts=reason_counts,
        recommendation=recommendation,
    )
    audit_text = audit_path.read_text(encoding="utf-8")
    audit_path.write_text(_upsert_summary_section(audit_text, summary), encoding="utf-8")
    return InspectionSummaryResult(
        audit_path=audit_path,
        inspected=len(rows),
        recommendation=recommendation,
    )


def _require_ignored_processed_out_dir(out_dir: Path) -> None:
    parts = out_dir.parts
    required = ("data", "processed", "stackexchange-difficulty")
    for index in range(len(parts) - len(required) + 1):
        if parts[index : index + len(required)] == required:
            return
    raise InspectionError(
        "inspection out-dir must be under data/processed/stackexchange-difficulty "
        "so row-level review files remain ignored by Git"
    )


def _merge_records(
    questions: Table,
    answers: Table,
    indicators: Table,
) -> list[dict[str, Any]]:
    answers_by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for answer in answers.rows:
        answers_by_question[str(answer.get("question_id", "")).strip()].append(answer)
    indicators_by_question = {
        str(row.get("question_id", "")).strip(): row for row in indicators.rows
    }

    records: list[dict[str, Any]] = []
    for question in questions.rows:
        question_id = str(question.get("question_id", "")).strip()
        indicator = indicators_by_question.get(question_id, {})
        categories = _categories(question, indicator)
        records.append(
            {
                "question": question,
                "answers": sorted(
                    answers_by_question.get(question_id, []),
                    key=lambda row: str(row.get("creation_date", "")),
                ),
                "indicators": indicator,
                "categories": categories,
                "sample_stratum": ";".join(categories),
            }
        )
    return sorted(records, key=lambda row: _question_sort_key(row["question"]))


def _categories(question: dict[str, Any], indicator: dict[str, Any]) -> list[str]:
    categories = [
        "answered" if _truthy_text(indicator.get("has_answer")) else "unanswered",
        "accepted"
        if _truthy_text(indicator.get("has_accepted_answer"))
        else "no_accepted",
        "closed" if _truthy_text(indicator.get("is_closed")) else "open",
        "duplicate" if _truthy_text(indicator.get("is_duplicate")) else "not_duplicate",
    ]
    latency = _float_or_none(indicator.get("time_to_first_answer_hours"))
    if latency is None:
        categories.append("no_timing")
    elif latency >= 24:
        categories.append("long_latency")
    else:
        categories.append("short_latency")
    bucket = str(indicator.get("tag_popularity_bucket", "") or "none").strip().lower()
    categories.append(f"tag_bucket:{bucket or 'none'}")
    if str(question.get("comment_count", "")).strip() not in {"", "0"}:
        categories.append("has_question_comments")
    return categories


def _stratified_sample(
    records: list[dict[str, Any]],
    *,
    sample_size: int,
    seed: int,
) -> list[dict[str, Any]]:
    if sample_size >= len(records):
        return _with_record_indexes(records)

    rng = random.Random(seed)
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    priority_categories = (
        "answered",
        "unanswered",
        "accepted",
        "no_accepted",
        "open",
        "closed",
        "duplicate",
        "not_duplicate",
        "long_latency",
        "short_latency",
        "no_timing",
        "tag_bucket:high",
        "tag_bucket:medium",
        "tag_bucket:low",
        "tag_bucket:none",
    )
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        for category in record["categories"]:
            by_category[category].append(record)

    for category in priority_categories:
        if len(selected) >= sample_size:
            break
        candidates = list(by_category.get(category, []))
        rng.shuffle(candidates)
        for candidate in candidates:
            question_id = str(candidate["question"].get("question_id", "")).strip()
            if question_id not in selected_ids:
                selected.append(candidate)
                selected_ids.add(question_id)
                break

    remaining = [
        record
        for record in records
        if str(record["question"].get("question_id", "")).strip() not in selected_ids
    ]
    rng.shuffle(remaining)
    selected.extend(remaining[: max(0, sample_size - len(selected))])
    return _with_record_indexes(selected)


def _with_record_indexes(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **record,
            "record_index": str(index),
        }
        for index, record in enumerate(records, start=1)
    ]


def _write_review(path: Path, sample: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS, delimiter="\t")
        writer.writeheader()
        for record in sample:
            question = record["question"]
            indicators = record["indicators"]
            writer.writerow(
                {
                    "record_index": record["record_index"],
                    "sample_stratum": record["sample_stratum"],
                    "question_id": question.get("question_id", ""),
                    "title": question.get("title", ""),
                    "body_html": question.get("body_html", ""),
                    "tags": question.get("tags", ""),
                    "creation_date": question.get("creation_date", ""),
                    "score": question.get("score", ""),
                    "view_count": question.get("view_count", ""),
                    "answer_count": question.get("answer_count", ""),
                    "comment_count": question.get("comment_count", ""),
                    "closed_date": question.get("closed_date", ""),
                    "accepted_answer_id": question.get("accepted_answer_id", ""),
                    "is_duplicate": question.get("is_duplicate", ""),
                    "content_license": question.get("content_license", ""),
                    "indicator_has_answer": indicators.get("has_answer", ""),
                    "indicator_has_accepted_answer": indicators.get(
                        "has_accepted_answer", ""
                    ),
                    "indicator_is_unanswered": indicators.get("is_unanswered", ""),
                    "indicator_is_closed": indicators.get("is_closed", ""),
                    "indicator_is_duplicate": indicators.get("is_duplicate", ""),
                    "indicator_time_to_first_answer_hours": indicators.get(
                        "time_to_first_answer_hours", ""
                    ),
                    "indicator_tag_popularity_bucket": indicators.get(
                        "tag_popularity_bucket", ""
                    ),
                    "answers_for_review": _answers_for_review(record["answers"]),
                }
            )


def _write_labels_template(path: Path, sample: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LABEL_COLUMNS, delimiter="\t")
        writer.writeheader()
        for record in sample:
            writer.writerow(
                {
                    "record_index": record["record_index"],
                    "sample_stratum": record["sample_stratum"],
                    "suitable": "",
                    "answerability_clear": "",
                    "math_notation_readable": "",
                    "needs_comments": "",
                    "reason_code": "",
                    "notes": "",
                }
            )


def _answers_for_review(answers: list[dict[str, Any]]) -> str:
    blocks = []
    for answer in answers:
        blocks.append(
            "\n".join(
                [
                    f"answer_id={answer.get('answer_id', '')}",
                    f"is_accepted={answer.get('is_accepted', '')}",
                    f"score={answer.get('score', '')}",
                    f"creation_date={answer.get('creation_date', '')}",
                    str(answer.get("body_html", "")),
                ]
            )
        )
    return "\n\n--- answer ---\n\n".join(blocks)


def _summary_markdown(
    *,
    inspected: int,
    suitable: Counter[str],
    answerability: Counter[str],
    notation: Counter[str],
    needs_comments: Counter[str],
    reason_counts: Counter[str],
    recommendation: str,
) -> str:
    return "\n".join(
        [
            INSPECTION_SECTION_HEADING,
            "",
            "- Inspection source: local ignored label file under "
            "`data/processed/stackexchange-difficulty/`.",
            f"- Inspected records: {inspected}.",
            f"- Suitable records: {_format_judgments(suitable)}.",
            f"- Answerability clear: {_format_judgments(answerability)}.",
            f"- Math notation readable: {_format_judgments(notation)}.",
            f"- Needs comments: {_format_judgments(needs_comments)}.",
            f"- Top reason codes: {_format_counter(reason_counts, top_n=10)}.",
            f"- Recommendation: {recommendation}.",
            "",
        ]
    )


def _upsert_summary_section(audit_text: str, summary: str) -> str:
    if INSPECTION_SECTION_HEADING in audit_text:
        start = audit_text.index(INSPECTION_SECTION_HEADING)
        following = audit_text.find("\n## ", start + len(INSPECTION_SECTION_HEADING))
        if following == -1:
            return audit_text[:start].rstrip() + "\n\n" + summary
        return audit_text[:start].rstrip() + "\n\n" + summary + audit_text[following:]

    decision_heading = "\n## Decision"
    if decision_heading in audit_text:
        return audit_text.replace(decision_heading, "\n" + summary + decision_heading, 1)
    return audit_text.rstrip() + "\n\n" + summary


def _recommendation(
    *,
    inspected: int,
    suitable: Counter[str],
    needs_comments: Counter[str],
) -> str:
    if inspected == 0:
        return "manual_inspection_incomplete"
    unsuitable_or_uncertain = suitable["no"] + suitable["uncertain"]
    if needs_comments["yes"] / inspected > 0.20:
        return "needs_comment_enrichment"
    if unsuitable_or_uncertain / inspected > 0.20:
        return "revise_query_or_sampling"
    if suitable["yes"] / inspected >= 0.80:
        return "go_for_larger_design"
    return "manual_inspection_review_required"


def _format_judgments(counter: Counter[str]) -> str:
    return f"yes={counter['yes']}, no={counter['no']}, uncertain={counter['uncertain']}"


def _format_counter(counter: Counter[str], *, top_n: int) -> str:
    if not counter:
        return "none"
    items = sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:top_n]
    return ", ".join(f"{key}={value}" for key, value in items)


def _judgment(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"yes", "y", "true", "1"}:
        return "yes"
    if text in {"no", "n", "false", "0"}:
        return "no"
    return "uncertain"


def _truthy_text(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return truthy(value)


def _float_or_none(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _question_sort_key(question: dict[str, Any]) -> tuple[int, str]:
    question_id = str(question.get("question_id", "")).strip()
    try:
        return (0, f"{int(question_id):020d}")
    except ValueError:
        return (1, question_id)
