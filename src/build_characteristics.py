"""Build one clear question-level table from a Stack Exchange data dump.

The script reads only the source files needed by the current analysis:
Posts.xml, Comments.xml, and Votes.xml. It creates:

* thread_characteristics.tsv — one row per selected question;
* run_metadata.json — source, period, schema, and execution information;
* validation.tsv — checks and explicit warnings about source differences.

Example:
    python src/build_characteristics.py \
        --dump-dir /path/to/superuser.com \
        --site superuser.com \
        --dump-date 2026-04-20 \
        --start-date 2024-01-01 \
        --end-date 2024-12-31 \
        --output-dir data/processed/superuser-2024
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import tempfile
import time
from collections import defaultdict
from contextlib import suppress
from datetime import date, datetime, time as datetime_time, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from lxml import etree

from question_characteristics import (
    build_characteristic_row,
    optional_integer,
    optional_stack_datetime,
)
from stackexchange_xml import (
    chronological_key,
    describe_row as row_context,
    parse_stack_datetime as stack_datetime,
    positive_id,
    stream_rows as xml_rows,
)


SCHEMA_VERSION = "1.0"
PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = PROJECT_DIR / "config" / "characteristics.tsv"
SOURCE_FILENAMES = ("Posts.xml", "Comments.xml", "Votes.xml")
SITE_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?")


# 1. Read the user-supplied run settings.
def parse_args(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    """Read and validate the command-line parameters."""
    parser = argparse.ArgumentParser(
        description="Build a verified question-level TSV from a Stack Exchange XML dump."
    )
    parser.add_argument(
        "--dump-dir",
        required=True,
        type=Path,
        help="Folder containing Posts.xml, Comments.xml, and Votes.xml.",
    )
    parser.add_argument(
        "--site",
        required=True,
        help="Site host name used in provenance and question URLs, for example superuser.com.",
    )
    parser.add_argument(
        "--dump-date",
        required=True,
        help="Snapshot date represented by the dump, in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--start-date",
        required=True,
        help="First included question date, in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--end-date",
        required=True,
        help="Last included question date, in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Folder that will receive the TSV, metadata, and validation files.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA,
        help="Characteristic specification TSV. The project default is used normally.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional chronological row limit for a quick verification run.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing output from an earlier run.",
    )
    values = parser.parse_args(arguments)

    if SITE_PATTERN.fullmatch(values.site) is None:
        parser.error("--site must be a plain host name such as superuser.com")
    if values.limit is not None and values.limit <= 0:
        parser.error("--limit must be a positive integer")

    try:
        values.dump_date_value = date.fromisoformat(values.dump_date)
        values.start_datetime = datetime.combine(
            date.fromisoformat(values.start_date), datetime_time.min
        )
        values.end_datetime = datetime.combine(
            date.fromisoformat(values.end_date), datetime_time.max
        )
    except ValueError:
        parser.error("--dump-date, --start-date, and --end-date must use YYYY-MM-DD")
    if values.start_datetime > values.end_datetime:
        parser.error("--start-date must be on or before --end-date")
    if values.dump_date_value < values.end_datetime.date():
        parser.error("--dump-date must be on or after --end-date")
    return values


# 2. Read the selected questions and their related source rows.
def select_questions(
    posts_path: Path,
    start: datetime,
    end: datetime,
    limit: int | None,
) -> list[dict[str, str]]:
    """Select question rows in chronological order for the requested period."""
    selected: list[tuple[datetime, Decimal, int, dict[str, str]]] = []
    for row in xml_rows(posts_path):
        if row.get("PostTypeId") != "1":
            continue
        context = row_context(posts_path, row)
        positive_id(row.get("Id"), context)
        created = stack_datetime(row.get("CreationDate"), context, "CreationDate")
        if start <= created <= end:
            optional_stack_datetime(row.get("LastEditDate"), context, "LastEditDate")
            optional_stack_datetime(row.get("ClosedDate"), context, "ClosedDate")
            selected.append((*chronological_key(posts_path, row), row))

    selected.sort(key=lambda item: (item[0], item[1]))
    if limit is not None:
        selected = selected[:limit]
    return [row for _, _, _, row in selected]


def read_answers(
    posts_path: Path, question_ids: set[str]
) -> dict[str, list[dict[str, str]]]:
    """Read every available answer whose parent is a selected question."""
    answers: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in xml_rows(posts_path):
        parent_id = row.get("ParentId")
        if row.get("PostTypeId") != "2" or parent_id not in question_ids:
            continue
        context = row_context(posts_path, row)
        positive_id(row.get("Id"), context)
        stack_datetime(row.get("CreationDate"), context, "CreationDate")
        optional_integer(row.get("Score"), context, "Score")
        answers[parent_id].append(row)

    for rows in answers.values():
        rows.sort(key=lambda row: chronological_key(posts_path, row))
    return answers


def read_question_comments(
    comments_path: Path, question_ids: set[str]
) -> dict[str, list[dict[str, str]]]:
    """Read comments attached directly to selected questions."""
    comments: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in xml_rows(comments_path):
        question_id = row.get("PostId")
        if question_id not in question_ids:
            continue
        context = row_context(comments_path, row)
        positive_id(row.get("Id"), context)
        stack_datetime(row.get("CreationDate"), context, "CreationDate")
        comments[question_id].append(row)

    for rows in comments.values():
        rows.sort(key=lambda row: chronological_key(comments_path, row))
    return comments


def read_acceptance_dates(
    votes_path: Path, accepted_answer_ids: set[str]
) -> dict[str, date]:
    """Read the earliest acceptance day for each currently accepted answer."""
    dates: dict[str, date] = {}
    for row in xml_rows(votes_path):
        answer_id = row.get("PostId")
        if row.get("VoteTypeId") != "1" or answer_id not in accepted_answer_ids:
            continue
        context = row_context(votes_path, row)
        created = stack_datetime(row.get("CreationDate"), context, "CreationDate").date()
        if answer_id not in dates or created < dates[answer_id]:
            dates[answer_id] = created
    return dates


# 3. Check and write the three canonical output files.
def load_schema(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Load the versioned characteristic order and validate its basic shape."""
    if not path.is_file():
        raise FileNotFoundError(f"Characteristic schema not found: {path}")
    with path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file, delimiter="\t"))
    if not rows:
        raise ValueError(f"Characteristic schema is empty: {path}")
    positions = [int(row["position"]) for row in rows]
    if positions != list(range(1, len(rows) + 1)):
        raise ValueError("Characteristic schema positions must be consecutive from 1")
    columns = [row["characteristic"] for row in rows]
    if len(columns) != len(set(columns)):
        raise ValueError("Characteristic schema contains duplicate names")
    return columns, rows


