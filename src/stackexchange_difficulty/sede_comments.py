"""SEDE comment-enrichment workflow for an existing pilot."""

from __future__ import annotations

import csv
import os
import re
import shutil
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from stackexchange_difficulty.derive import derive_indicators
from stackexchange_difficulty.jsonl import build_threads, write_jsonl
from stackexchange_difficulty.provenance import (
    finalize_processed_hashes,
    sha256_file,
    write_provenance_json,
)
from stackexchange_difficulty.schema import SEDE_COMMENT_REQUIRED_COLUMNS
from stackexchange_difficulty.sede_pilot import (
    SUPPORTED_EXPORT_SUFFIXES,
    normalize_pilot_slug,
    normalize_site_slug,
    prepare_browser_session,
    wait_for_sede_export,
)
from stackexchange_difficulty.validation import (
    Table,
    ValidationIssue,
    read_table,
    validate_dataset,
    validate_required_columns,
    write_validation_report,
)

COMMENT_QUERY_URL_TEMPLATE = "https://data.stackexchange.com/{site_slug}/query/new"
DEFAULT_COMMENT_QUERY_TEMPLATE = Path(
    "reports/datasets/stackexchange-difficulty/sede_comments_query_template.sql"
)
COMMENTS_RAW_PREFIX = "sede-comments"
COMMENT_POST_TYPES = {"1", "2"}
DOWNLOAD_DIR_NAMES = ("Downloads", "T\u00e9l\u00e9chargements", "Telechargements")


class SedeCommentError(RuntimeError):
    """Raised when SEDE comment enrichment cannot continue safely."""


@dataclass(frozen=True)
class SedeCommentConfig:
    project_root: Path
    pilot_date: str
    site_slug: str
    site_name: str | None
    questions_path: Path
    answers_path: Path
    pilot_slug: str | None = None
    export_path: Path | None = None
    download_dir: Path | str | None = "auto"
    open_browser: bool = False
    timeout_seconds: float = 1800
    query_url: str | None = None
    query_template: Path | None = None


@dataclass(frozen=True)
class SedeCommentResult:
    ok: bool
    query_file: Path
    raw_export: Path | None
    provenance: Path
    processed_dir: Path | None
    derived_dir: Path | None
    audit: Path
    comments: int
    covered_questions: int
    covered_answer_posts: int
    issues: list[dict[str, Any]]

    def to_payload(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "query_file": str(self.query_file),
            "raw_export": str(self.raw_export) if self.raw_export else None,
            "provenance": str(self.provenance),
            "processed_dir": str(self.processed_dir) if self.processed_dir else None,
            "derived_dir": str(self.derived_dir) if self.derived_dir else None,
            "audit": str(self.audit),
            "comments": self.comments,
            "covered_questions": self.covered_questions,
            "covered_answer_posts": self.covered_answer_posts,
            "issues": self.issues,
        }


