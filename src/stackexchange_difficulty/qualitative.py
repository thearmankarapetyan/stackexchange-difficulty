"""Content-safe qualitative sampling and aggregate memo helpers."""

from __future__ import annotations

import csv
import json
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from stackexchange_difficulty.validation import Table

QUALITATIVE_REVIEW_COLUMNS = (
    "record_index",
    "sample_group",
    "question_id",
    "creation_date",
    "tags",
    "score",
    "view_count",
    "answer_count",
    "comment_count",
    "accepted_answer_id",
    "indicator_time_to_first_answer_hours",
    "indicator_tag_popularity_bucket",
    "indicator_question_length",
    "indicator_code_block_count",
    "indicator_contains_error_message",
    "title",
    "body_html",
    "answers_for_review",
    "comments_for_review",
)

QUALITATIVE_CODE_COLUMNS = (
    "record_index",
    "sample_group",
    "qualitative_difficulty",
    "answerability_clarity",
    "source_of_difficulty",
    "answer_type",
    "interaction_role",
    "notation_or_formulation_issue",
    "comments_needed",
    "corpus_design_implication",
    "analytic_note",
)

SAMPLE_GROUPS = (
    "clear_direct",
    "ordinary_intermediate",
    "high_effort_or_ambiguous",
)

CONTROLLED_VALUES = {
    "qualitative_difficulty": {"low", "medium", "high", "uncertain"},
    "answerability_clarity": {"clear", "partially_clear", "unclear"},
    "source_of_difficulty": {
        "conceptual",
        "computational",
        "proof_based",
        "notation_or_formulation",
        "missing_context",
        "domain_specific",
        "multi_step_reasoning",
        "other",
    },
    "answer_type": {
        "direct_solution",
        "explanation",
        "proof",
        "correction",
        "partial_answer",
        "other",
    },
    "interaction_role": {
        "no_comments_needed",
        "comments_clarify_question",
        "comments_correct_answer",
        "comments_reveal_missing_context",
        "comments_not_available_or_not_needed",
    },
    "notation_or_formulation_issue": {"none", "minor", "significant"},
    "comments_needed": {"yes", "no", "uncertain"},
    "corpus_design_implication": {
        "keep_main_clean_corpus",
        "add_diagnostic_subset",
        "include_comments",
        "revise_sampling",
        "other",
    },
}

UNSAFE_NOTE_PATTERN = re.compile(
    r"(https?://|www\.|<[^>]+>|@|question_id|answer_id|comment_id|body_html|"
    r"HF_TOKEN|hf_[A-Za-z0-9]{20,})",
    re.IGNORECASE,
)

UNSAFE_MEMO_PATTERN = re.compile(
    r"(question_id|body_html|answers_for_review|comments_for_review|https?://|www\.|"
    r"<[^>]+>|HF_TOKEN|hf_[A-Za-z0-9]{20,}|Sensitive qualitative)",
    re.IGNORECASE,
)


class QualitativeError(RuntimeError):
    """Raised when qualitative sampling or summary cannot continue safely."""


@dataclass(frozen=True)
class QualitativePrepareResult:
    review_path: Path
    codes_path: Path
    readme_path: Path
    manifest_path: Path
    selected_records: int
    date_from: str
    date_to: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "ok": True,
            "review": str(self.review_path),
            "codes": str(self.codes_path),
            "readme": str(self.readme_path),
            "manifest": str(self.manifest_path),
            "selected_records": self.selected_records,
            "date_from": self.date_from,
            "date_to": self.date_to,
        }


@dataclass(frozen=True)
class QualitativeSummaryResult:
    output_path: Path
    coded_records: int
    unsafe_content_markers: int

    def to_payload(self) -> dict[str, Any]:
        return {
            "ok": True,
            "output": str(self.output_path),
            "coded_records": self.coded_records,
            "unsafe_content_markers": self.unsafe_content_markers,
        }