def validation_rows(
    rows: list[dict[str, Any]], columns: list[str]
) -> list[dict[str, str]]:
    """Return independent structural checks and source-difference warnings."""
    expected_keys = set(columns)
    ids = [str(row.get("question_id") or "") for row in rows]
    answer_differences = sum(
        row.get("stackexchange_answer_count") is not None
        and row["stackexchange_answer_count"] != row["available_answer_count"]
        for row in rows
    )
    comment_differences = sum(
        row.get("stackexchange_comment_count") is not None
        and row["stackexchange_comment_count"]
        != row["available_question_comment_count"]
        for row in rows
    )
    unavailable_accepted = sum(
        bool(row.get("accepted_answer_id"))
        and not row.get("accepted_answer_available")
        for row in rows
    )
    missing_acceptance_dates = sum(
        bool(row.get("accepted_answer_id")) and not row.get("acceptance_date")
        for row in rows
    )

    checks: list[tuple[str, str, str, str]] = [
        ("rows produced", "PASS" if rows else "FAIL", str(len(rows)), "more than zero"),
        (
            "schema matches every row",
            "PASS"
            if all(set(row) == expected_keys for row in rows)
            else "FAIL",
            str(sum(set(row) != expected_keys for row in rows)),
            "zero mismatched rows",
        ),
        (
            "question identifiers are present and unique",
            "PASS" if all(ids) and len(ids) == len(set(ids)) else "FAIL",
            f"rows={len(ids)}; unique={len(set(ids))}",
            "all present and unique",
        ),
        (
            "available-answer flag matches available count",
            "PASS"
            if all(
                bool(row["available_answer_count"]) == row["has_available_answer"]
                for row in rows
            )
            else "FAIL",
            str(
                sum(
                    bool(row["available_answer_count"])
                    != row["has_available_answer"]
                    for row in rows
                )
            ),
            "zero mismatches",
        ),
        (
            "Stack Exchange and available answer counts differ",
            "WARN" if answer_differences else "PASS",
            str(answer_differences),
            "reported explicitly because unavailable or removed rows can create differences",
        ),
        (
            "Stack Exchange and available question-comment counts differ",
            "WARN" if comment_differences else "PASS",
            str(comment_differences),
            "reported explicitly because unavailable or removed rows can create differences",
        ),
        (
            "accepted-answer identifiers without an available answer row",
            "WARN" if unavailable_accepted else "PASS",
            str(unavailable_accepted),
            "reported explicitly",
        ),
        (
            "accepted-answer identifiers without a recorded acceptance date",
            "WARN" if missing_acceptance_dates else "PASS",
            str(missing_acceptance_dates),
            "reported explicitly because Votes.xml may omit an event",
        ),
        (
            "observation periods are non-negative",
            "PASS"
            if all(row["observation_days_at_dump"] >= 0 for row in rows)
            else "FAIL",
            str(sum(row["observation_days_at_dump"] < 0 for row in rows)),
            "zero negative values",
        ),
    ]
    return [
        {
            "check": name,
            "status": status,
            "observed": observed,
            "expected_or_meaning": expected,
        }
        for name, status, observed, expected in checks
    ]


