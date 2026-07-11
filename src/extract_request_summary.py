"""Extract the twelve fields requested by the internship supervisors.

Each ``request`` element contains the question ID, body and posting date; the
earliest question comment; the earliest answer; and the answer currently marked
as accepted.  The accepted-answer date is the date when that answer was posted.

Example:
    python src/extract_request_summary.py --dump-dir /path/to/site-dump \
        --output data/examples/request-summary.xml 123 456
"""

from __future__ import annotations

import argparse
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


OUTPUT_FIELDS = (
    "question_id",
    "question_body",
    "question_date",
    "first_comment_id",
    "first_comment_text",
    "first_comment_date",
    "first_answer_id",
    "first_answer_body",
    "first_answer_date",
    "accepted_answer_id",
    "accepted_answer_body",
    "accepted_answer_date",
)


def first_row(rows: Sequence[dict[str, str]]) -> dict[str, str]:
    """Return the first chronological row or an empty row."""
    return rows[0] if rows else {}


def summary_values(
    question: dict[str, str],
    comments: Sequence[dict[str, str]],
    answers: Sequence[dict[str, str]],
) -> dict[str, str]:
    """Map source rows to the twelve requested values."""
    first_comment = first_row(comments)
    first_answer = first_row(answers)
    accepted_id = question.get("AcceptedAnswerId", "")
    accepted_answer = next(
        (answer for answer in answers if answer.get("Id") == accepted_id), {}
    )
    return {
        "question_id": question.get("Id", ""),
        "question_body": question.get("Body", ""),
        "question_date": question.get("CreationDate", ""),
        "first_comment_id": first_comment.get("Id", ""),
        "first_comment_text": first_comment.get("Text", ""),
        "first_comment_date": first_comment.get("CreationDate", ""),
        "first_answer_id": first_answer.get("Id", ""),
        "first_answer_body": first_answer.get("Body", ""),
        "first_answer_date": first_answer.get("CreationDate", ""),
        "accepted_answer_id": accepted_id,
        "accepted_answer_body": accepted_answer.get("Body", ""),
        "accepted_answer_date": accepted_answer.get("CreationDate", ""),
    }


def build_summary_tree(
    question_ids: Sequence[str],
    questions: dict[str, dict[str, str]],
    comments: dict[str, list[dict[str, str]]],
    answers: dict[str, list[dict[str, str]]],
) -> etree._ElementTree:
    """Build one predictable twelve-field element per requested question."""
    root = etree.Element("requests")
    for question_id in question_ids:
        values = summary_values(
            questions[question_id],
            comments.get(question_id, []),
            answers.get(question_id, []),
        )
        request = etree.SubElement(root, "request")
        for field in OUTPUT_FIELDS:
            etree.SubElement(request, field).text = values[field]
    return etree.ElementTree(root)


def extract_request_summaries(
    dump_dir: Path, question_ids: Sequence[str], output_path: Path
) -> Path:
    """Write the twelve requested fields for one or more questions."""
    requested_ids = normalize_question_ids(question_ids)
    posts_path, comments_path = source_paths(Path(dump_dir))
    output_path = Path(output_path)
    protect_source_files(output_path, (posts_path, comments_path))

    questions, answers = read_posts(posts_path, requested_ids)
    comments = read_question_comments(comments_path, requested_ids)
    write_xml_safely(
        build_summary_tree(requested_ids, questions, comments, answers), output_path
    )
    return output_path


def main(arguments: Sequence[str] | None = None) -> int:
    """Run the command-line interface and return its process exit code."""
    parser = argparse.ArgumentParser(
        description="Extract the twelve supervisor-requested fields into XML."
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
        "question_ids",
        nargs="+",
        metavar="QUESTION_ID",
        help="One question ID or several question IDs.",
    )
    values = parser.parse_args(arguments)
    try:
        output = extract_request_summaries(
            values.dump_dir, values.question_ids, values.output
        )
    except (FileNotFoundError, OSError, ValueError, etree.XMLSyntaxError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