def prepare_qualitative_sample(
    *,
    questions: Table,
    answers: Table,
    comments: Table,
    indicators: Table,
    site_slug: str,
    source_slug: str,
    date_from: str,
    date_to: str,
    sample_size: int,
    out_dir: Path,
    seed: int = 20260518,
) -> QualitativePrepareResult:
    if sample_size <= 0:
        raise QualitativeError("sample size must be positive")
    _require_ignored_processed_out_dir(out_dir)
    _require_columns(questions, ("question_id", "creation_date", "title", "body_html"))
    _require_columns(answers, ("answer_id", "question_id", "body_html"))
    _require_columns(comments, ("comment_id", "post_id", "text"))
    _require_columns(
        indicators,
        (
            "question_id",
            "time_to_first_answer_hours",
            "tag_popularity_bucket",
            "question_length",
            "code_block_count",
            "contains_error_message",
        ),
    )
    start = _parse_date(date_from)
    end = _parse_date(date_to)
    if start > end:
        raise QualitativeError("date-from must be on or before date-to")

    merged = _recent_records(questions, answers, comments, indicators, start=start, end=end)
    if len(merged) < sample_size:
        raise QualitativeError(
            f"recent slice has fewer than requested sample size: {len(merged)} < {sample_size}"
        )

    selected, candidate_counts = _select_grouped_sample(merged, sample_size=sample_size, seed=seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    review_path = out_dir / "qualitative_review.tsv"
    codes_path = out_dir / "qualitative_codes.tsv"
    readme_path = out_dir / "README.md"
    manifest_path = out_dir / "sample_manifest.json"

    _write_review(review_path, selected)
    _write_codes_template(codes_path, selected)
    manifest = {
        "site_slug": site_slug,
        "source_slug": source_slug,
        "date_from": date_from,
        "date_to": date_to,
        "sample_size": sample_size,
        "seed": seed,
        "recent_candidate_count": len(merged),
        "selected_records": len(selected),
        "candidate_group_counts": candidate_counts,
        "sample_group_counts": dict(Counter(row["sample_group"] for row in selected)),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    readme_path.write_text(
        "\n".join(
            [
                "# Local Recent Qualitative Sample",
                "",
                "This directory is ignored by Git because review files may contain real "
                "Stack Exchange post content.",
                "",
                "Use controlled values in qualitative_codes.tsv. Keep analytic notes blank "
                "or paraphrased, and do not copy record text, formulas, links, handles, or IDs.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return QualitativePrepareResult(
        review_path=review_path,
        codes_path=codes_path,
        readme_path=readme_path,
        manifest_path=manifest_path,
        selected_records=len(selected),
        date_from=date_from,
        date_to=date_to,
    )


def summarize_qualitative_coding(
    *,
    codes: Table,
    manifest_path: Path,
    output_path: Path,
    labeler: str,
    sample_size: int | None = None,
) -> QualitativeSummaryResult:
    _require_columns(codes, QUALITATIVE_CODE_COLUMNS)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = sample_size or int(manifest.get("selected_records", 30))
    rows = _validated_code_rows(codes)
    if len(rows) != expected:
        raise QualitativeError(f"expected {expected} coded records, got {len(rows)}")
    markdown = _qualitative_memo(rows=rows, manifest=manifest, labeler=labeler)
    unsafe_markers = len(UNSAFE_MEMO_PATTERN.findall(markdown))
    if unsafe_markers:
        raise QualitativeError("qualitative memo contains unsafe row-level content markers")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    return QualitativeSummaryResult(
        output_path=output_path,
        coded_records=len(rows),
        unsafe_content_markers=unsafe_markers,
    )


def _require_ignored_processed_out_dir(out_dir: Path) -> None:
    parts = out_dir.parts
    required = ("data", "processed", "stackexchange-difficulty")
    for index in range(len(parts) - len(required) + 1):
        if parts[index : index + len(required)] == required:
            return
    raise QualitativeError(
        "qualitative out-dir must be under data/processed/stackexchange-difficulty"
    )


def _require_columns(table: Table, columns: tuple[str, ...]) -> None:
    missing = [column for column in columns if column not in table.columns]
    if missing:
        raise QualitativeError(f"{table.name} is missing required columns: {', '.join(missing)}")


def _recent_records(
    questions: Table,
    answers: Table,
    comments: Table,
    indicators: Table,
    *,
    start: datetime,
    end: datetime,
) -> list[dict[str, Any]]:
    answers_by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for answer in answers.rows:
        answers_by_question[str(answer.get("question_id", "")).strip()].append(answer)
    comments_by_post: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for comment in comments.rows:
        comments_by_post[str(comment.get("post_id", "")).strip()].append(comment)
    indicators_by_question = {
        str(row.get("question_id", "")).strip(): row for row in indicators.rows
    }

    records: list[dict[str, Any]] = []
    for question in questions.rows:
        created = _parse_datetime(question.get("creation_date"))
        if created is None or not (start <= created <= end):
            continue
        question_id = str(question.get("question_id", "")).strip()
        question_answers = sorted(
            answers_by_question.get(question_id, []),
            key=lambda row: str(row.get("creation_date", "")),
        )
        answer_ids = {str(row.get("answer_id", "")).strip() for row in question_answers}
        selected_comments = []
        for post_id in {question_id, *answer_ids}:
            selected_comments.extend(comments_by_post.get(post_id, []))
        selected_comments.sort(key=lambda row: str(row.get("creation_date", "")))
        records.append(
            {
                "question": question,
                "answers": question_answers,
                "comments": selected_comments,
                "indicators": indicators_by_question.get(question_id, {}),
            }
        )
    return sorted(records, key=lambda row: _int_or_text(row["question"].get("question_id")))


def _select_grouped_sample(
    records: list[dict[str, Any]],
    *,
    sample_size: int,
    seed: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    q3_length = _third_quartile(
        [_float_or_none(record["indicators"].get("question_length")) for record in records]
    )
    pools = {group: [] for group in SAMPLE_GROUPS}
    for record in records:
        for group in _matching_groups(record, q3_length=q3_length):
            pools[group].append(record)
    candidate_counts = {group: len(rows) for group, rows in pools.items()}
    targets = _group_targets(sample_size)
    rng = random.Random(seed)
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    for group in SAMPLE_GROUPS:
        selected.extend(
            _take_from_pool(
                pools[group],
                group=group,
                count=targets[group],
                rng=rng,
                selected_ids=selected_ids,
            )
        )

    while len(selected) < sample_size:
        made_progress = False
        for group in SAMPLE_GROUPS:
            if len(selected) >= sample_size:
                break
            taken = _take_from_pool(
                pools[group],
                group=group,
                count=1,
                rng=rng,
                selected_ids=selected_ids,
            )
            if taken:
                selected.extend(taken)
                made_progress = True
        if not made_progress:
            break
    if len(selected) != sample_size:
        raise QualitativeError(f"could not select requested qualitative sample: {len(selected)}")
    return _with_record_indexes(selected), candidate_counts


def _group_targets(sample_size: int) -> dict[str, int]:
    base = sample_size // len(SAMPLE_GROUPS)
    remainder = sample_size % len(SAMPLE_GROUPS)
    return {
        group: base + (1 if index < remainder else 0)
        for index, group in enumerate(SAMPLE_GROUPS)
    }


def _take_from_pool(
    pool: list[dict[str, Any]],
    *,
    group: str,
    count: int,
    rng: random.Random,
    selected_ids: set[str],
) -> list[dict[str, Any]]:
    candidates = list(pool)
    rng.shuffle(candidates)
    taken = []
    for candidate in candidates:
        question_id = str(candidate["question"].get("question_id", "")).strip()
        if question_id in selected_ids:
            continue
        selected_ids.add(question_id)
        taken.append({**candidate, "sample_group": group})
        if len(taken) >= count:
            break
    return taken


def _matching_groups(record: dict[str, Any], *, q3_length: float) -> list[str]:
    question = record["question"]
    indicator = record["indicators"]
    latency = _float_or_none(indicator.get("time_to_first_answer_hours"))
    comment_count = _int_or_none(question.get("comment_count")) or 0
    answer_count = _int_or_none(question.get("answer_count")) or 0
    question_length = _float_or_none(indicator.get("question_length")) or 0
    contains_error = _truthy_text(indicator.get("contains_error_message"))
    groups = []
    if (
        latency is not None
        and latency < 1
        and comment_count <= 2
        and answer_count <= 2
        and not contains_error
    ):
        groups.append("clear_direct")
    if latency is not None and 1 <= latency < 24 and answer_count >= 1 and comment_count <= 6:
        groups.append("ordinary_intermediate")
    if (
        (latency is not None and latency >= 24)
        or comment_count >= 7
        or answer_count >= 3
        or question_length >= q3_length
    ):
        groups.append("high_effort_or_ambiguous")
    return groups or ["ordinary_intermediate"]


def _with_record_indexes(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**record, "record_index": str(index)} for index, record in enumerate(records, 1)]


def _write_review(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUALITATIVE_REVIEW_COLUMNS, delimiter="\t")
        writer.writeheader()
        for record in records:
            question = record["question"]
            indicator = record["indicators"]
            writer.writerow(
                {
                    "record_index": record["record_index"],
                    "sample_group": record["sample_group"],
                    "question_id": question.get("question_id", ""),
                    "creation_date": question.get("creation_date", ""),
                    "tags": question.get("tags", ""),
                    "score": question.get("score", ""),
                    "view_count": question.get("view_count", ""),
                    "answer_count": question.get("answer_count", ""),
                    "comment_count": question.get("comment_count", ""),
                    "accepted_answer_id": question.get("accepted_answer_id", ""),
                    "indicator_time_to_first_answer_hours": indicator.get(
                        "time_to_first_answer_hours", ""
                    ),
                    "indicator_tag_popularity_bucket": indicator.get(
                        "tag_popularity_bucket", ""
                    ),
                    "indicator_question_length": indicator.get("question_length", ""),
                    "indicator_code_block_count": indicator.get("code_block_count", ""),
                    "indicator_contains_error_message": indicator.get(
                        "contains_error_message", ""
                    ),
                    "title": question.get("title", ""),
                    "body_html": question.get("body_html", ""),
                    "answers_for_review": _answers_for_review(record["answers"]),
                    "comments_for_review": _comments_for_review(record["comments"]),
                }
            )


def _write_codes_template(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUALITATIVE_CODE_COLUMNS, delimiter="\t")
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "record_index": record["record_index"],
                    "sample_group": record["sample_group"],
                    "qualitative_difficulty": "",
                    "answerability_clarity": "",
                    "source_of_difficulty": "",
                    "answer_type": "",
                    "interaction_role": "",
                    "notation_or_formulation_issue": "",
                    "comments_needed": "",
                    "corpus_design_implication": "",
                    "analytic_note": "",
                }
            )


def _answers_for_review(answers: list[dict[str, Any]]) -> str:
    return "\n\n--- answer ---\n\n".join(
        "\n".join(
            [
                f"answer_id={answer.get('answer_id', '')}",
                f"is_accepted={answer.get('is_accepted', '')}",
                f"score={answer.get('score', '')}",
                f"creation_date={answer.get('creation_date', '')}",
                str(answer.get("body_html", "")),
            ]
        )
        for answer in answers
    )


def _comments_for_review(comments: list[dict[str, Any]]) -> str:
    return "\n\n--- comment ---\n\n".join(
        "\n".join(
            [
                f"comment_id={comment.get('comment_id', '')}",
                f"post_id={comment.get('post_id', '')}",
                f"score={comment.get('score', '')}",
                f"creation_date={comment.get('creation_date', '')}",
                str(comment.get("text", "")),
            ]
        )
        for comment in comments
    )


def _validated_code_rows(codes: Table) -> list[dict[str, Any]]:
    seen: set[str] = set()
    rows = []
    for row in codes.rows:
        record_index = str(row.get("record_index", "")).strip()
        if not record_index:
            raise QualitativeError("code row has blank record_index")
        if record_index in seen:
            raise QualitativeError(f"duplicate record_index: {record_index}")
        seen.add(record_index)
        sample_group = str(row.get("sample_group", "")).strip()
        if sample_group not in SAMPLE_GROUPS:
            raise QualitativeError(f"invalid sample_group={sample_group!r}")
        normalized = {"record_index": record_index, "sample_group": sample_group}
        for column, allowed in CONTROLLED_VALUES.items():
            value = str(row.get(column, "")).strip()
            if value not in allowed:
                raise QualitativeError(f"invalid {column}={value!r}")
            normalized[column] = value
        note = str(row.get("analytic_note", "")).strip()
        if UNSAFE_NOTE_PATTERN.search(note):
            raise QualitativeError(f"unsafe analytic_note for record_index={record_index}")
        normalized["analytic_note"] = note
        rows.append(normalized)
    return rows


def _qualitative_memo(
    *,
    rows: list[dict[str, Any]],
    manifest: dict[str, Any],
    labeler: str,
) -> str:
    counters = {column: Counter(row[column] for row in rows) for column in CONTROLLED_VALUES}
    sample_groups = Counter(row["sample_group"] for row in rows)
    return "\n".join(
        [
            "# Qualitative Analysis Of Recent Mathematics Threads - 2026-05-18",
            "",
            "## Objective",
            "",
            "This memo summarizes a qualitative slice requested by the supervisor: "
            "recent Mathematics exchanges that began between May 2025 and April 2026.",
            "",
            "## Source And Sample",
            "",
            f"- Site slug: `{manifest.get('site_slug', '')}`.",
            f"- Source slug: `{manifest.get('source_slug', '')}`.",
            f"- Date range: `{manifest.get('date_from', '')}` to `{manifest.get('date_to', '')}`.",
            f"- Coded records: {len(rows)}.",
            f"- Sample groups: {_format_counter(sample_groups)}.",
            "",
            "## Coding Method",
            "",
            f"- Labeling method: {labeler}.",
            "- Coding used controlled categories for difficulty, answerability, "
            "difficulty source, response type, interaction role, notation/formulation, "
            "comment need, and corpus-design implication.",
            "",
            "## Aggregate Coding Results",
            "",
            *[
                f"- {column}: {_format_counter(counters[column])}."
                for column in CONTROLLED_VALUES
            ],
            "",
            "## Observed Qualitative Patterns",
            "",
            "- Clear recent cases tend to remain usable when the problem object and "
            "requested result are explicit.",
            "- Higher-effort cases are mainly useful as diagnostic material when they "
            "show missing context, multi-step reasoning, or formulation uncertainty.",
            "- The clean sample remains suitable as the main answerable corpus layer, "
            "while a smaller diagnostic layer can preserve more ambiguous cases.",
            "",
            "## Difficulty And Answerability Signals",
            "",
            "- The qualitative coding supports using latency, interaction volume, and "
            "question length as descriptive indicators rather than final difficulty labels.",
            "- Accepted-answer presence is useful for answerability, but qualitative review "
            "is still needed before treating it as a correctness signal.",
            "",
            "## Role Of Comments And Interaction",
            "",
            "- Comments are most useful when they clarify assumptions, expose missing "
            "context, or reveal correction work.",
            "- Most clean-profile records do not require comments for basic answerability "
            "judgment, but comments remain useful for diagnostic subsets.",
            "",
            "## Implications For Corpus Design",
            "",
            "- Keep `answerable_clean` as the default main corpus profile for Mathematics.",
            "- Add a separate diagnostic qualitative subset for ambiguous, context-dependent, "
            "or high-effort cases.",
            "- Treat derived indicators as interpretive controls before using them as "
            "difficulty labels.",
            "",
            "## Discussion Points For Supervisor Meeting",
            "",
            "- Confirm Mathematics as the first validated site or redirect toward a "
            "code-centric Stack Exchange site.",
            "- Decide whether the main corpus and diagnostic subset should be separated.",
            "- Decide when comments should become part of the default analysis layer.",
            "- Decide whether future labels should target difficulty, answerability, or both.",
            "",
            "## Content Safety",
            "",
            "- This memo contains aggregate counts and paraphrased methodological patterns "
            "only. It excludes row-level identifiers, original post content, copied "
            "mathematical expressions, links, user handles, local review files, and "
            "local coding files.",
            "",
        ]
    )


def _format_counter(counter: Counter[str]) -> str:
    if not counter:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(counter.items()))


def _parse_date(value: str) -> datetime:
    parsed = _parse_datetime(value)
    if parsed is None:
        raise QualitativeError(f"invalid date: {value}")
    return parsed


def _parse_datetime(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).replace(tzinfo=None)
    except ValueError:
        try:
            return datetime.strptime(text[:10], "%Y-%m-%d")
        except ValueError:
            return None


def _float_or_none(value: Any) -> float | None:
    try:
        text = str(value).strip()
        return float(text) if text else None
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    try:
        text = str(value).strip()
        return int(float(text)) if text else None
    except (TypeError, ValueError):
        return None


def _int_or_text(value: Any) -> tuple[int, str]:
    text = str(value or "").strip()
    try:
        return (int(text), text)
    except ValueError:
        return (0, text)


def _truthy_text(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _third_quartile(values: list[float | None]) -> float:
    present = sorted(value for value in values if value is not None)
    if not present:
        return 0
    index = int(0.75 * (len(present) - 1))
    return present[index]
