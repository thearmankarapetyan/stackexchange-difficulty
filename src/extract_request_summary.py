"""Extract a configurable question summary from Stack Exchange dump files.

The default field selection reproduces the twelve-field XML requested for the
project.  A TSV field file can select or reorder supported fields without a
source-code change.  Each output ``request`` represents one question.

Example:
    python src/extract_request_summary.py --dump-dir /path/to/site-dump \
        --output data/examples/request-summary.xml 123 456

Requires Python 3.10 or newer and ``lxml``.  Source dump and field-selection
files remain unchanged, and the destination XML is published atomically.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Sequence

from lxml import etree

from stackexchange_xml import (
    normalize_question_ids,
    protect_source_files,
    read_posts,
    read_question_comments,
    source_paths,
    write_xml_safely,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_FIELDS_FILE = PROJECT_DIR / "config" / "summary_fields.tsv"

# Each supported output field copies one attribute from a selected source row.
# The first and accepted rows are chosen before these simple lookups are made.
FIELD_SOURCES = {
    "question_id": ("question", "Id"),
    "question_title": ("question", "Title"),
    "question_body": ("question", "Body"),
    "question_date": ("question", "CreationDate"),
    "question_last_edit_date": ("question", "LastEditDate"),
    "question_tags": ("question", "Tags"),
    "question_score": ("question", "Score"),
    "question_view_count": ("question", "ViewCount"),
    "question_answer_count": ("question", "AnswerCount"),
    "question_comment_count": ("question", "CommentCount"),
    "question_closed_date": ("question", "ClosedDate"),
    "question_owner_user_id": ("question", "OwnerUserId"),
    "first_comment_id": ("first_comment", "Id"),
    "first_comment_text": ("first_comment", "Text"),
    "first_comment_date": ("first_comment", "CreationDate"),
    "first_comment_score": ("first_comment", "Score"),
    "first_comment_user_id": ("first_comment", "UserId"),
    "first_answer_id": ("first_answer", "Id"),
    "first_answer_body": ("first_answer", "Body"),
    "first_answer_date": ("first_answer", "CreationDate"),
    "first_answer_score": ("first_answer", "Score"),
    "first_answer_owner_user_id": ("first_answer", "OwnerUserId"),
    "accepted_answer_id": ("question", "AcceptedAnswerId"),
    "accepted_answer_body": ("accepted_answer", "Body"),
    "accepted_answer_date": ("accepted_answer", "CreationDate"),
    "accepted_answer_score": ("accepted_answer", "Score"),
    "accepted_answer_owner_user_id": ("accepted_answer", "OwnerUserId"),
}


def first_row(rows: Sequence[dict[str, str]]) -> dict[str, str]:
    """Return the earliest row from an already sorted collection."""
    return rows[0] if rows else {}


def load_summary_fields(path: Path) -> list[str]:
    """Load enabled summary fields in their requested output order.

    The TSV must preserve every supported field-to-source mapping and use
    ``TRUE`` or ``FALSE`` in ``include``.  Unknown fields, duplicates, invalid
    mappings, invalid flags, and an empty selection raise contextual
    ``ValueError``; an absent file raises ``FileNotFoundError``.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Summary field file not found: {path}")

    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file, delimiter="\t")
        required = {"field", "include", "source_record", "source_attribute"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(
                f"{path}: expected TSV columns: " + ", ".join(sorted(required))
            )
        rows = list(reader)

    selected: list[str] = []
    seen: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        field = (row.get("field") or "").strip()
        if field not in FIELD_SOURCES:
            raise ValueError(f"{path} row {row_number}: unknown summary field {field!r}")
        if field in seen:
            raise ValueError(f"{path} row {row_number}: duplicate summary field {field!r}")
        seen.add(field)

        expected_record, expected_attribute = FIELD_SOURCES[field]
        if (
            row.get("source_record") != expected_record
            or row.get("source_attribute") != expected_attribute
        ):
            raise ValueError(
                f"{path} row {row_number}: source mapping for {field!r} must be "
                f"{expected_record}.{expected_attribute}"
            )

        include = (row.get("include") or "").strip().upper()
        if include not in {"TRUE", "FALSE"}:
            raise ValueError(
                f"{path} row {row_number}: include must be TRUE or FALSE"
            )
        if include == "TRUE":
            selected.append(field)

    if not selected:
        raise ValueError(f"{path}: select at least one summary field")
    return selected


def summary_values(
    question: dict[str, str],
    comments: Sequence[dict[str, str]],
    answers: Sequence[dict[str, str]],
) -> dict[str, str]:
    """Map one question and its already ordered related rows to supported fields.

    The first comment and answer come from position zero.  The accepted answer
    is matched to the question's original ``AcceptedAnswerId``.  Unavailable
    source values become empty strings.
    """
    accepted_id = question.get("AcceptedAnswerId", "")
    records = {
        "question": question,
        "first_comment": first_row(comments),
        "first_answer": first_row(answers),
        "accepted_answer": next(
            (answer for answer in answers if answer.get("Id") == accepted_id), {}
        ),
    }
    return {
        field: records[record].get(attribute, "")
        for field, (record, attribute) in FIELD_SOURCES.items()
    }


def build_summary_tree(
    question_ids: Sequence[str],
    questions: dict[str, dict[str, str]],
    comments: dict[str, list[dict[str, str]]],
    answers: dict[str, list[dict[str, str]]],
    fields: Sequence[str],
) -> etree._ElementTree:
    """Build one ordered, selected-field element per requested question.

    The input dictionaries must contain every requested question.  Field order
    is copied exactly from ``fields``; empty values remain present as empty XML
    elements.
    """
    root = etree.Element("requests")
    for question_id in question_ids:
        values = summary_values(
            questions[question_id],
            comments.get(question_id, []),
            answers.get(question_id, []),
        )
        request = etree.SubElement(root, "request")
        for field in fields:
            etree.SubElement(request, field).text = values[field]
    return etree.ElementTree(root)


def extract_request_summaries(
    dump_dir: Path,
    question_ids: Sequence[str],
    output_path: Path,
    fields_path: Path = DEFAULT_FIELDS_FILE,
) -> Path:
    """Write selected summary fields for one or more question IDs.

    The function validates and deduplicates IDs, loads the selected field TSV,
    reads related dump rows, protects every source path, and atomically
    publishes the XML.  Input, XML, validation, and filesystem errors propagate
    to the caller; the returned path identifies the result.
    """
    requested_ids = normalize_question_ids(question_ids)
    posts_path, comments_path = source_paths(Path(dump_dir))
    output_path = Path(output_path)
    fields_path = Path(fields_path)
    protect_source_files(output_path, (posts_path, comments_path, fields_path))

    fields = load_summary_fields(fields_path)
    questions, answers = read_posts(posts_path, requested_ids)
    comments = read_question_comments(comments_path, requested_ids)
    write_xml_safely(
        build_summary_tree(requested_ids, questions, comments, answers, fields),
        output_path,
    )
    return output_path


def main(arguments: Sequence[str] | None = None) -> int:
    """Run the command-line interface and return its process exit code.

    Success prints the destination and returns ``0``.  Handled input,
    validation, XML, and filesystem errors print one contextual message to
    standard error and return ``1``.
    """
    parser = argparse.ArgumentParser(
        description="Extract selected question-summary fields into one XML file."
    )
    parser.add_argument(
        "--dump-dir",
        required=True,
        type=Path,
        help="Folder containing Posts.xml and Comments.xml.",
    )
    parser.add_argument(
        "--output", required=True, type=Path, help="Destination XML file."
    )
    parser.add_argument(
        "--fields",
        type=Path,
        default=DEFAULT_FIELDS_FILE,
        help=(
            "TSV field selection. Copy config/summary_fields.tsv and change "
            "TRUE/FALSE values to customize the output."
        ),
    )
    parser.add_argument(
        "question_ids",
        nargs="+",
        metavar="QUESTION_ID",
        help="One question post ID or several question post IDs.",
    )
    values = parser.parse_args(arguments)
    try:
        output = extract_request_summaries(
            values.dump_dir,
            values.question_ids,
            values.output,
            values.fields,
        )
    except (FileNotFoundError, OSError, ValueError, etree.XMLSyntaxError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