def run_sede_comment_enrichment(config: SedeCommentConfig) -> SedeCommentResult:
    root = config.project_root.resolve()
    site_slug = normalize_site_slug(config.site_slug)
    site_name = config.site_name or _name_from_slug(site_slug)
    pilot_slug = normalize_pilot_slug(config.pilot_slug) if config.pilot_slug else None
    artifact_slug = pilot_slug or site_slug
    report_slug = artifact_slug.replace("-", "_")
    query_url = config.query_url or COMMENT_QUERY_URL_TEMPLATE.format(site_slug=site_slug)
    query_template = _resolve_template(root, config.query_template)
    questions = read_table(config.questions_path, name="questions")
    answers = read_table(config.answers_path, name="answers")

    context = _build_context(root, artifact_slug, config.pilot_date)
    query_file = context["query_file"]
    raw_target_stem = f"{COMMENTS_RAW_PREFIX}-{artifact_slug}-{config.pilot_date}"
    audit_path = (
        root
        / "reports/datasets/stackexchange-difficulty/audits"
        / f"sede_pilot_{report_slug}_{config.pilot_date}.md"
    )
    provenance_path = (
        root
        / "reports/datasets/stackexchange-difficulty"
        / f"provenance_sede_comments_{report_slug}_{config.pilot_date}.json"
    )

    query_text = render_comment_query(
        questions=questions,
        answers=answers,
        template=query_template.read_text(encoding="utf-8"),
    )
    _write_generated_query(query_file, query_text)

    source_export = _resolve_comment_export(config, query_file=query_file, query_url=query_url)
    raw_export = _copy_raw_comment_export(
        source_export,
        root=root,
        target_stem=raw_target_stem,
    )
    raw_hash = sha256_file(raw_export)
    _write_hash_manifest(raw_export.with_name(f"{raw_export.name}.sha256"), [raw_export])

    export = read_table(raw_export, name="sede_comment_export")
    issues = validate_sede_comment_export(export, questions=questions, answers=answers)
    normalized_comments = normalize_sede_comment_export(export) if not issues else None
    coverage = _comment_coverage(normalized_comments, answers) if normalized_comments else {}
    if issues:
        issue_payload = [issue.__dict__ for issue in issues]
        _upsert_comment_audit(
            audit_path,
            section=_build_comment_audit_section(
                site_name=site_name,
                query_file=query_file,
                raw_export=raw_export,
                provenance_path=provenance_path,
                processed_dir=None,
                derived_dir=None,
                raw_hash=raw_hash,
                comments=0,
                coverage={},
                issues=issue_payload,
                root=root,
                decision="revise_sede_query",
            ),
        )
        return SedeCommentResult(
            ok=False,
            query_file=query_file,
            raw_export=raw_export,
            provenance=provenance_path,
            processed_dir=None,
            derived_dir=None,
            audit=audit_path,
            comments=0,
            covered_questions=0,
            covered_answer_posts=0,
            issues=issue_payload,
        )

    assert normalized_comments is not None
    processed_dir = (
        root
        / "data/processed/stackexchange-difficulty"
        / f"pilot-{artifact_slug}-{config.pilot_date}-comment-enriched"
    )
    derived_dir = (
        root
        / "data/processed/stackexchange-difficulty"
        / f"pilot-{artifact_slug}-{config.pilot_date}-comment-enriched-derived"
    )
    processed_dir.mkdir(parents=True, exist_ok=True)
    derived_dir.mkdir(parents=True, exist_ok=True)

    provenance = _build_comment_provenance(
        pilot_date=config.pilot_date,
        site_slug=site_slug,
        site_name=site_name,
        pilot_slug=pilot_slug,
        artifact_slug=artifact_slug,
        query_url=query_url,
        query_template=query_template,
        query_file=query_file,
        raw_export=raw_export,
        raw_hash=raw_hash,
        root=root,
    )
    report = validate_dataset(
        questions,
        answers=answers,
        comments=normalized_comments,
        provenance=provenance,
    )
    write_validation_report(report, processed_dir / "validation_report.json")
    if not report.ok:
        issue_payload = [issue.__dict__ for issue in report.issues]
        _upsert_comment_audit(
            audit_path,
            section=_build_comment_audit_section(
                site_name=site_name,
                query_file=query_file,
                raw_export=raw_export,
                provenance_path=provenance_path,
                processed_dir=processed_dir,
                derived_dir=None,
                raw_hash=raw_hash,
                comments=len(normalized_comments.rows),
                coverage=coverage,
                issues=issue_payload,
                root=root,
                decision="revise_sede_query",
            ),
        )
        return SedeCommentResult(
            ok=False,
            query_file=query_file,
            raw_export=raw_export,
            provenance=provenance_path,
            processed_dir=processed_dir,
            derived_dir=None,
            audit=audit_path,
            comments=len(normalized_comments.rows),
            covered_questions=int(coverage.get("covered_questions", 0)),
            covered_answer_posts=int(coverage.get("covered_answer_posts", 0)),
            issues=issue_payload,
        )

    _write_tsv(questions.rows, processed_dir / "questions.tsv", list(questions.columns))
    _write_tsv(answers.rows, processed_dir / "answers.tsv", list(answers.columns))
    _write_tsv(
        normalized_comments.rows,
        processed_dir / "comments.tsv",
        list(normalized_comments.columns),
    )
    write_provenance_json(provenance, processed_dir / "provenance.json")
    processed_manifest = processed_dir / "processed-output.sha256"
    _write_hash_manifest(
        processed_manifest,
        [
            processed_dir / "questions.tsv",
            processed_dir / "answers.tsv",
            processed_dir / "comments.tsv",
            processed_dir / "validation_report.json",
        ],
    )
    finalized = finalize_processed_hashes(provenance, processed_manifest)
    finalized["processed_hash_manifest"] = _display_path(processed_manifest, root)
    write_provenance_json(finalized, provenance_path)
    write_provenance_json(finalized, processed_dir / "provenance.json")

    finalized_report = validate_dataset(
        questions,
        answers=answers,
        comments=normalized_comments,
        provenance=finalized,
    )
    write_validation_report(finalized_report, derived_dir / "validation_report.json")
    if not finalized_report.ok:
        issue_payload = [issue.__dict__ for issue in finalized_report.issues]
        _upsert_comment_audit(
            audit_path,
            section=_build_comment_audit_section(
                site_name=site_name,
                query_file=query_file,
                raw_export=raw_export,
                provenance_path=provenance_path,
                processed_dir=processed_dir,
                derived_dir=derived_dir,
                raw_hash=raw_hash,
                comments=len(normalized_comments.rows),
                coverage=coverage,
                issues=issue_payload,
                root=root,
                decision="revise_sede_query",
            ),
        )
        return SedeCommentResult(
            ok=False,
            query_file=query_file,
            raw_export=raw_export,
            provenance=provenance_path,
            processed_dir=processed_dir,
            derived_dir=derived_dir,
            audit=audit_path,
            comments=len(normalized_comments.rows),
            covered_questions=int(coverage.get("covered_questions", 0)),
            covered_answer_posts=int(coverage.get("covered_answer_posts", 0)),
            issues=issue_payload,
        )

    indicators = derive_indicators(questions, answers=answers, comments=normalized_comments)
    _write_tsv(
        indicators,
        derived_dir / "derived_thread_indicators.tsv",
        list(indicators[0]) if indicators else [],
    )
    threads = build_threads(
        questions,
        answers=answers,
        comments=normalized_comments,
        indicators=indicators,
        provenance=finalized,
    )
    write_jsonl(threads, derived_dir / "threads.jsonl")
    _write_hash_manifest(
        derived_dir / "derived-output.sha256",
        [
            derived_dir / "derived_thread_indicators.tsv",
            derived_dir / "threads.jsonl",
            derived_dir / "validation_report.json",
        ],
    )

    _upsert_comment_audit(
        audit_path,
        section=_build_comment_audit_section(
            site_name=site_name,
            query_file=query_file,
            raw_export=raw_export,
            provenance_path=provenance_path,
            processed_dir=processed_dir,
            derived_dir=derived_dir,
            raw_hash=raw_hash,
            comments=len(normalized_comments.rows),
            coverage=coverage,
            issues=[],
            root=root,
            decision="needs_more_comment_coverage",
        ),
    )
    return SedeCommentResult(
        ok=True,
        query_file=query_file,
        raw_export=raw_export,
        provenance=provenance_path,
        processed_dir=processed_dir,
        derived_dir=derived_dir,
        audit=audit_path,
        comments=len(normalized_comments.rows),
        covered_questions=int(coverage.get("covered_questions", 0)),
        covered_answer_posts=int(coverage.get("covered_answer_posts", 0)),
        issues=[],
    )


