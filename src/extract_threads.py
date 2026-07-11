"""Reconstruct complete Stack Exchange question threads in one XML file.

For every requested question ID, the result contains the original question
attributes, comments attached directly to that question, and all its answers.
Comments on answers are outside the agreed extraction scope.  One ID creates
one thread; several IDs create several threads in the same output file.

Example:
    python src/extract_threads.py --dump-dir /path/to/site-dump \
        --output data/examples/threads.xml 123 456

Requires Python 3.10 or newer and ``lxml``.  Source dump files remain
unchanged, and the destination XML is published atomically.
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


def build_thread_tree(
    question_ids: Sequence[str],
    questions: dict[str, dict[str, str]],
    comments: dict[str, list[dict[str, str]]],
    answers: dict[str, list[dict[str, str]]],
) -> etree._ElementTree:
    """Build ``threads/thread/question/comments+answers`` in request order.

    The input dictionaries must already contain every requested question, and
    related rows must already be chronologically ordered.  Empty ``comments``
    and ``answers`` containers are retained in the returned tree.
    """
    root = etree.Element("threads")
    for question_id in question_ids:
        thread = etree.SubElement(root, "thread")
        question = etree.SubElement(thread, "question", questions[question_id])
        comment_container = etree.SubElement(question, "comments")
        for row in comments.get(question_id, []):
            etree.SubElement(comment_container, "comment", row)
        answer_container = etree.SubElement(question, "answers")
        for row in answers.get(question_id, []):
            etree.SubElement(answer_container, "answer", row)
    return etree.ElementTree(root)


def extract_threads(
    dump_dir: Path, question_ids: Sequence[str], output_path: Path
) -> Path:
    """Extract one or more requested question threads into one XML file.

    IDs are validated and deduplicated in request order.  The function reads
    ``Posts.xml`` and ``Comments.xml``, protects both source paths, and
    atomically publishes the result.  Input, XML, validation, and filesystem
    errors propagate to the caller; the returned path identifies the result.
    """
    requested_ids = normalize_question_ids(question_ids)
    posts_path, comments_path = source_paths(Path(dump_dir))
    output_path = Path(output_path)
    protect_source_files(output_path, (posts_path, comments_path))

    questions, answers = read_posts(posts_path, requested_ids)
    comments = read_question_comments(comments_path, requested_ids)
    write_xml_safely(
        build_thread_tree(requested_ids, questions, comments, answers), output_path
    )
    return output_path


def main(arguments: Sequence[str] | None = None) -> int:
    """Run the command-line interface and return its process exit code.

    Success prints the destination and returns ``0``.  Handled input,
    validation, XML, and filesystem errors print one contextual message to
    standard error and return ``1``.
    """
    parser = argparse.ArgumentParser(
        description="Reconstruct complete Stack Exchange question threads."
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
        output = extract_threads(values.dump_dir, values.question_ids, values.output)
    except (FileNotFoundError, OSError, ValueError, etree.XMLSyntaxError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
