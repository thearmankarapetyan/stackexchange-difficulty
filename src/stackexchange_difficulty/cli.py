"""Command-line interface for the corpus scaffold."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from stackexchange_difficulty.api import run_api_smoke
from stackexchange_difficulty.derive import derive_indicators
from stackexchange_difficulty.jsonl import build_threads, write_jsonl
from stackexchange_difficulty.provenance import load_provenance
from stackexchange_difficulty.validation import (
    read_table,
    validate_dataset,
    write_validation_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stackexchange-difficulty")
    subparsers = parser.add_subparsers(dest="command")

    validate = subparsers.add_parser("validate", help="Validate corpus tables.")
    validate.add_argument("--questions", required=True)
    validate.add_argument("--answers")
    validate.add_argument("--comments")
    validate.add_argument("--provenance")
    validate.add_argument("--out", required=True)
    validate.set_defaults(func=cmd_validate)

    derive = subparsers.add_parser("derive", help="Derive indicators and JSONL threads.")
    derive.add_argument("--questions", required=True)
    derive.add_argument("--answers")
    derive.add_argument("--comments")
    derive.add_argument("--provenance")
    derive.add_argument("--out-dir", required=True)
    derive.set_defaults(func=cmd_derive)

    api_smoke = subparsers.add_parser("api-smoke", help="Run opt-in API v2.3 metadata smoke.")
    api_smoke.add_argument("--live", action="store_true")
    api_smoke.add_argument("--site", default="stackoverflow")
    api_smoke.add_argument("--out", required=True)
    api_smoke.set_defaults(func=cmd_api_smoke)

    return parser


def cmd_validate(args: argparse.Namespace) -> int:
    questions, answers, comments, provenance = _load_inputs(args)
    report = validate_dataset(questions, answers=answers, comments=comments, provenance=provenance)
    write_validation_report(report, args.out)
    print(json.dumps({"ok": report.ok, "issues": len(report.issues)}, sort_keys=True))
    return 0 if report.ok else 1


def cmd_derive(args: argparse.Namespace) -> int:
    questions, answers, comments, provenance = _load_inputs(args)
    report = validate_dataset(questions, answers=answers, comments=comments, provenance=provenance)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_validation_report(report, out_dir / "validation_report.json")
    if not report.ok:
        print(json.dumps({"ok": False, "issues": len(report.issues)}, sort_keys=True))
        return 1

    indicators = derive_indicators(questions, answers=answers, comments=comments)
    write_tsv(indicators, out_dir / "derived_thread_indicators.tsv")
    threads = build_threads(
        questions,
        answers=answers,
        comments=comments,
        indicators=indicators,
        provenance=provenance,
    )
    write_jsonl(threads, out_dir / "threads.jsonl")
    print(json.dumps({"ok": True, "threads": len(threads)}, sort_keys=True))
    return 0


def cmd_api_smoke(args: argparse.Namespace) -> int:
    try:
        metadata = run_api_smoke(live=args.live, site=args.site, out=args.out)
    except ValueError as exc:
        print(str(exc))
        return 2
    print(json.dumps({"ok": True, "http_status": metadata["http_status"]}, sort_keys=True))
    return 0


def write_tsv(rows: list[dict[str, Any]], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        target.write_text("", encoding="utf-8")
        return
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _load_inputs(args: argparse.Namespace):
    questions = read_table(args.questions, name="questions")
    answers = read_table(args.answers, name="answers") if args.answers else None
    comments = read_table(args.comments, name="comments") if args.comments else None
    provenance = load_provenance(args.provenance) if args.provenance else None
    return questions, answers, comments, provenance
