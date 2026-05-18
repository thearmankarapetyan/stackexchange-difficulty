"""Command-line interface for the corpus scaffold."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from stackexchange_difficulty.api import run_api_smoke
from stackexchange_difficulty.data_dump import (
    DataDumpError,
    DataDumpPilotConfig,
    DataDumpPreflightConfig,
    preflight_dump,
    run_data_dump_pilot,
)
from stackexchange_difficulty.derive import derive_indicators
from stackexchange_difficulty.hf_release import (
    HuggingFaceReleaseError,
    prepare_hf_release,
    upload_hf_release,
)
from stackexchange_difficulty.inspection import (
    InspectionError,
    prepare_comment_reinspection_files,
    prepare_inspection_files,
    summarize_comment_reinspection_labels,
    summarize_inspection_labels,
)
from stackexchange_difficulty.inspection_diagnostics import (
    InspectionDiagnosticsError,
    diagnose_inspection_strata,
)
from stackexchange_difficulty.jsonl import build_threads, write_jsonl
from stackexchange_difficulty.provenance import (
    finalize_processed_hashes,
    load_provenance,
    sha256_file,
    write_provenance_json,
)
from stackexchange_difficulty.sede import normalize_sede_export, validate_sede_export
from stackexchange_difficulty.sede_comments import (
    SedeCommentConfig,
    SedeCommentError,
    run_sede_comment_enrichment,
)
from stackexchange_difficulty.sede_pilot import (
    SedePilotConfig,
    SedePilotError,
    resolve_pilot_date,
    run_sede_pilot,
)
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

    preflight_sede = subparsers.add_parser(
        "preflight-sede",
        help="Validate a local SEDE pilot export before ingestion.",
    )
    preflight_sede.add_argument("--export", required=True)
    preflight_sede.add_argument("--min-rows", type=int, default=5000)
    preflight_sede.add_argument("--max-rows", type=int, default=10000)
    preflight_sede.add_argument("--hash-out")
    preflight_sede.set_defaults(func=cmd_preflight_sede)

    ingest_sede = subparsers.add_parser("ingest-sede", help="Normalize a local SEDE pilot export.")
    ingest_sede.add_argument("--export", required=True)
    ingest_sede.add_argument("--provenance", required=True)
    ingest_sede.add_argument("--out-dir", required=True)
    ingest_sede.set_defaults(func=cmd_ingest_sede)

    preflight_dump_parser = subparsers.add_parser(
        "preflight-dump",
        help="Validate local extracted Stack Exchange Data Dump XML files.",
    )
    preflight_dump_parser.add_argument("--dump-dir", required=True)
    preflight_dump_parser.add_argument("--site-slug", required=True)
    preflight_dump_parser.add_argument("--site-name", required=True)
    preflight_dump_parser.add_argument("--dump-date", required=True)
    preflight_dump_parser.add_argument(
        "--sample-profile",
        default="answerable_pilot",
        help="Supported profiles: answerable_pilot, answerable_clean.",
    )
    preflight_dump_parser.add_argument("--include-post-history", action="store_true")
    preflight_dump_parser.add_argument("--out")
    preflight_dump_parser.add_argument(
        "--project-root",
        help=(
            "Project root. Defaults to auto-detection from the current "
            "directory or a projects/stackexchange-difficulty child."
        ),
    )
    preflight_dump_parser.set_defaults(func=cmd_preflight_dump)

    run_dump = subparsers.add_parser(
        "run-data-dump-pilot",
        help="Run the local Data Dump pilot parser pipeline.",
    )
    run_dump.add_argument("--dump-dir", required=True)
    run_dump.add_argument("--site-slug", required=True)
    run_dump.add_argument("--site-name", required=True)
    run_dump.add_argument("--pilot-slug", required=True)
    run_dump.add_argument("--dump-date", required=True)
    run_dump.add_argument(
        "--sample-profile",
        default="answerable_pilot",
        help="Supported profiles: answerable_pilot, answerable_clean.",
    )
    run_dump.add_argument("--sample-size", type=int, default=5000)
    run_dump.add_argument("--sample-seed", type=int, default=20260513)
    run_dump.add_argument("--include-post-history", action="store_true")
    run_dump.add_argument(
        "--project-root",
        help=(
            "Project root. Defaults to auto-detection from the current "
            "directory or a projects/stackexchange-difficulty child."
        ),
    )
    run_dump.set_defaults(func=cmd_run_data_dump_pilot)

    run_sede = subparsers.add_parser(
        "run-sede-pilot",
        help="Run the safe browser-assisted SEDE pilot pipeline.",
    )
    run_sede.add_argument("--export", help="Already downloaded local SEDE CSV/TSV export.")
    run_sede.add_argument("--pilot-date", default="auto")
    run_sede.add_argument("--download-dir", default=str(Path.home() / "Downloads"))
    run_sede.add_argument("--open-browser", action="store_true")
    run_sede.add_argument("--timeout-seconds", type=float, default=1800)
    run_sede.add_argument("--min-rows", type=int, default=5000)
    run_sede.add_argument("--max-rows", type=int, default=10000)
    run_sede.add_argument(
        "--query-url",
        help=(
            "Explicit SEDE query URL. Defaults to the Stack Overflow query page, "
            "or to https://data.stackexchange.com/{site-slug}/query/new when "
            "--site-slug is set."
        ),
    )
    run_sede.add_argument(
        "--site-slug",
        help="SEDE site slug used for site-specific names, for example math.",
    )
    run_sede.add_argument(
        "--site-name",
        help="Human-readable site name for provenance and audits, for example Mathematics.",
    )
    run_sede.add_argument(
        "--pilot-slug",
        help=(
            "Optional pilot identity separate from the SEDE site slug, for example "
            "math-answerable."
        ),
    )
    run_sede.add_argument(
        "--query-file",
        help=(
            "Repository-relative or absolute SQL file to use for browser "
            "instructions and provenance."
        ),
    )
    run_sede.add_argument(
        "--project-root",
        help=(
            "Project root. Defaults to auto-detection from the current "
            "directory or a projects/stackexchange-difficulty child."
        ),
    )
    run_sede.set_defaults(func=cmd_run_sede_pilot)

    run_sede_comments = subparsers.add_parser(
        "run-sede-comment-enrichment",
        help="Export and ingest SEDE comments for an existing pilot.",
    )
    run_sede_comments.add_argument(
        "--export",
        help="Already downloaded local comments CSV/TSV export.",
    )
    run_sede_comments.add_argument("--pilot-date", required=True)
    run_sede_comments.add_argument("--site-slug", required=True)
    run_sede_comments.add_argument("--site-name")
    run_sede_comments.add_argument(
        "--pilot-slug",
        help=(
            "Optional pilot identity separate from the SEDE site slug, for example "
            "math-answerable."
        ),
    )
    run_sede_comments.add_argument("--questions", required=True)
    run_sede_comments.add_argument("--answers", required=True)
    run_sede_comments.add_argument("--download-dir", default="auto")
    run_sede_comments.add_argument("--open-browser", action="store_true")
    run_sede_comments.add_argument("--timeout-seconds", type=float, default=1800)
    run_sede_comments.add_argument("--query-url")
    run_sede_comments.add_argument(
        "--query-template",
        help="Repository-relative or absolute comment-query template SQL file.",
    )
    run_sede_comments.add_argument(
        "--project-root",
        help=(
            "Project root. Defaults to auto-detection from the current "
            "directory or a projects/stackexchange-difficulty child."
        ),
    )
    run_sede_comments.set_defaults(func=cmd_run_sede_comment_enrichment)

    prepare_hf = subparsers.add_parser(
        "prepare-hf-release",
        help="Prepare a metadata-only Hugging Face dataset release folder.",
    )
    prepare_hf.add_argument("--pilot-date", required=True)
    prepare_hf.add_argument(
        "--site-slug",
        help="Optional pilot site slug, for example math, to find site-specific artifacts.",
    )
    prepare_hf.add_argument(
        "--pilot-slug",
        help=(
            "Optional pilot identity separate from the source site, for example "
            "math-answerable."
        ),
    )
    prepare_hf.add_argument("--repo-id", required=True)
    prepare_hf.add_argument("--out-dir", required=True)
    prepare_hf.add_argument(
        "--project-root",
        help=(
            "Project root. Defaults to auto-detection from the current "
            "directory or a projects/stackexchange-difficulty child."
        ),
    )
    prepare_hf.set_defaults(func=cmd_prepare_hf_release)

    prepare_inspection = subparsers.add_parser(
        "prepare-inspection",
        help="Prepare ignored local files for content-safe pilot inspection.",
    )
    prepare_inspection.add_argument("--questions", required=True)
    prepare_inspection.add_argument("--answers", required=True)
    prepare_inspection.add_argument("--indicators", required=True)
    prepare_inspection.add_argument("--site-slug", required=True)
    prepare_inspection.add_argument("--pilot-date", required=True)
    prepare_inspection.add_argument("--sample-size", type=int, default=100)
    prepare_inspection.add_argument("--seed", type=int, default=20260513)
    prepare_inspection.add_argument("--out-dir", required=True)
    prepare_inspection.set_defaults(func=cmd_prepare_inspection)

    summarize_inspection = subparsers.add_parser(
        "summarize-inspection",
        help="Append aggregate inspection results to a tracked audit.",
    )
    summarize_inspection.add_argument("--labels", required=True)
    summarize_inspection.add_argument("--audit", required=True)
    summarize_inspection.add_argument(
        "--labeler",
        default="manual",
        help="Aggregate label source recorded in the audit, for example manual or llm_assisted.",
    )
    summarize_inspection.add_argument(
        "--decision-profile",
        default="standard",
        help=(
            "Decision policy for aggregate inspection results: standard, "
            "answerable_pilot, or target_scale_answerable."
        ),
    )
    summarize_inspection.set_defaults(func=cmd_summarize_inspection)

    diagnose_inspection = subparsers.add_parser(
        "diagnose-inspection-strata",
        help="Write aggregate-only diagnostics for local inspection labels.",
    )
    diagnose_inspection.add_argument("--review", required=True)
    diagnose_inspection.add_argument("--labels", required=True)
    diagnose_inspection.add_argument("--out", required=True)
    diagnose_inspection.set_defaults(func=cmd_diagnose_inspection_strata)

    prepare_reinspection = subparsers.add_parser(
        "prepare-comment-reinspection",
        help="Prepare ignored comment-enriched files for targeted LLM reinspection.",
    )
    prepare_reinspection.add_argument("--review", required=True)
    prepare_reinspection.add_argument("--labels", required=True)
    prepare_reinspection.add_argument("--comments", required=True)
    prepare_reinspection.add_argument("--out-dir", required=True)
    prepare_reinspection.set_defaults(func=cmd_prepare_comment_reinspection)

    summarize_reinspection = subparsers.add_parser(
        "summarize-comment-reinspection",
        help="Append aggregate comment-enriched reinspection results to a tracked audit.",
    )
    summarize_reinspection.add_argument("--labels", required=True)
    summarize_reinspection.add_argument("--audit", required=True)
    summarize_reinspection.add_argument(
        "--labeler",
        default="llm_assisted_comment_enriched",
        help=(
            "Aggregate label source recorded in the audit, for example "
            "llm_assisted_comment_enriched."
        ),
    )
    summarize_reinspection.set_defaults(func=cmd_summarize_comment_reinspection)

    upload_hf = subparsers.add_parser(
        "upload-hf-release",
        help="Dry-run or apply a metadata-only Hugging Face dataset upload.",
    )
    upload_hf.add_argument("--release-dir", required=True)
    upload_hf.add_argument("--repo-id", required=True)
    upload_hf.add_argument("--apply", action="store_true")
    upload_hf.add_argument(
        "--commit-message",
        default="Publish metadata-only Stack Exchange difficulty release",
    )
    upload_hf.set_defaults(func=cmd_upload_hf_release)

    finalize_provenance = subparsers.add_parser(
        "finalize-provenance",
        help="Replace pending provenance output hashes from a hash manifest.",
    )
    finalize_provenance.add_argument("--provenance", required=True)
    finalize_provenance.add_argument("--hash-file", required=True)
    finalize_provenance.add_argument("--out", required=True)
    finalize_provenance.set_defaults(func=cmd_finalize_provenance)

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


def cmd_preflight_sede(args: argparse.Namespace) -> int:
    export_path = Path(args.export)
    digest = sha256_file(export_path)
    hash_out = Path(args.hash_out) if args.hash_out else Path(f"{export_path}.sha256")
    hash_out.parent.mkdir(parents=True, exist_ok=True)
    hash_out.write_text(f"{digest}  {export_path}\n", encoding="utf-8")

    export = read_table(export_path, name="sede_export")
    issues = validate_sede_export(export)
    row_count_ok = args.min_rows <= len(export.rows) <= args.max_rows
    ok = not issues and row_count_ok
    payload = {
        "ok": ok,
        "rows": len(export.rows),
        "columns": list(export.columns),
        "sha256": digest,
        "hash_out": str(hash_out),
        "issues": [issue.__dict__ for issue in issues],
    }
    if not row_count_ok:
        payload["issues"].append(
            {
                "code": "row_count_out_of_range",
                "message": (
                    f"SEDE export row count {len(export.rows)} is outside "
                    f"{args.min_rows}-{args.max_rows}."
                ),
                "row_id": None,
            }
        )
    print(json.dumps(payload, sort_keys=True))
    return 0 if ok else 1


def cmd_ingest_sede(args: argparse.Namespace) -> int:
    export = read_table(args.export, name="sede_export")
    provenance = load_provenance(args.provenance)
    export_issues = validate_sede_export(export)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if export_issues:
        report = {
            "ok": False,
            "issues": [issue.__dict__ for issue in export_issues],
            "row_counts": {"sede_export": len(export.rows)},
        }
        (out_dir / "validation_report.json").write_text(
            json.dumps(report, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"ok": False, "issues": len(export_issues)}, sort_keys=True))
        return 1

    questions, answers, comments = normalize_sede_export(export)
    report = validate_dataset(
        questions,
        answers=answers,
        comments=comments,
        provenance=provenance,
    )
    write_validation_report(report, out_dir / "validation_report.json")
    if not report.ok:
        print(json.dumps({"ok": False, "issues": len(report.issues)}, sort_keys=True))
        return 1

    write_tsv(questions.rows, out_dir / "questions.tsv", fieldnames=list(questions.columns))
    write_tsv(answers.rows, out_dir / "answers.tsv", fieldnames=list(answers.columns))
    write_tsv(comments.rows, out_dir / "comments.tsv", fieldnames=list(comments.columns))
    (out_dir / "provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": True,
                "questions": len(questions.rows),
                "answers": len(answers.rows),
                "comments": len(comments.rows),
            },
            sort_keys=True,
        )
    )
    return 0


def cmd_preflight_dump(args: argparse.Namespace) -> int:
    try:
        root = resolve_project_root(args.project_root)
        result = preflight_dump(
            DataDumpPreflightConfig(
                project_root=root,
                dump_dir=_resolve_cli_path(args.dump_dir, root),
                site_slug=args.site_slug,
                site_name=args.site_name,
                dump_date=args.dump_date,
                sample_profile=args.sample_profile,
                include_post_history=args.include_post_history,
            )
        )
    except DataDumpError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    payload = result.to_payload()
    if args.out:
        out_path = _resolve_cli_path(args.out, root)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        payload["out"] = str(out_path)
    print(json.dumps(payload, sort_keys=True))
    return 0 if result.ok else 1


def cmd_run_data_dump_pilot(args: argparse.Namespace) -> int:
    try:
        root = resolve_project_root(args.project_root)
        result = run_data_dump_pilot(
            DataDumpPilotConfig(
                project_root=root,
                dump_dir=_resolve_cli_path(args.dump_dir, root),
                site_slug=args.site_slug,
                site_name=args.site_name,
                dump_date=args.dump_date,
                sample_profile=args.sample_profile,
                include_post_history=args.include_post_history,
                pilot_slug=args.pilot_slug,
                sample_size=args.sample_size,
                sample_seed=args.sample_seed,
            )
        )
    except DataDumpError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result.to_payload(), sort_keys=True))
    return 0 if result.ok else 1


def cmd_finalize_provenance(args: argparse.Namespace) -> int:
    provenance = load_provenance(args.provenance)
    finalized = finalize_processed_hashes(provenance, args.hash_file)
    write_provenance_json(finalized, args.out)
    print(
        json.dumps(
            {
                "ok": True,
                "output_hash": finalized["output_hash"],
                "out": args.out,
            },
            sort_keys=True,
        )
    )
    return 0


def cmd_run_sede_pilot(args: argparse.Namespace) -> int:
    try:
        pilot_date = resolve_pilot_date(args.pilot_date)
        result = run_sede_pilot(
            SedePilotConfig(
                project_root=resolve_project_root(args.project_root),
                pilot_date=pilot_date,
                export_path=Path(args.export) if args.export else None,
                download_dir=args.download_dir,
                open_browser=args.open_browser,
                timeout_seconds=args.timeout_seconds,
                min_rows=args.min_rows,
                max_rows=args.max_rows,
                query_url=args.query_url,
                site_slug=args.site_slug,
                site_name=args.site_name,
                pilot_slug=args.pilot_slug,
                query_file=Path(args.query_file) if args.query_file else None,
            )
        )
    except SedePilotError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result.to_payload(), sort_keys=True))
    return 0 if result.ok else 1


def cmd_run_sede_comment_enrichment(args: argparse.Namespace) -> int:
    try:
        pilot_date = resolve_pilot_date(args.pilot_date)
        root = resolve_project_root(args.project_root)
        result = run_sede_comment_enrichment(
            SedeCommentConfig(
                project_root=root,
                pilot_date=pilot_date,
                site_slug=args.site_slug,
                site_name=args.site_name,
                pilot_slug=args.pilot_slug,
                questions_path=_resolve_cli_path(args.questions, root),
                answers_path=_resolve_cli_path(args.answers, root),
                export_path=_resolve_cli_path(args.export, root) if args.export else None,
                download_dir=args.download_dir,
                open_browser=args.open_browser,
                timeout_seconds=args.timeout_seconds,
                query_url=args.query_url,
                query_template=Path(args.query_template) if args.query_template else None,
            )
        )
    except (SedeCommentError, SedePilotError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result.to_payload(), sort_keys=True))
    return 0 if result.ok else 1


def cmd_prepare_hf_release(args: argparse.Namespace) -> int:
    try:
        result = prepare_hf_release(
            project_root=resolve_project_root(args.project_root),
            pilot_date=args.pilot_date,
            repo_id=args.repo_id,
            out_dir=Path(args.out_dir),
            site_slug=args.site_slug,
            pilot_slug=args.pilot_slug,
        )
    except HuggingFaceReleaseError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result.to_payload(), sort_keys=True))
    return 0


def cmd_prepare_inspection(args: argparse.Namespace) -> int:
    try:
        result = prepare_inspection_files(
            questions=read_table(args.questions, name="questions"),
            answers=read_table(args.answers, name="answers"),
            indicators=read_table(args.indicators, name="derived_thread_indicators"),
            site_slug=args.site_slug,
            pilot_date=args.pilot_date,
            sample_size=args.sample_size,
            out_dir=Path(args.out_dir),
            seed=args.seed,
        )
    except InspectionError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result.to_payload(), sort_keys=True))
    return 0


def cmd_summarize_inspection(args: argparse.Namespace) -> int:
    try:
        result = summarize_inspection_labels(
            labels=read_table(args.labels, name="inspection_labels"),
            audit_path=Path(args.audit),
            labeler=args.labeler,
            decision_profile=args.decision_profile,
        )
    except InspectionError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result.to_payload(), sort_keys=True))
    return 0


def cmd_diagnose_inspection_strata(args: argparse.Namespace) -> int:
    try:
        result = diagnose_inspection_strata(
            review=read_table(args.review, name="inspection_review"),
            labels=read_table(args.labels, name="inspection_labels"),
            output_path=Path(args.out),
        )
    except InspectionDiagnosticsError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result.to_payload(), sort_keys=True))
    return 0


def cmd_prepare_comment_reinspection(args: argparse.Namespace) -> int:
    try:
        result = prepare_comment_reinspection_files(
            review=read_table(args.review, name="inspection_review"),
            labels=read_table(args.labels, name="inspection_labels"),
            comments=read_table(args.comments, name="comments"),
            out_dir=Path(args.out_dir),
        )
    except InspectionError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result.to_payload(), sort_keys=True))
    return 0


def cmd_summarize_comment_reinspection(args: argparse.Namespace) -> int:
    try:
        result = summarize_comment_reinspection_labels(
            labels=read_table(args.labels, name="comment_reinspection_labels"),
            audit_path=Path(args.audit),
            labeler=args.labeler,
        )
    except InspectionError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result.to_payload(), sort_keys=True))
    return 0


def resolve_project_root(value: str | None = None) -> Path:
    if value:
        return Path(value)

    cwd = Path.cwd()
    candidates = [
        cwd,
        cwd / "projects/stackexchange-difficulty",
        Path(__file__).resolve().parents[2],
    ]
    for candidate in candidates:
        if _looks_like_project_root(candidate):
            return candidate
    return cwd


def _looks_like_project_root(path: Path) -> bool:
    return (
        (path / "src/stackexchange_difficulty").is_dir()
        and (path / "reports/datasets/stackexchange-difficulty").is_dir()
    )


def _resolve_cli_path(value: str, root: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    rooted = root / path
    if rooted.exists():
        return rooted
    if path.exists():
        return path
    return rooted


def cmd_upload_hf_release(args: argparse.Namespace) -> int:
    try:
        result = upload_hf_release(
            release_dir=Path(args.release_dir),
            repo_id=args.repo_id,
            apply=args.apply,
            commit_message=args.commit_message,
        )
    except HuggingFaceReleaseError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result.to_payload(), sort_keys=True))
    return 0


def cmd_api_smoke(args: argparse.Namespace) -> int:
    try:
        metadata = run_api_smoke(live=args.live, site=args.site, out=args.out)
    except ValueError as exc:
        print(str(exc))
        return 2
    print(json.dumps({"ok": True, "http_status": metadata["http_status"]}, sort_keys=True))
    return 0


def write_tsv(
    rows: list[dict[str, Any]],
    path: str | Path,
    fieldnames: list[str] | None = None,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not rows and not fieldnames:
        target.write_text("", encoding="utf-8")
        return
    fieldnames = fieldnames or list(rows[0])
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _load_inputs(args: argparse.Namespace):
    questions = read_table(args.questions, name="questions")
    answers = read_table(args.answers, name="answers") if args.answers else None
    comments = read_table(args.comments, name="comments") if args.comments else None
    provenance = load_provenance(args.provenance) if args.provenance else None
    return questions, answers, comments, provenance
