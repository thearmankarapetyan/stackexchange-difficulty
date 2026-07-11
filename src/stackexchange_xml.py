"""Small shared helpers for reading Stack Exchange XML dump rows.

The public dump stores records as ``<row ... />`` elements.  The files can be
several gigabytes, so ``stream_rows`` reads one row at a time and clears it
before continuing.  The two thread-extraction commands use the remaining
helpers to apply the same validation and chronological ordering rules.
"""

from __future__ import annotations

import re
import tempfile
from contextlib import suppress
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Iterator, Sequence

from lxml import etree


XmlRow = dict[str, str]
QUESTION_POST_TYPE = "1"
ANSWER_POST_TYPE = "2"
STACK_DATETIME_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?"
)


def normalize_question_ids(question_ids: Sequence[str]) -> list[str]:
    """Validate question IDs and remove duplicates in the requested order."""
    normalized: dict[str, None] = {}
    for question_id in question_ids:
        value = str(question_id)
        if not value.isdecimal() or int(value) <= 0:
            raise ValueError(
                f"Question ID must be a positive decimal integer: {value!r}"
            )
        normalized[str(int(value))] = None
    if not normalized:
        raise ValueError("At least one question ID is required")
    return list(normalized)


def stream_rows(path: Path) -> Iterator[XmlRow]:
    """Yield copied row attributes while keeping memory use bounded."""
    context = etree.iterparse(str(path), events=("end",), tag="row", huge_tree=True)
    for _, element in context:
        try:
            yield dict(element.attrib)
        finally:
            parent = element.getparent()
            element.clear()
            if parent is not None:
                while element.getprevious() is not None:
                    del parent[0]


def describe_row(path: Path, row: XmlRow) -> str:
    """Identify a source row in a validation error."""
    identifiers = ", ".join(
        f"{name}={row[name]!r}"
        for name in ("Id", "ParentId", "PostId")
        if name in row
    )
    return f"{path.name} row ({identifiers or 'no identifier'})"


def positive_id(value: str | None, context: str, field: str = "Id") -> str:
    """Return a positive decimal identifier in its canonical form."""
    if value is None or not value.isdecimal() or int(value) <= 0:
        raise ValueError(f"{context}: {field} must be a positive decimal integer")
    return str(int(value))


def parse_stack_datetime(value: str | None, context: str, field: str) -> datetime:
    """Parse the timestamp format used by Stack Exchange dump rows."""
    if not value:
        raise ValueError(f"{context}: missing {field}")
    try:
        if STACK_DATETIME_PATTERN.fullmatch(value) is None:
            raise ValueError
        return datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(
            f"{context}: invalid {field} {value!r}; "
            "expected Stack Exchange format YYYY-MM-DDTHH:MM:SS[.fraction]"
        ) from None


def chronological_key(path: Path, row: XmlRow) -> tuple[datetime, Decimal, int]:
    """Sort by the exact creation time and then by the numeric row ID."""
    context = describe_row(path, row)
    row_id = positive_id(row.get("Id"), context)
    raw_date = row.get("CreationDate")
    parsed = parse_stack_datetime(raw_date, context, "CreationDate")
    _, point, digits = raw_date.partition(".")
    fraction = Decimal(f"0.{digits}") if point else Decimal(0)
    return parsed.replace(microsecond=0), fraction, int(row_id)


def read_posts(
    posts_path: Path, question_ids: Sequence[str]
) -> tuple[dict[str, XmlRow], dict[str, list[XmlRow]]]:
    """Read requested questions and every answer belonging to them."""
    requested = set(question_ids)
    questions: dict[str, XmlRow] = {}
    answers: dict[str, list[XmlRow]] = {}

    for row in stream_rows(posts_path):
        post_id = row.get("Id")
        parent_id = row.get("ParentId")
        if post_id in requested:
            questions[post_id] = row
        if row.get("PostTypeId") == ANSWER_POST_TYPE and parent_id in requested:
            answers.setdefault(parent_id, []).append(row)

    missing = [question_id for question_id in question_ids if question_id not in questions]
    if missing:
        raise ValueError(f"Question post ID(s) not found: {', '.join(missing)}")

    wrong_type = [
        question_id
        for question_id in question_ids
        if questions[question_id].get("PostTypeId") != QUESTION_POST_TYPE
    ]
    if wrong_type:
        raise ValueError(f"Post ID(s) are not questions: {', '.join(wrong_type)}")

    for question in questions.values():
        chronological_key(posts_path, question)
    for rows in answers.values():
        rows.sort(key=lambda row: chronological_key(posts_path, row))
    return questions, answers


def read_question_comments(
    comments_path: Path, question_ids: Sequence[str]
) -> dict[str, list[XmlRow]]:
    """Read comments attached directly to the requested questions."""
    requested = set(question_ids)
    comments: dict[str, list[XmlRow]] = {}
    for row in stream_rows(comments_path):
        question_id = row.get("PostId")
        if question_id in requested:
            comments.setdefault(question_id, []).append(row)
    for rows in comments.values():
        rows.sort(key=lambda row: chronological_key(comments_path, row))
    return comments


def source_paths(dump_dir: Path) -> tuple[Path, Path]:
    """Return verified Posts.xml and Comments.xml paths."""
    posts_path = Path(dump_dir) / "Posts.xml"
    comments_path = Path(dump_dir) / "Comments.xml"
    for path in (posts_path, comments_path):
        if not path.is_file():
            raise FileNotFoundError(f"{path.name} file not found: {path}")
    return posts_path, comments_path


def protect_source_files(output_path: Path, source_files: Sequence[Path]) -> None:
    """Prevent an output path from replacing an input dump file."""
    if Path(output_path).resolve() in {path.resolve() for path in source_files}:
        raise ValueError("Output path must not overwrite a source XML file")


def write_xml_safely(tree: etree._ElementTree, output_path: Path) -> None:
    """Publish a complete XML file and remove a temporary file after failures."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, dir=output_path.parent) as file:
            temporary_path = Path(file.name)
        tree.write(
            str(temporary_path),
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=True,
        )
        temporary_path.replace(output_path)
    finally:
        if temporary_path is not None:
            with suppress(OSError):
                temporary_path.unlink(missing_ok=True)
