"""Aggregate-only diagnostics for local inspection labels."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from stackexchange_difficulty.inspection import (
    LABEL_COLUMNS,
    REASON_CODE_PATTERN,
    REVIEW_COLUMNS,
)
from stackexchange_difficulty.validation import Table

JUDGMENT_COLUMNS = (
    "suitable",
    "answerability_clear",
    "math_notation_readable",
    "needs_comments",
)
JUDGMENT_VALUES = {"yes", "no", "uncertain"}
ALLOWED_NOTES = {
    "",
    "generic_missing_context",
    "generic_notation_issue",
    "generic_answerability_unclear",
    "generic_unsuitable",
    "generic_other",
}
UNSAFE_OUTPUT_PATTERN = re.compile(
    r"(question_id|body_html|answers_for_review|https?://|www\.|<p>|</p>|<code>|</code>|"
    r"Sensitive diagnostic|HF_TOKEN|hf_[A-Za-z0-9]{20,})"
)


class InspectionDiagnosticsError(RuntimeError):
    """Raised when aggregate inspection diagnostics cannot be generated safely."""


@dataclass(frozen=True)
class InspectionDiagnosticsResult:
    output_path: Path
    inspected: int
    unsafe_content_markers: int

    def to_payload(self) -> dict[str, Any]:
        return {
            "ok": True,
            "output": str(self.output_path),
            "inspected": self.inspected,
            "unsafe_content_markers": self.unsafe_content_markers,
        }


def diagnose_inspection_strata(
    *,
    review: Table,
    labels: Table,
    output_path: Path,
) -> InspectionDiagnosticsResult:
    _require_columns(review, REVIEW_COLUMNS)
    _require_columns(labels, LABEL_COLUMNS)
    review_by_index = _review_by_index(review)
    joined = _validated_joined_rows(review_by_index, labels)
    markdown = _diagnostic_markdown(joined)
    unsafe_markers = len(UNSAFE_OUTPUT_PATTERN.findall(markdown))
    if unsafe_markers:
        raise InspectionDiagnosticsError(
            "diagnostic output contains unsafe row-level content markers"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    return InspectionDiagnosticsResult(
        output_path=output_path,
        inspected=len(joined),
        unsafe_content_markers=unsafe_markers,
    )


def _require_columns(table: Table, required: tuple[str, ...]) -> None:
    missing = [column for column in required if column not in table.columns]
    if missing:
        raise InspectionDiagnosticsError(
            f"{table.name} is missing required columns: {', '.join(missing)}"
        )


def _review_by_index(review: Table) -> dict[str, dict[str, Any]]:
    by_index: dict[str, dict[str, Any]] = {}
    for row in review.rows:
        record_index = str(row.get("record_index", "")).strip()
        if not record_index:
            raise InspectionDiagnosticsError("review row has blank record_index")
        if record_index in by_index:
            raise InspectionDiagnosticsError(f"duplicate review record_index: {record_index}")
        by_index[record_index] = row
    return by_index


def _validated_joined_rows(
    review_by_index: dict[str, dict[str, Any]],
    labels: Table,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for label in labels.rows:
        record_index = str(label.get("record_index", "")).strip()
        if not record_index:
            raise InspectionDiagnosticsError("label row has blank record_index")
        if record_index in seen:
            raise InspectionDiagnosticsError(f"duplicate record_index in labels: {record_index}")
        seen.add(record_index)
        review = review_by_index.get(record_index)
        if review is None:
            raise InspectionDiagnosticsError(
                f"label record_index {record_index} does not match any review row"
            )
        for column in JUDGMENT_COLUMNS:
            value = _judgment(label.get(column))
            if value not in JUDGMENT_VALUES:
                raise InspectionDiagnosticsError(
                    f"invalid {column}={label.get(column)!r} for record_index={record_index}"
                )
            label[column] = value
        reason = str(label.get("reason_code", "")).strip().lower()
        if not reason or not REASON_CODE_PATTERN.fullmatch(reason):
            raise InspectionDiagnosticsError(
                f"invalid reason_code={reason!r} for record_index={record_index}"
            )
        note = str(label.get("notes", "")).strip()
        if note not in ALLOWED_NOTES:
            raise InspectionDiagnosticsError(
                f"non-generic note for record_index={record_index}: {note!r}"
            )
        rows.append({"review": review, "label": {**label, "reason_code": reason, "notes": note}})
    return rows


def _diagnostic_markdown(rows: list[dict[str, Any]]) -> str:
    labels = [row["label"] for row in rows]
    reviews = [row["review"] for row in rows]
    suitable = Counter(row["suitable"] for row in labels)
    answerability = Counter(row["answerability_clear"] for row in labels)
    notation = Counter(row["math_notation_readable"] for row in labels)
    needs_comments = Counter(row["needs_comments"] for row in labels)
    reasons = Counter(row["reason_code"] for row in labels)
    sample_strata = Counter(str(row.get("sample_stratum", "")).strip() for row in labels)
    recommendation = _recommendation(
        suitable=suitable,
        answerability=answerability,
        notation=notation,
        needs_comments=needs_comments,
    )

    return "\n".join(
        [
            "# Target-Scale Inspection Diagnostics",
            "",
            "## Source",
            "",
            f"- Inspected records: {len(rows)}.",
            "- Inputs were local ignored inspection files; this report contains aggregates only.",
            "",
            "## Label Summary",
            "",
            f"- Suitable records: {_judgment_counter(suitable)}.",
            f"- Answerability clear: {_judgment_counter(answerability)}.",
            f"- Math notation readable: {_judgment_counter(notation)}.",
            f"- Needs comments: {_judgment_counter(needs_comments)}.",
            f"- Reason codes: {_format_counter(reasons, top_n=25)}.",
            "",
            "## Suitability By Stratum",
            "",
            *_stratum_lines(labels, "suitable"),
            "",
            "## Answerability By Stratum",
            "",
            *_stratum_lines(labels, "answerability_clear"),
            "",
            "## Reason Codes By Stratum",
            "",
            *_reason_by_stratum_lines(labels),
            "",
            "## Metadata Buckets",
            "",
            f"- Sample strata: {_format_counter(sample_strata, top_n=25)}.",
            f"- score_bucket: {_format_counter(Counter(_score_bucket(row) for row in reviews))}.",
            f"- view_bucket: {_format_counter(Counter(_view_bucket(row) for row in reviews))}.",
            "- comment_count_bucket: "
            f"{_format_counter(Counter(_comment_count_bucket(row) for row in reviews))}.",
            "- latency_bucket: "
            f"{_format_counter(Counter(_latency_bucket(row) for row in reviews))}.",
            "- tag_popularity_bucket: "
            f"{_format_counter(Counter(_tag_bucket(row) for row in reviews))}.",
            "- has_question_comments: "
            f"{_format_counter(Counter(_has_question_comments(row) for row in reviews))}.",
            "",
            "## Clean Sampling Recommendation",
            "",
            f"- Recommendation: {recommendation}.",
            "",
            "## Content Safety",
            "",
            "- This diagnostic contains aggregate counts only. It does not include "
            "individual row identifiers, row-level text fields, formulas, links, user "
            "handles, label notes, or copied Stack Exchange post content.",
            "",
        ]
    )


def _stratum_lines(labels: list[dict[str, Any]], column: str) -> list[str]:
    by_stratum: dict[str, Counter[str]] = defaultdict(Counter)
    for row in labels:
        by_stratum[str(row.get("sample_stratum", "")).strip()][str(row.get(column, ""))] += 1
    if not by_stratum:
        return ["- none."]
    return [
        f"- {stratum}: {_judgment_counter(counter)}."
        for stratum, counter in sorted(by_stratum.items())
    ]


def _reason_by_stratum_lines(labels: list[dict[str, Any]]) -> list[str]:
    by_stratum: dict[str, Counter[str]] = defaultdict(Counter)
    for row in labels:
        by_stratum[str(row.get("sample_stratum", "")).strip()][
            str(row.get("reason_code", ""))
        ] += 1
    if not by_stratum:
        return ["- none."]
    return [
        f"- {stratum}: {_format_counter(counter, top_n=10)}."
        for stratum, counter in sorted(by_stratum.items())
    ]


def _recommendation(
    *,
    suitable: Counter[str],
    answerability: Counter[str],
    notation: Counter[str],
    needs_comments: Counter[str],
) -> str:
    if suitable["yes"] < 80 or answerability["yes"] < 80:
        return "Recommend using sample_profile=answerable_clean for the next target-scale run"
    if needs_comments["yes"] > 10:
        return "Recommend comment enrichment before sampling changes"
    if notation["yes"] < 95:
        return "Recommend notation-specific review before scaling"
    return "Recommend keeping current sampling"


def _judgment(value: Any) -> str:
    return str(value or "").strip().lower()


def _judgment_counter(counter: Counter[str]) -> str:
    return ", ".join(f"{key}={counter[key]}" for key in ("yes", "no", "uncertain"))


def _format_counter(counter: Counter[str], *, top_n: int | None = None) -> str:
    if not counter:
        return "none"
    items = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    if top_n is not None and len(items) > top_n:
        top = items[:top_n]
        other = sum(value for _key, value in items[top_n:])
        items = [*top, ("other", other)]
    return ", ".join(f"{key}={value}" for key, value in items)


def _score_bucket(row: dict[str, Any]) -> str:
    score = _int(row.get("score"))
    if score < 0:
        return "negative"
    if score < 3:
        return "low"
    if score < 10:
        return "medium"
    return "high"


def _view_bucket(row: dict[str, Any]) -> str:
    views = _int(row.get("view_count"))
    if views < 500:
        return "low"
    if views < 5000:
        return "medium"
    return "high"


def _comment_count_bucket(row: dict[str, Any]) -> str:
    count = _int(row.get("comment_count"))
    if count == 0:
        return "none"
    if count < 4:
        return "low"
    return "high"


def _latency_bucket(row: dict[str, Any]) -> str:
    value = _float_or_none(row.get("indicator_time_to_first_answer_hours"))
    if value is None:
        return "no_timing"
    if value < 1:
        return "under_1h"
    if value < 24:
        return "under_24h"
    if value < 168:
        return "under_7d"
    return "over_7d"


def _tag_bucket(row: dict[str, Any]) -> str:
    value = str(row.get("indicator_tag_popularity_bucket", "") or "none").strip().lower()
    return value or "none"


def _has_question_comments(row: dict[str, Any]) -> str:
    return "true" if _int(row.get("comment_count")) > 0 else "false"


def _int(value: Any) -> int:
    try:
        return int(str(value or "0").strip())
    except ValueError:
        return 0


def _float_or_none(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None