def tsv_value(value: Any) -> Any:
    """Serialize booleans and missing values consistently for TSV output."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return value


def atomic_write(path: Path, write: Callable[[Any], None], newline: str | None = None) -> None:
    """Write a complete temporary file beside the destination, then publish it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline=newline,
            delete=False,
            dir=path.parent,
        ) as temporary:
            temporary_path = Path(temporary.name)
            write(temporary)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            with suppress(OSError):
                temporary_path.unlink(missing_ok=True)


def write_tsv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> None:
    """Write dictionaries to a UTF-8 tab-separated file."""
    def write(file: Any) -> None:
        writer = csv.DictWriter(file, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: tsv_value(row.get(column)) for column in columns})

    atomic_write(path, write, newline="")


def write_json(path: Path, value: Any) -> None:
    """Write readable UTF-8 JSON atomically."""
    atomic_write(
        path,
        lambda file: json.dump(value, file, ensure_ascii=False, indent=2),
    )


def source_metadata(path: Path) -> dict[str, Any]:
    """Describe a local source file without rereading it for a full hash."""
    stat = path.stat()
    return {
        "path": str(path.resolve()),
        "size_bytes": stat.st_size,
        "modified_utc": datetime.fromtimestamp(
            stat.st_mtime, tz=timezone.utc
        ).isoformat(),
    }


def output_paths(output_dir: Path) -> dict[str, Path]:
    """Return the three canonical output paths."""
    return {
        "characteristics": output_dir / "thread_characteristics.tsv",
        "metadata": output_dir / "run_metadata.json",
        "validation": output_dir / "validation.tsv",
    }


def ensure_paths(args: argparse.Namespace) -> tuple[dict[str, Path], dict[str, Path]]:
    """Check source files and protect existing outputs."""
    sources = {name: args.dump_dir / name for name in SOURCE_FILENAMES}
    missing = [str(path) for path in sources.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required source file(s): " + ", ".join(missing))
    paths = output_paths(args.output_dir)
    existing = [str(path) for path in paths.values() if path.exists()]
    if existing and not args.overwrite:
        raise FileExistsError(
            "Output already exists; use --overwrite to replace it: " + ", ".join(existing)
        )
    return sources, paths


# 4. Run the complete workflow in a visible, predictable order.
def run(args: argparse.Namespace) -> int:
    """Run extraction, validation, and output writing."""
    started = time.perf_counter()
    sources, paths = ensure_paths(args)
    columns, _ = load_schema(args.schema)

    print("Selecting questions from Posts.xml...")
    questions = select_questions(
        sources["Posts.xml"], args.start_datetime, args.end_datetime, args.limit
    )
    if not questions:
        raise ValueError("No question was found in the requested period")
    question_ids = {row["Id"] for row in questions}

    print(f"Selected {len(questions):,} questions. Reading their answers...")
    answers = read_answers(sources["Posts.xml"], question_ids)
    print("Reading question comments...")
    comments = read_question_comments(sources["Comments.xml"], question_ids)
    accepted_ids = {
        row["AcceptedAnswerId"]
        for row in questions
        if row.get("AcceptedAnswerId")
    }
    print("Reading acceptance dates from Votes.xml...")
    acceptance_dates = read_acceptance_dates(sources["Votes.xml"], accepted_ids)

    print("Calculating documented characteristics...")
    rows = [
        build_characteristic_row(
            question,
            answers.get(question["Id"], []),
            comments.get(question["Id"], []),
            acceptance_dates,
            args.site,
            args.dump_date_value,
            sources["Posts.xml"],
            sources["Comments.xml"],
        )
        for question in questions
    ]
    checks = validation_rows(rows, columns)
    failures = [check for check in checks if check["status"] == "FAIL"]
    warnings = [check for check in checks if check["status"] == "WARN"]
    if failures:
        failed_names = ", ".join(check["check"] for check in failures)
        raise ValueError(f"Internal validation failed: {failed_names}")

    write_tsv(paths["characteristics"], rows, columns)
    write_tsv(
        paths["validation"],
        checks,
        ["check", "status", "observed", "expected_or_meaning"],
    )
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "schema_path": str(args.schema.resolve()),
        "site": args.site,
        "dump_snapshot_date": args.dump_date,
        "question_start_date": args.start_date,
        "question_end_date": args.end_date,
        "row_limit": args.limit,
        "row_count": len(rows),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "python_version": sys.version.split()[0],
        "source_files": {
            name: source_metadata(path) for name, path in sources.items()
        },
        "validation_failures": len(failures),
        "validation_warnings": len(warnings),
    }
    write_json(paths["metadata"], metadata)

    print(f"Wrote {paths['characteristics']}")
    print(
        f"Validation: {len(checks) - len(failures) - len(warnings)} PASS, "
        f"{len(warnings)} WARN, {len(failures)} FAIL"
    )
    return 0


def main(arguments: Sequence[str] | None = None) -> int:
    """Run the command-line program and return a process exit code."""
    try:
        return run(parse_args(arguments))
    except (
        FileNotFoundError,
        FileExistsError,
        OSError,
        ValueError,
        etree.XMLSyntaxError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
