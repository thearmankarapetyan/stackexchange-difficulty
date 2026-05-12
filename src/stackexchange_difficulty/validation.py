"""Validation checks for Stack Exchange-like corpus tables."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from stackexchange_difficulty.provenance import load_provenance
from stackexchange_difficulty.schema import (
    ANSWER_REQUIRED_COLUMNS,
    ARTIFICIAL_POST_IDS,
    COMMENT_REQUIRED_COLUMNS,
    PROVENANCE_IDENTIFIER_KEYS,
    PROVENANCE_REQUIRED_KEYS,
    QUESTION_REQUIRED_COLUMNS,
)


@dataclass(frozen=True)
class Table:
    name: str
    rows: list[dict[str, Any]]
    columns: tuple[str, ...]


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    row_id: str | None = None


@dataclass
class ValidationReport:
    ok: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    row_counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "issues": [issue.__dict__ for issue in self.issues],
            "row_counts": self.row_counts,
        }


def read_table(path: str | Path, name: str | None = None) -> Table:
    source = Path(path)
    table_name = name or source.stem
    suffix = source.suffix.lower()
    if suffix == ".jsonl":
        rows = [
            json.loads(line)
            for line in source.read_text(encoding="utf-8").splitlines()
            if line
        ]
    elif suffix == ".json":
        loaded = json.loads(source.read_text(encoding="utf-8"))
        rows = loaded if isinstance(loaded, list) else loaded.get("rows", [])
    else:
        delimiter = "\t" if suffix in {".tsv", ".tab"} else ","
        with source.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter=delimiter))
    columns = tuple(rows[0].keys()) if rows else ()
    return Table(name=table_name, rows=rows, columns=columns)


def write_validation_report(report: ValidationReport, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")


def validate_dataset(
    questions: Table,
    answers: Table | None = None,
    comments: Table | None = None,
    provenance: dict[str, Any] | None = None,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    row_counts = {
        "questions": len(questions.rows),
        "answers": len(answers.rows) if answers else 0,
        "comments": len(comments.rows) if comments else 0,
    }

    issues.extend(validate_required_columns(questions, QUESTION_REQUIRED_COLUMNS))
    if answers is not None:
        issues.extend(validate_required_columns(answers, ANSWER_REQUIRED_COLUMNS))
    if comments is not None:
        issues.extend(validate_required_columns(comments, COMMENT_REQUIRED_COLUMNS))

    if not issues:
        issues.extend(validate_question_ids(questions))
        issues.extend(validate_artificial_post_exclusion(questions))
        if answers is not None:
            issues.extend(validate_answer_links(questions, answers))
            issues.extend(validate_accepted_answers(questions, answers))
        if provenance is not None:
            issues.extend(validate_provenance_record(provenance))

    return ValidationReport(ok=not issues, issues=issues, row_counts=row_counts)


def validate_required_columns(
    table: Table,
    required_columns: tuple[str, ...],
) -> list[ValidationIssue]:
    missing = [column for column in required_columns if column not in table.columns]
    if not missing:
        return []
    return [
        ValidationIssue(
            code="missing_required_columns",
            message=f"{table.name} is missing required columns: {', '.join(missing)}",
        )
    ]


def validate_question_ids(questions: Table) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    seen: set[str] = set()
    for row in questions.rows:
        question_id = str(row.get("question_id", "")).strip()
        if not question_id:
            issues.append(
                ValidationIssue("missing_question_id", "Question row has no question_id.")
            )
        elif question_id in seen:
            issues.append(
                ValidationIssue(
                    "duplicate_question_id",
                    f"Duplicate question_id: {question_id}",
                    row_id=question_id,
                )
            )
        seen.add(question_id)
    return issues


def validate_artificial_post_exclusion(questions: Table) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for row in questions.rows:
        question_id = str(row.get("question_id", "")).strip()
        if question_id in ARTIFICIAL_POST_IDS:
            issues.append(
                ValidationIssue(
                    "artificial_post_id",
                    f"Artificial Data Dump post ID must be excluded: {question_id}",
                    row_id=question_id,
                )
            )
    return issues


def validate_answer_links(questions: Table, answers: Table) -> list[ValidationIssue]:
    question_ids = {str(row["question_id"]).strip() for row in questions.rows}
    issues: list[ValidationIssue] = []
    for row in answers.rows:
        answer_id = str(row.get("answer_id", "")).strip()
        question_id = str(row.get("question_id", "")).strip()
        if question_id not in question_ids:
            issues.append(
                ValidationIssue(
                    "answer_parent_missing",
                    f"Answer {answer_id} points to missing question_id {question_id}.",
                    row_id=answer_id,
                )
            )
    return issues


def validate_accepted_answers(questions: Table, answers: Table) -> list[ValidationIssue]:
    answer_by_id = {str(row["answer_id"]).strip(): row for row in answers.rows}
    issues: list[ValidationIssue] = []
    for row in questions.rows:
        accepted_answer_id = str(row.get("accepted_answer_id", "")).strip()
        if not accepted_answer_id:
            continue
        question_id = str(row["question_id"]).strip()
        answer = answer_by_id.get(accepted_answer_id)
        if answer is None:
            issues.append(
                ValidationIssue(
                    "accepted_answer_missing",
                    f"Question {question_id} accepted_answer_id {accepted_answer_id} is absent.",
                    row_id=question_id,
                )
            )
            continue
        if str(answer.get("question_id", "")).strip() != question_id:
            issues.append(
                ValidationIssue(
                    "accepted_answer_parent_mismatch",
                    (
                        f"Accepted answer {accepted_answer_id} does not belong "
                        f"to question {question_id}."
                    ),
                    row_id=question_id,
                )
            )
        if "is_accepted" in answer and not truthy(answer.get("is_accepted")):
            issues.append(
                ValidationIssue(
                    "accepted_answer_flag_mismatch",
                    f"Accepted answer {accepted_answer_id} is not marked is_accepted.",
                    row_id=question_id,
                )
            )
    return issues


def validate_provenance_file(path: str | Path) -> list[ValidationIssue]:
    return validate_provenance_record(load_provenance(path))


def validate_provenance_record(record: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for key in PROVENANCE_REQUIRED_KEYS:
        if _is_blank(record.get(key)):
            issues.append(
                ValidationIssue(
                    "provenance_missing_required_key",
                    f"Provenance record is missing required key: {key}",
                )
            )
    if not any(not _is_blank(record.get(key)) for key in PROVENANCE_IDENTIFIER_KEYS):
        issues.append(
            ValidationIssue(
                "provenance_missing_source_identifier",
                "Provenance record needs a source version, query, dump file, or export identifier.",
            )
        )
    return issues


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y"}


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, tuple, dict, set)):
        return len(value) == 0
    return str(value).strip() == ""