def render_comment_query(*, questions: Table, answers: Table, template: str) -> str:
    question_values = _sql_values(
        [(str(row["question_id"]).strip(),) for row in questions.rows],
        columns=1,
    )
    answer_rows = []
    for row in answers.rows:
        answer_id = str(row.get("answer_id", "")).strip()
        question_id = str(row.get("question_id", "")).strip()
        if answer_id and question_id:
            answer_rows.append((answer_id, question_id))
    answer_values = _sql_values(answer_rows, columns=2)
    return template.format(
        question_values=question_values,
        answer_values=answer_values,
    )


def validate_sede_comment_export(
    table: Table,
    *,
    questions: Table,
    answers: Table,
) -> list[ValidationIssue]:
    issues = validate_required_columns(table, SEDE_COMMENT_REQUIRED_COLUMNS)
    if issues:
        return issues

    question_ids = {str(row["question_id"]).strip() for row in questions.rows}
    answer_ids = {str(row["answer_id"]).strip() for row in answers.rows}
    valid_post_ids = question_ids | answer_ids
    expected_comment_threads = {
        str(row["question_id"]).strip()
        for row in questions.rows
        if _to_int(row.get("comment_count")) > 0
    }
    seen_comments: set[str] = set()

    for row in table.rows:
        comment_id = _clean(row.get("comment_id"))
        question_id = _clean(row.get("question_id"))
        post_id = _clean(row.get("post_id"))
        post_type_id = _clean(row.get("post_type_id"))
        if not comment_id:
            issues.append(ValidationIssue("missing_comment_id", "Comment row has no comment_id."))
        elif comment_id in seen_comments:
            issues.append(
                ValidationIssue(
                    "duplicate_comment_id",
                    f"Duplicate comment_id: {comment_id}",
                    row_id=comment_id,
                )
            )
        seen_comments.add(comment_id)
        if question_id not in question_ids:
            issues.append(
                ValidationIssue(
                    "comment_question_missing",
                    f"Comment {comment_id} points to missing question_id {question_id}.",
                    row_id=comment_id or None,
                )
            )
        if post_id not in valid_post_ids:
            issues.append(
                ValidationIssue(
                    "comment_post_missing",
                    f"Comment {comment_id} points to missing post_id {post_id}.",
                    row_id=comment_id or None,
                )
            )
        if post_type_id not in COMMENT_POST_TYPES:
            issues.append(
                ValidationIssue(
                    "comment_post_type_unsupported",
                    f"Comment {comment_id} has unsupported post_type_id {post_type_id}.",
                    row_id=comment_id or None,
                )
            )

    if not table.rows and expected_comment_threads:
        issues.append(
            ValidationIssue(
                "comment_export_empty",
                (
                    "Comment export is empty although the pilot question table "
                    "contains nonzero comment_count values."
                ),
            )
        )
    return issues


def normalize_sede_comment_export(table: Table) -> Table:
    rows = [
        {
            "comment_id": _clean(row.get("comment_id")),
            "post_id": _clean(row.get("post_id")),
            "question_id": _clean(row.get("question_id")),
            "post_type_id": _clean(row.get("post_type_id")),
            "text": _clean(row.get("text")),
            "score": _clean(row.get("score")),
            "creation_date": _clean(row.get("creation_date")),
            "content_license": _clean(row.get("content_license")),
        }
        for row in table.rows
    ]
    return Table(name="comments", rows=rows, columns=SEDE_COMMENT_REQUIRED_COLUMNS)


def resolve_download_dir(value: str | Path | None) -> Path:
    if value is None:
        value = "auto"
    if str(value) != "auto":
        return Path(value).expanduser()

    candidates = _xdg_download_candidates()
    home = Path.home()
    candidates.extend(home / name for name in DOWNLOAD_DIR_NAMES)
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    names = ", ".join(str(candidate) for candidate in candidates)
    raise SedeCommentError(f"no download directory found; checked: {names}")


def _resolve_comment_export(
    config: SedeCommentConfig,
    *,
    query_file: Path,
    query_url: str,
) -> Path:
    if config.export_path:
        return config.export_path
    if not config.open_browser:
        raise SedeCommentError("run-sede-comment-enrichment requires --export or --open-browser")
    prepare_browser_session(query_url=query_url)
    print(f"SEDE comment query file: {query_file}")
    print("Paste the SQL from that file into the SEDE editor after the page opens.")
    print(f"Opened SEDE query page: {query_url}")
    download_dir = resolve_download_dir(config.download_dir)
    return wait_for_sede_export(
        download_dir,
        start_time=time.time(),
        timeout_seconds=config.timeout_seconds,
    )


def _resolve_template(root: Path, query_template: Path | None) -> Path:
    template = query_template or DEFAULT_COMMENT_QUERY_TEMPLATE
    path = template if template.is_absolute() else root / template
    path = path.resolve()
    if not path.is_file():
        raise SedeCommentError(f"SEDE comment query template does not exist: {path}")
    return path


def _build_context(root: Path, artifact_slug: str, pilot_date: str) -> dict[str, Path]:
    work_dir = (
        root
        / "data/processed/stackexchange-difficulty"
        / f"pilot-{artifact_slug}-{pilot_date}-comment-enrichment"
    )
    work_dir.mkdir(parents=True, exist_ok=True)
    return {"query_file": work_dir / "sede_comments_query.sql"}


def _copy_raw_comment_export(source_export: Path, *, root: Path, target_stem: str) -> Path:
    source = source_export.resolve()
    if source.suffix.lower() not in SUPPORTED_EXPORT_SUFFIXES:
        raise SedeCommentError("SEDE comment export must use a .csv or .tsv suffix")
    target = (
        root
        / "data/raw/stackexchange-difficulty"
        / f"{target_stem}{source.suffix.lower()}"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    if source == target.resolve():
        return target
    if target.exists():
        raise SedeCommentError(f"raw comment export already exists: {target}")
    shutil.copy2(source, target)
    return target


def _write_generated_query(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SedeCommentError(
            f"generated comment query already exists with different text: {path}"
        )
    path.write_text(text, encoding="utf-8")


def _build_comment_provenance(
    *,
    pilot_date: str,
    site_slug: str,
    site_name: str,
    pilot_slug: str | None,
    artifact_slug: str,
    query_url: str,
    query_template: Path,
    query_file: Path,
    raw_export: Path,
    raw_hash: str,
    root: Path,
) -> dict[str, Any]:
    return {
        "dataset_name": "stackexchange-difficulty",
        "dataset_version": f"sede-comments-{artifact_slug}-{pilot_date}",
        "source_method": "sede_comment_export",
        "source_version": "SEDE snapshot visible at export time",
        "source_site_slug": site_slug,
        "source_site_name": site_name,
        **({"pilot_slug": pilot_slug} if pilot_slug else {}),
        "query_url": query_url,
        "query_or_dump_file": _display_path(query_template, root),
        "generated_query_file": _display_path(query_file, root),
        "export_identifier": _display_path(raw_export, root),
        "access_date": pilot_date,
        "official_source_checked_at": pilot_date,
        "license": "CC BY-SA, version determined by each exported comment ContentLicense",
        "transformation_steps": [
            f"generated ID-locked {site_name} comment query from existing pilot IDs",
            f"exported {site_name} comments manually through SEDE",
            "stored raw comment export unchanged under data/raw/stackexchange-difficulty/",
            "validated comment IDs, question IDs, post IDs, and provenance",
            "created a comment-enriched processed dataset without overwriting the pilot",
            "derived thread indicators and JSONL from finalized provenance",
            "updated tracked audit with aggregate comment counts only",
        ],
        "raw_export_hash": f"sha256:{raw_hash}",
        "processed_output_hash": "sha256:pending-before-processing",
        "output_hash": "sha256:pending-before-processing",
    }


def _comment_coverage(comments: Table | None, answers: Table) -> dict[str, int]:
    if comments is None:
        return {"covered_questions": 0, "covered_answer_posts": 0}
    answer_ids = {str(row["answer_id"]).strip() for row in answers.rows}
    covered_questions = {
        str(row.get("question_id", "")).strip()
        for row in comments.rows
        if str(row.get("question_id", "")).strip()
    }
    covered_answer_posts = {
        str(row.get("post_id", "")).strip()
        for row in comments.rows
        if str(row.get("post_id", "")).strip() in answer_ids
    }
    return {
        "covered_questions": len(covered_questions),
        "covered_answer_posts": len(covered_answer_posts),
    }


def _build_comment_audit_section(
    *,
    site_name: str,
    query_file: Path,
    raw_export: Path,
    provenance_path: Path,
    processed_dir: Path | None,
    derived_dir: Path | None,
    raw_hash: str,
    comments: int,
    coverage: dict[str, int],
    issues: list[dict[str, Any]],
    root: Path,
    decision: str,
) -> str:
    issue_counts = Counter(issue["code"] for issue in issues)
    return "\n".join(
        [
            "## Comment Enrichment",
            "",
            f"- Source: {site_name} SEDE comment export.",
            f"- Generated query file: `{_display_path(query_file, root)}`.",
            f"- Raw comment export: `{_display_path(raw_export, root)}`.",
            f"- Comment provenance file: `{_display_path(provenance_path, root)}`.",
            f"- Raw comment export hash: `sha256:{raw_hash}`.",
            f"- Comment rows: {comments}.",
            f"- Covered questions: {coverage.get('covered_questions', 0)}.",
            f"- Covered included answer posts: {coverage.get('covered_answer_posts', 0)}.",
            f"- Validation issues: {_format_counter(issue_counts) if issues else 'none'}.",
            "- Processed output: "
            f"`{_display_path(processed_dir, root) if processed_dir else 'not produced'}`.",
            "- Derived output: "
            f"`{_display_path(derived_dir, root) if derived_dir else 'not produced'}`.",
            "- Content-safety status: aggregate audit only; no copied titles, bodies, "
            "answers, comments, code snippets, URLs, usernames, or credentials.",
            "",
            "## Comment-Enriched LLM Reinspection",
            "",
            "- Status: pending. Reinspect ignored local records previously labeled "
            "`needs_comments=yes` before making the scaling decision.",
            "- Allowed final decisions after reinspection: `ready_for_data_dump_design`, "
            "`needs_more_comment_coverage`, or `revise_sede_query`.",
            "",
            "## Comment-Enriched Decision",
            "",
            f"- Decision: {decision}.",
            "",
        ]
    )


def _upsert_comment_audit(audit_path: Path, *, section: str) -> None:
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    if audit_path.exists():
        text = audit_path.read_text(encoding="utf-8")
    else:
        text = "# SEDE Pilot Audit\n\n"
    pattern = re.compile(
        r"\n## Comment Enrichment\n.*?(?=\n## Decision\n|\Z)",
        flags=re.DOTALL,
    )
    replacement = "\n" + section
    if pattern.search(text):
        updated = pattern.sub(replacement, text)
    elif "\n## Decision\n" in text:
        updated = text.replace("\n## Decision\n", replacement + "\n## Decision\n", 1)
    else:
        updated = text.rstrip() + "\n\n" + section
    audit_path.write_text(updated, encoding="utf-8")


def _write_hash_manifest(path: Path, files: list[Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{sha256_file(file_path)}  {file_path}\n" for file_path in files]
    path.write_text("".join(lines), encoding="utf-8")


def _write_tsv(rows: list[dict[str, Any]], path: Path, fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _sql_values(rows: list[tuple[str, ...]], *, columns: int) -> str:
    if not rows:
        nulls = ", ".join("CAST(NULL AS int)" for _ in range(columns))
        return f"({nulls})"
    normalized = sorted({tuple(_sql_int(value) for value in row) for row in rows})
    return ",\n        ".join(f"({', '.join(row)})" for row in normalized)


def _sql_int(value: str) -> str:
    text = str(value).strip()
    if not text.isdigit():
        raise SedeCommentError(f"post IDs in generated comment query must be numeric: {text}")
    return text


def _xdg_download_candidates() -> list[Path]:
    candidates: list[Path] = []
    env_path = os.environ.get("XDG_DOWNLOAD_DIR")
    if env_path:
        candidates.append(Path(os.path.expandvars(env_path)).expanduser())
    config = Path.home() / ".config/user-dirs.dirs"
    if config.is_file():
        match = re.search(
            r'^XDG_DOWNLOAD_DIR="?([^"\n]+)"?',
            config.read_text(encoding="utf-8", errors="ignore"),
            flags=re.MULTILINE,
        )
        if match:
            candidates.append(Path(os.path.expandvars(match.group(1))).expanduser())
    return candidates


def _resolve_source_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def _display_path(path: Path | None, root: Path) -> str:
    if path is None:
        return "not produced"
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _name_from_slug(site_slug: str) -> str:
    known_names = {
        "math": "Mathematics",
        "stackoverflow": "Stack Overflow",
        "stats": "Cross Validated",
    }
    return known_names.get(
        site_slug,
        " ".join(part.capitalize() for part in site_slug.split("-")),
    )


def _format_counter(counter: Counter[str]) -> str:
    if not counter:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(counter.items()))


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _to_int(value: Any) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0
