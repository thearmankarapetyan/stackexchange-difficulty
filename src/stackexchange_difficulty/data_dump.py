"""Local Stack Exchange Data Dump pilot parsing workflow."""

from __future__ import annotations

import csv
import random
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from stackexchange_difficulty.derive import derive_indicators, elapsed_hours, parse_datetime
from stackexchange_difficulty.jsonl import build_threads, write_jsonl
from stackexchange_difficulty.provenance import (
    finalize_processed_hashes,
    load_provenance,
    sha256_file,
    write_provenance_json,
)
from stackexchange_difficulty.schema import (
    ANSWER_REQUIRED_COLUMNS,
    ARTIFICIAL_POST_IDS,
    COMMENT_REQUIRED_COLUMNS,
    DERIVED_COLUMNS,
    DUPLICATE_LINK_TYPE_ID,
    POST_HISTORY_COLUMNS,
    POST_LINK_COLUMNS,
    QUESTION_REQUIRED_COLUMNS,
    TAG_COLUMNS,
)
from stackexchange_difficulty.sede_pilot import (
    SedePilotError,
    normalize_pilot_slug,
    normalize_site_slug,
)
from stackexchange_difficulty.validation import Table, validate_dataset, write_validation_report

ANSWERABLE_PILOT_PROFILE = "answerable_pilot"
ANSWERABLE_CLEAN_PROFILE = "answerable_clean"
SUPPORTED_SAMPLE_PROFILES = {ANSWERABLE_PILOT_PROFILE, ANSWERABLE_CLEAN_PROFILE}
ANSWERABLE_PROFILES = {ANSWERABLE_PILOT_PROFILE, ANSWERABLE_CLEAN_PROFILE}
DEFAULT_SAMPLE_SEED = 20260513
DATA_DUMP_FILES = ("Posts.xml", "PostLinks.xml", "Comments.xml", "Tags.xml", "PostHistory.xml")


class DataDumpError(RuntimeError):
    """Raised when a local Data Dump workflow cannot continue safely."""


@dataclass(frozen=True)
class DataDumpPreflightConfig:
    project_root: Path
    dump_dir: Path
    site_slug: str
    site_name: str
    dump_date: str
    sample_profile: str = "answerable_pilot"
    include_post_history: bool = False


@dataclass(frozen=True)
class DataDumpPilotConfig(DataDumpPreflightConfig):
    pilot_slug: str = "math-answerable"
    sample_size: int = 5000
    sample_seed: int = DEFAULT_SAMPLE_SEED


@dataclass(frozen=True)
class DataDumpPreflightResult:
    ok: bool
    dump_dir: Path
    site_slug: str
    site_name: str
    dump_date: str
    sample_profile: str
    files: dict[str, dict[str, Any]]
    raw_file_hashes: dict[str, str]
    issues: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "dump_dir": str(self.dump_dir),
            "site_slug": self.site_slug,
            "site_name": self.site_name,
            "dump_date": self.dump_date,
            "sample_profile": self.sample_profile,
            "files": self.files,
            "raw_file_hashes": self.raw_file_hashes,
            "issues": self.issues,
            "warnings": self.warnings,
        }


@dataclass(frozen=True)
class DataDumpPilotResult:
    ok: bool
    decision: str
    processed_dir: Path | None
    derived_dir: Path | None
    audit: Path
    provenance: Path
    selected_questions: int
    issues: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "decision": self.decision,
            "processed_dir": str(self.processed_dir) if self.processed_dir else None,
            "derived_dir": str(self.derived_dir) if self.derived_dir else None,
            "audit": str(self.audit),
            "provenance": str(self.provenance),
            "selected_questions": self.selected_questions,
            "issues": self.issues,
            "warnings": self.warnings,
        }


@dataclass(frozen=True)
class QuestionCandidate:
    question_id: str
    accepted_answer_id: str
    tags: str
    creation_date: str
    score: int
    view_count: int
    answer_count: int
    comment_count: int
    closed_date: str
    is_duplicate: bool
    first_answer_creation_date: str
    stratum: tuple[str, str, str, str, str, str]


@dataclass(frozen=True)
class AnswerMeta:
    answer_id: str
    question_id: str
    creation_date: str


@dataclass
class SelectionResult:
    selected_ids: set[str]
    selected_candidates: list[QuestionCandidate]
    excluded_counts: Counter[str]
    total_questions: int
    eligible_questions: int
    decision: str = "data_dump_parser_validated"
    issues: list[dict[str, Any]] = field(default_factory=list)


def iter_xml_rows(path: Path) -> Iterator[dict[str, str]]:
    """Yield Stack Exchange Data Dump row attributes without loading the full tree."""
    try:
        for _event, elem in ET.iterparse(path, events=("end",)):
            if elem.tag == "row":
                yield {str(key): str(value) for key, value in elem.attrib.items()}
            elem.clear()
    except ET.ParseError as exc:
        raise DataDumpError(f"XML parse failed for {path}: {exc}") from exc


def preflight_dump(config: DataDumpPreflightConfig) -> DataDumpPreflightResult:
    site_slug = _normalize_site_slug(config.site_slug)
    sample_profile = _validate_sample_profile(config.sample_profile)
    _validate_dump_date(config.dump_date)
    dump_dir = config.dump_dir
    issues: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    files: dict[str, dict[str, Any]] = {}
    raw_hashes: dict[str, str] = {}

    if not dump_dir.is_dir():
        issues.append(_issue("dump_dir_missing", f"dump directory does not exist: {dump_dir}"))

    for filename in DATA_DUMP_FILES:
        path = dump_dir / filename
        required = _is_required_file(
            filename,
            sample_profile=sample_profile,
            include_post_history=config.include_post_history,
        )
        entry: dict[str, Any] = {"present": path.is_file(), "required": required}
        if not path.is_file():
            if required:
                code = (
                    "missing_postlinks_for_answerable_pilot"
                    if filename == "PostLinks.xml"
                    else "missing_required_dump_file"
                )
                issues.append(_issue(code, f"required Data Dump file is missing: {filename}"))
            else:
                warnings.append(
                    _issue("missing_optional_dump_file", f"optional file missing: {filename}")
                )
            files[filename] = entry
            continue

        if filename == "PostHistory.xml" and not config.include_post_history:
            entry["skipped"] = True
            entry["reason"] = "post history not requested"
            files[filename] = entry
            continue

        digest = sha256_file(path)
        row_count = _xml_row_count(path)
        entry["sha256"] = f"sha256:{digest}"
        entry["rows"] = row_count
        raw_hashes[filename] = f"sha256:{digest}"
        files[filename] = entry

    return DataDumpPreflightResult(
        ok=not issues,
        dump_dir=dump_dir,
        site_slug=site_slug,
        site_name=config.site_name,
        dump_date=config.dump_date,
        sample_profile=sample_profile,
        files=files,
        raw_file_hashes=raw_hashes,
        issues=issues,
        warnings=warnings,
    )


def run_data_dump_pilot(config: DataDumpPilotConfig) -> DataDumpPilotResult:
    root = config.project_root.resolve()
    _normalize_site_slug(config.site_slug)
    pilot_slug = _normalize_pilot_slug(config.pilot_slug)
    _validate_sample_profile(config.sample_profile)
    _validate_dump_date(config.dump_date)
    if config.sample_size < 1:
        raise DataDumpError("sample size must be at least 1")

    artifact_slug = pilot_slug
    report_slug = artifact_slug.replace("-", "_")
    processed_dir = (
        root / f"data/processed/stackexchange-difficulty/dump-{artifact_slug}-{config.dump_date}"
    )
    derived_dir = (
        root
        / f"data/processed/stackexchange-difficulty/dump-{artifact_slug}-{config.dump_date}-derived"
    )
    audit_path = (
        root
        / "reports/datasets/stackexchange-difficulty/audits"
        / f"data_dump_{report_slug}_{config.dump_date}.md"
    )
    provenance_path = (
        root
        / "reports/datasets/stackexchange-difficulty"
        / f"provenance_data_dump_{report_slug}_{config.dump_date}.json"
    )
    _fail_if_exists(processed_dir, derived_dir, audit_path, provenance_path)

    preflight = preflight_dump(config)
    if not preflight.ok:
        decision = (
            "data_dump_duplicate_filter_incomplete"
            if any(
                issue["code"] == "missing_postlinks_for_answerable_pilot"
                for issue in preflight.issues
            )
            else "data_dump_preflight_failed"
        )
        _write_audit(
            audit_path,
            _build_audit(
                config=config,
                preflight=preflight,
                selection=None,
                validation_report=None,
                processed_dir=None,
                derived_dir=None,
                root=root,
                decision=decision,
            ),
        )
        return DataDumpPilotResult(
            ok=False,
            decision=decision,
            processed_dir=None,
            derived_dir=None,
            audit=audit_path,
            provenance=provenance_path,
            selected_questions=0,
            issues=preflight.issues,
            warnings=preflight.warnings,
        )

    selection = _select_questions(config, preflight)
    if selection.decision != "data_dump_parser_validated":
        _write_audit(
            audit_path,
            _build_audit(
                config=config,
                preflight=preflight,
                selection=selection,
                validation_report=None,
                processed_dir=None,
                derived_dir=None,
                root=root,
                decision=selection.decision,
            ),
        )
        return DataDumpPilotResult(
            ok=False,
            decision=selection.decision,
            processed_dir=None,
            derived_dir=None,
            audit=audit_path,
            provenance=provenance_path,
            selected_questions=len(selection.selected_ids),
            issues=selection.issues,
            warnings=preflight.warnings,
        )

    processed_dir.mkdir(parents=True)
    derived_dir.mkdir(parents=True)
    tables = _write_selected_outputs(config, selection, processed_dir)
    provenance = _build_provenance(config, preflight, root=root)
    write_provenance_json(provenance, provenance_path)
    write_provenance_json(provenance, processed_dir / "provenance.json")

    validation_report = validate_dataset(
        tables["questions"],
        answers=tables["answers"],
        comments=tables["comments"],
        provenance=provenance,
    )
    write_validation_report(validation_report, processed_dir / "validation_report.json")
    if not validation_report.ok:
        decision = "data_dump_validation_failed"
        _write_audit(
            audit_path,
            _build_audit(
                config=config,
                preflight=preflight,
                selection=selection,
                validation_report=validation_report.to_dict(),
                processed_dir=processed_dir,
                derived_dir=None,
                root=root,
                decision=decision,
            ),
        )
        return DataDumpPilotResult(
            ok=False,
            decision=decision,
            processed_dir=processed_dir,
            derived_dir=None,
            audit=audit_path,
            provenance=provenance_path,
            selected_questions=len(selection.selected_ids),
            issues=[issue.__dict__ for issue in validation_report.issues],
            warnings=preflight.warnings,
        )

    processed_manifest = processed_dir / "processed-output.sha256"
    _write_hash_manifest(processed_manifest, _processed_hash_files(processed_dir))
    finalized = finalize_processed_hashes(provenance, processed_manifest)
    finalized["processed_hash_manifest"] = _display_path(processed_manifest, root)
    write_provenance_json(finalized, provenance_path)
    write_provenance_json(finalized, processed_dir / "provenance.json")

    finalized_report = validate_dataset(
        tables["questions"],
        answers=tables["answers"],
        comments=tables["comments"],
        provenance=finalized,
    )
    write_validation_report(finalized_report, derived_dir / "validation_report.json")
    if not finalized_report.ok:
        decision = "data_dump_validation_failed"
        _write_audit(
            audit_path,
            _build_audit(
                config=config,
                preflight=preflight,
                selection=selection,
                validation_report=finalized_report.to_dict(),
                processed_dir=processed_dir,
                derived_dir=derived_dir,
                root=root,
                decision=decision,
            ),
        )
        return DataDumpPilotResult(
            ok=False,
            decision=decision,
            processed_dir=processed_dir,
            derived_dir=derived_dir,
            audit=audit_path,
            provenance=provenance_path,
            selected_questions=len(selection.selected_ids),
            issues=[issue.__dict__ for issue in finalized_report.issues],
            warnings=preflight.warnings,
        )

    indicators = derive_indicators(
        tables["questions"],
        answers=tables["answers"],
        comments=tables["comments"],
    )
    _write_tsv(indicators, derived_dir / "derived_thread_indicators.tsv", list(DERIVED_COLUMNS))
    threads = build_threads(
        tables["questions"],
        answers=tables["answers"],
        comments=tables["comments"],
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

    decision = "data_dump_parser_validated"
    _write_audit(
        audit_path,
        _build_audit(
            config=config,
            preflight=preflight,
            selection=selection,
            validation_report=finalized_report.to_dict(),
            processed_dir=processed_dir,
            derived_dir=derived_dir,
            root=root,
            decision=decision,
            derived_rows=indicators,
        ),
    )
    return DataDumpPilotResult(
        ok=True,
        decision=decision,
        processed_dir=processed_dir,
        derived_dir=derived_dir,
        audit=audit_path,
        provenance=provenance_path,
        selected_questions=len(selection.selected_ids),
        issues=[],
        warnings=preflight.warnings,
    )


def _select_questions(
    config: DataDumpPilotConfig,
    preflight: DataDumpPreflightResult,
) -> SelectionResult:
    dump_dir = config.dump_dir
    duplicate_ids = _duplicate_question_ids(dump_dir / "PostLinks.xml")
    minimal_candidates: dict[str, dict[str, str]] = {}
    accepted_ids: set[str] = set()
    excluded = Counter()
    total_questions = 0

    for row in iter_xml_rows(dump_dir / "Posts.xml"):
        if row.get("PostTypeId") != "1":
            continue
        total_questions += 1
        question_id = _clean(row.get("Id"))
        if question_id in ARTIFICIAL_POST_IDS:
            excluded["artificial_post_id"] += 1
            continue
        accepted_id = _clean(row.get("AcceptedAnswerId"))
        minimal_candidates[question_id] = {
            "question_id": question_id,
            "accepted_answer_id": accepted_id,
            "tags": _clean(row.get("Tags")),
            "creation_date": _clean(row.get("CreationDate")),
            "score": _clean(row.get("Score")),
            "view_count": _clean(row.get("ViewCount")),
            "answer_count": _clean(row.get("AnswerCount")),
            "comment_count": _clean(row.get("CommentCount")),
            "closed_date": _clean(row.get("ClosedDate")),
        }
        if accepted_id:
            accepted_ids.add(accepted_id)

    candidate_ids = set(minimal_candidates)
    answer_by_id: dict[str, AnswerMeta] = {}
    answer_counts = Counter()
    first_answer_by_question: dict[str, AnswerMeta] = {}
    for row in iter_xml_rows(dump_dir / "Posts.xml"):
        if row.get("PostTypeId") != "2":
            continue
        answer_id = _clean(row.get("Id"))
        parent_id = _clean(row.get("ParentId"))
        if answer_id not in accepted_ids and parent_id not in candidate_ids:
            continue
        meta = AnswerMeta(
            answer_id=answer_id,
            question_id=parent_id,
            creation_date=_clean(row.get("CreationDate")),
        )
        if answer_id in accepted_ids:
            answer_by_id[answer_id] = meta
        if parent_id in candidate_ids:
            answer_counts[parent_id] += 1
            previous = first_answer_by_question.get(parent_id)
            if previous is None or _sort_datetime(meta.creation_date) < _sort_datetime(
                previous.creation_date
            ):
                first_answer_by_question[parent_id] = meta

    eligible: list[QuestionCandidate] = []
    for question_id, row in sorted(minimal_candidates.items()):
        accepted_id = row["accepted_answer_id"]
        if row["closed_date"]:
            excluded["closed_question"] += 1
            continue
        if _int(row["answer_count"]) <= 0 or answer_counts[question_id] == 0:
            excluded["unanswered_question"] += 1
            continue
        if not accepted_id:
            excluded["no_accepted_answer"] += 1
            continue
        accepted = answer_by_id.get(accepted_id)
        if accepted is None:
            excluded["accepted_answer_missing"] += 1
            continue
        if accepted.question_id != question_id:
            excluded["accepted_answer_parent_mismatch"] += 1
            continue
        if question_id in duplicate_ids:
            excluded["duplicate_question"] += 1
            continue
        first_answer = first_answer_by_question.get(question_id)
        if config.sample_profile == ANSWERABLE_CLEAN_PROFILE:
            clean_exclusion = _clean_profile_exclusion(row, first_answer)
            if clean_exclusion:
                excluded[clean_exclusion] += 1
                continue
        eligible.append(
            _candidate_from_row(
                row,
                is_duplicate=False,
                first_answer_creation_date=first_answer.creation_date if first_answer else "",
            )
        )

    if len(eligible) < config.sample_size:
        return SelectionResult(
            selected_ids=set(),
            selected_candidates=[],
            excluded_counts=excluded,
            total_questions=total_questions,
            eligible_questions=len(eligible),
            decision="data_dump_sampling_failed",
            issues=[
                _issue(
                    "sample_size_unavailable",
                    (
                        f"eligible Data Dump questions {len(eligible)} are fewer than "
                        f"requested sample size {config.sample_size}"
                    ),
                )
            ],
        )

    selected = _stratified_sample(eligible, sample_size=config.sample_size, seed=config.sample_seed)
    return SelectionResult(
        selected_ids={candidate.question_id for candidate in selected},
        selected_candidates=selected,
        excluded_counts=excluded,
        total_questions=total_questions,
        eligible_questions=len(eligible),
    )


def _write_selected_outputs(
    config: DataDumpPilotConfig,
    selection: SelectionResult,
    processed_dir: Path,
) -> dict[str, Table]:
    selected_question_ids = selection.selected_ids
    accepted_by_question = {
        candidate.question_id: candidate.accepted_answer_id
        for candidate in selection.selected_candidates
    }
    selected_answer_ids: set[str] = set()
    question_rows: list[dict[str, str]] = []
    answer_rows: list[dict[str, str]] = []

    for row in iter_xml_rows(config.dump_dir / "Posts.xml"):
        post_type = row.get("PostTypeId")
        post_id = _clean(row.get("Id"))
        if post_type == "1" and post_id in selected_question_ids:
            question_rows.append(
                {
                    "question_id": post_id,
                    "title": _clean(row.get("Title")),
                    "body_html": _clean(row.get("Body")),
                    "tags": _clean(row.get("Tags")),
                    "creation_date": _clean(row.get("CreationDate")),
                    "score": _clean(row.get("Score")),
                    "view_count": _clean(row.get("ViewCount")),
                    "answer_count": _clean(row.get("AnswerCount")),
                    "comment_count": _clean(row.get("CommentCount")),
                    "closed_date": _clean(row.get("ClosedDate")),
                    "accepted_answer_id": _clean(row.get("AcceptedAnswerId")),
                    "is_duplicate": "false",
                    "content_license": _clean(row.get("ContentLicense")),
                }
            )
        elif post_type == "2":
            parent_id = _clean(row.get("ParentId"))
            if parent_id not in selected_question_ids:
                continue
            answer_id = post_id
            selected_answer_ids.add(answer_id)
            answer_rows.append(
                {
                    "answer_id": answer_id,
                    "question_id": parent_id,
                    "body_html": _clean(row.get("Body")),
                    "score": _clean(row.get("Score")),
                    "creation_date": _clean(row.get("CreationDate")),
                    "is_accepted": str(accepted_by_question.get(parent_id) == answer_id).lower(),
                }
            )

    comment_rows = _selected_comments(
        config.dump_dir / "Comments.xml",
        selected_question_ids,
        selected_answer_ids,
    )
    post_link_rows = _selected_post_links(config.dump_dir / "PostLinks.xml", selected_question_ids)
    tag_rows = _tag_rows(config.dump_dir / "Tags.xml")
    history_rows = (
        _selected_post_history(
            config.dump_dir / "PostHistory.xml",
            selected_question_ids | selected_answer_ids,
        )
        if config.include_post_history
        else []
    )

    question_rows.sort(key=lambda row: _int(row["question_id"]))
    answer_rows.sort(key=lambda row: (_int(row["question_id"]), _int(row["answer_id"])))
    comment_rows.sort(key=lambda row: _int(row["comment_id"]))

    _write_tsv(question_rows, processed_dir / "questions.tsv", list(QUESTION_REQUIRED_COLUMNS))
    _write_tsv(answer_rows, processed_dir / "answers.tsv", list(ANSWER_REQUIRED_COLUMNS))
    _write_tsv(
        comment_rows,
        processed_dir / "comments.tsv",
        [*COMMENT_REQUIRED_COLUMNS, "content_license"],
    )
    _write_tsv(post_link_rows, processed_dir / "post_links.tsv", list(POST_LINK_COLUMNS))
    if tag_rows:
        _write_tsv(tag_rows, processed_dir / "tags.tsv", list(TAG_COLUMNS))
    if config.include_post_history:
        _write_tsv(history_rows, processed_dir / "post_history.tsv", list(POST_HISTORY_COLUMNS))

    return {
        "questions": Table("questions", question_rows, QUESTION_REQUIRED_COLUMNS),
        "answers": Table("answers", answer_rows, ANSWER_REQUIRED_COLUMNS),
        "comments": Table("comments", comment_rows, (*COMMENT_REQUIRED_COLUMNS, "content_license")),
    }


def _selected_comments(
    path: Path,
    question_ids: set[str],
    answer_ids: set[str],
) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    valid_posts = question_ids | answer_ids
    rows: list[dict[str, str]] = []
    for row in iter_xml_rows(path):
        post_id = _clean(row.get("PostId"))
        if post_id not in valid_posts:
            continue
        rows.append(
            {
                "comment_id": _clean(row.get("Id")),
                "post_id": post_id,
                "text": _clean(row.get("Text")),
                "score": _clean(row.get("Score")),
                "creation_date": _clean(row.get("CreationDate")),
                "content_license": _clean(row.get("ContentLicense")),
            }
        )
    return rows


def _selected_post_links(path: Path, question_ids: set[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in iter_xml_rows(path):
        post_id = _clean(row.get("PostId"))
        if post_id not in question_ids:
            continue
        rows.append(
            {
                "post_link_id": _clean(row.get("Id")),
                "creation_date": _clean(row.get("CreationDate")),
                "post_id": post_id,
                "related_post_id": _clean(row.get("RelatedPostId")),
                "link_type_id": _clean(row.get("LinkTypeId")),
            }
        )
    return rows


def _tag_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    rows: list[dict[str, str]] = []
    for row in iter_xml_rows(path):
        rows.append(
            {
                "tag_id": _clean(row.get("Id")),
                "tag_name": _clean(row.get("TagName")),
                "count": _clean(row.get("Count")),
                "excerpt_post_id": _clean(row.get("ExcerptPostId")),
                "wiki_post_id": _clean(row.get("WikiPostId")),
            }
        )
    return rows


def _selected_post_history(path: Path, post_ids: set[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in iter_xml_rows(path):
        post_id = _clean(row.get("PostId"))
        if post_id not in post_ids:
            continue
        rows.append(
            {
                "post_history_id": _clean(row.get("Id")),
                "post_history_type_id": _clean(row.get("PostHistoryTypeId")),
                "post_id": post_id,
                "creation_date": _clean(row.get("CreationDate")),
                "comment": _clean(row.get("Comment")),
                "text": _clean(row.get("Text")),
                "content_license": _clean(row.get("ContentLicense")),
            }
        )
    return rows


def _duplicate_question_ids(path: Path) -> set[str]:
    duplicates: set[str] = set()
    for row in iter_xml_rows(path):
        if _clean(row.get("LinkTypeId")) == DUPLICATE_LINK_TYPE_ID:
            duplicates.add(_clean(row.get("PostId")))
    return duplicates


def _candidate_from_row(
    row: dict[str, str],
    *,
    is_duplicate: bool,
    first_answer_creation_date: str,
) -> QuestionCandidate:
    creation_date = row["creation_date"]
    score = _int(row["score"])
    view_count = _int(row["view_count"])
    comment_count = _int(row["comment_count"])
    latency = elapsed_hours(
        parse_datetime(creation_date),
        parse_datetime(first_answer_creation_date),
    )
    stratum = (
        _tag_family(row["tags"]),
        _time_period(creation_date),
        _answer_latency_bucket(latency),
        _score_bucket(score),
        _view_bucket(view_count),
        _comment_count_bucket(comment_count),
    )
    return QuestionCandidate(
        question_id=row["question_id"],
        accepted_answer_id=row["accepted_answer_id"],
        tags=row["tags"],
        creation_date=creation_date,
        score=score,
        view_count=view_count,
        answer_count=_int(row["answer_count"]),
        comment_count=comment_count,
        closed_date=row["closed_date"],
        is_duplicate=is_duplicate,
        first_answer_creation_date=first_answer_creation_date,
        stratum=stratum,
    )


def _clean_profile_exclusion(row: dict[str, str], first_answer: AnswerMeta | None) -> str | None:
    # Keep the first clean profile metadata-only so sampling can happen before
    # retaining titles, bodies, answers, comments, or post history.
    if _int(row["score"]) < 0:
        return "clean_negative_score"
    if not row["tags"]:
        return "clean_missing_tags"
    if first_answer is None or not first_answer.creation_date:
        return "clean_missing_first_answer_timing"
    latency = elapsed_hours(
        parse_datetime(row["creation_date"]),
        parse_datetime(first_answer.creation_date),
    )
    if latency is None:
        return "clean_missing_first_answer_timing"
    if latency > 168:
        return "clean_long_answer_latency"
    return None


def _stratified_sample(
    candidates: list[QuestionCandidate],
    *,
    sample_size: int,
    seed: int,
) -> list[QuestionCandidate]:
    rng = random.Random(seed)
    groups: dict[tuple[str, str, str, str, str, str], list[QuestionCandidate]] = defaultdict(list)
    for candidate in candidates:
        groups[candidate.stratum].append(candidate)
    for key, rows in groups.items():
        rows.sort(key=lambda candidate: _int(candidate.question_id))
        rng.shuffle(rows)
        groups[key] = rows
    selected: list[QuestionCandidate] = []
    keys = sorted(groups)
    while len(selected) < sample_size:
        added = False
        for key in keys:
            rows = groups[key]
            if not rows:
                continue
            selected.append(rows.pop())
            added = True
            if len(selected) == sample_size:
                break
        if not added:
            break
    return selected


def _profile_transformation_step(config: DataDumpPilotConfig) -> str:
    if config.sample_profile == ANSWERABLE_CLEAN_PROFILE:
        return (
            f"filtered clean answerable {config.site_name} question candidates "
            "using metadata-only rules"
        )
    return f"filtered answerable {config.site_name} question candidates"


def _build_provenance(
    config: DataDumpPilotConfig,
    preflight: DataDumpPreflightResult,
    *,
    root: Path,
) -> dict[str, Any]:
    template_path = (
        root / "reports/datasets/stackexchange-difficulty/provenance_data_dump_template.json"
    )
    record = load_provenance(template_path) if template_path.is_file() else {}
    record.update(
        {
            "dataset_name": "stackexchange-difficulty",
            "dataset_version": f"data-dump-{config.pilot_slug}-{config.dump_date}",
            "source_method": "stack_exchange_data_dump",
            "source_site_slug": preflight.site_slug,
            "source_site_name": config.site_name,
            "pilot_slug": config.pilot_slug,
            "sample_profile": config.sample_profile,
            "sample_size": config.sample_size,
            "sample_seed": config.sample_seed,
            "dump_date": config.dump_date,
            "dump_dir": _display_path(config.dump_dir, root),
            "source_version": f"Stack Exchange Data Dump {config.dump_date}",
            "access_date": config.dump_date,
            "official_source_checked_at": config.dump_date,
            "license": "CC BY-SA, version determined by each post ContentLicense",
            "transformation_steps": [
                "read local extracted Stack Exchange Data Dump XML files",
                "excluded artificial post IDs 1000000001 and 1000000010",
                _profile_transformation_step(config),
                "sampled eligible questions deterministically",
                "normalized selected questions, answers, comments, links, and optional history",
                "validated required fields and accepted-answer consistency",
                "derived thread indicators and JSONL from finalized provenance",
                "wrote aggregate audit without copied Stack Exchange post content",
            ],
            "raw_file_hashes": preflight.raw_file_hashes,
            "processed_output_hash": "sha256:pending-before-processing",
            "output_hash": "sha256:pending-before-processing",
            "script_version": _package_version(),
        }
    )
    return record


def _build_audit(
    *,
    config: DataDumpPilotConfig,
    preflight: DataDumpPreflightResult,
    selection: SelectionResult | None,
    validation_report: dict[str, Any] | None,
    processed_dir: Path | None,
    derived_dir: Path | None,
    root: Path,
    decision: str,
    derived_rows: list[dict[str, Any]] | None = None,
) -> str:
    selected = selection.selected_candidates if selection else []
    validation_issues = len(validation_report.get("issues", [])) if validation_report else 0
    row_counts = validation_report.get("row_counts", {}) if validation_report else {}
    processed_manifest = _display_optional(
        _manifest_path(processed_dir, "processed-output.sha256"),
        root,
    )
    derived_manifest = _display_optional(
        _manifest_path(derived_dir, "derived-output.sha256"),
        root,
    )
    return "\n".join(
        [
            "# Data Dump Pilot Audit",
            "",
            "## Source And Scope",
            "",
            f"- Source: {config.site_name} Stack Exchange Data Dump.",
            f"- Site slug: `{preflight.site_slug}`.",
            f"- Pilot slug: `{config.pilot_slug}`.",
            f"- Dump date: `{config.dump_date}`.",
            f"- Sample profile: `{config.sample_profile}`.",
            f"- Requested sample size: {config.sample_size}.",
            "- No API crawling, HTML scraping, archive download, credential handling, "
            "or corpus release was performed.",
            "",
            "## Preflight",
            "",
            f"- Dump directory: `{_display_path(config.dump_dir, root)}`.",
            f"- XML files: {_format_file_status(preflight.files)}.",
            f"- Raw file hashes: {_format_hashes(preflight.raw_file_hashes)}.",
            f"- Preflight issues: {len(preflight.issues)}.",
            f"- Preflight warnings: {len(preflight.warnings)}.",
            "",
            "## Selection Summary",
            "",
            f"- Total question rows scanned: {selection.total_questions if selection else 0}.",
            f"- Eligible question candidates: {selection.eligible_questions if selection else 0}.",
            f"- Selected questions: {len(selected)}.",
            f"- Artificial ID exclusions: {_excluded(selection, 'artificial_post_id')}.",
            f"- Closed question exclusions: {_excluded(selection, 'closed_question')}.",
            f"- Unanswered exclusions: {_excluded(selection, 'unanswered_question')}.",
            f"- No accepted-answer exclusions: {_excluded(selection, 'no_accepted_answer')}.",
            "- Missing accepted-answer exclusions: "
            f"{_excluded(selection, 'accepted_answer_missing')}.",
            "- Accepted-answer parent mismatch exclusions: "
            f"{_excluded(selection, 'accepted_answer_parent_mismatch')}.",
            f"- Duplicate-link exclusions: {_excluded(selection, 'duplicate_question')}.",
            *_clean_exclusion_lines(config, selection),
            "",
            "## Validation Summary",
            "",
            f"- Question rows: {row_counts.get('questions', 0)}.",
            f"- Answer rows: {row_counts.get('answers', 0)}.",
            f"- Comment rows: {row_counts.get('comments', 0)}.",
            f"- Validation issue count: {validation_issues}.",
            "",
            "## Distribution Summary",
            "",
            f"- Answerability distribution: {_format_counter(Counter({'true': len(selected)}))}.",
            f"- Closure distribution: {_format_counter(Counter({'false': len(selected)}))}.",
            f"- Duplicate distribution: {_format_counter(Counter({'false': len(selected)}))}.",
            "- Tag-family distribution: "
            f"{_format_counter(Counter(c.stratum[0] for c in selected), top_n=25)}.",
            "- Time-period distribution: "
            f"{_format_counter(Counter(c.stratum[1] for c in selected))}.",
            "- Answer-latency distribution: "
            f"{_format_counter(Counter(c.stratum[2] for c in selected))}.",
            f"- Score buckets: {_format_counter(Counter(c.stratum[3] for c in selected))}.",
            f"- View buckets: {_format_counter(Counter(c.stratum[4] for c in selected))}.",
            f"- Comment-count buckets: {_format_counter(Counter(c.stratum[5] for c in selected))}.",
            f"- Derived indicator rows: {len(derived_rows or [])}.",
            "",
            "## Derived Outputs",
            "",
            f"- Processed output directory: `{_display_optional(processed_dir, root)}`.",
            f"- Derived output directory: `{_display_optional(derived_dir, root)}`.",
            f"- Processed hash manifest: `{processed_manifest}`.",
            f"- Derived hash manifest: `{derived_manifest}`.",
            "",
            "## Content Safety",
            "",
            "- This audit contains aggregate counts and hashes only. It does not include "
            "record-level Stack Exchange content, per-record identifiers, annotation files, "
            "credentials, or release artifacts.",
            "",
            "## Decision",
            "",
            f"- Decision: {decision}.",
            "",
        ]
    )


def _xml_row_count(path: Path) -> int:
    count = 0
    for _row in iter_xml_rows(path):
        count += 1
    return count


def _clean_exclusion_lines(
    config: DataDumpPilotConfig,
    selection: SelectionResult | None,
) -> list[str]:
    if config.sample_profile != ANSWERABLE_CLEAN_PROFILE:
        return []
    return [
        f"- Clean negative-score exclusions: {_excluded(selection, 'clean_negative_score')}.",
        f"- Clean missing-tag exclusions: {_excluded(selection, 'clean_missing_tags')}.",
        "- Clean missing first-answer timing exclusions: "
        f"{_excluded(selection, 'clean_missing_first_answer_timing')}.",
        "- Clean long-answer-latency exclusions: "
        f"{_excluded(selection, 'clean_long_answer_latency')}.",
    ]


def _is_required_file(filename: str, *, sample_profile: str, include_post_history: bool) -> bool:
    return filename == "Posts.xml" or (
        filename == "PostLinks.xml" and sample_profile in ANSWERABLE_PROFILES
    ) or (filename == "PostHistory.xml" and include_post_history)


def _validate_sample_profile(value: str) -> str:
    if value not in SUPPORTED_SAMPLE_PROFILES:
        supported = ", ".join(sorted(SUPPORTED_SAMPLE_PROFILES))
        raise DataDumpError(f"sample profile must be one of: {supported}")
    return value


def _validate_dump_date(value: str) -> None:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise DataDumpError("dump date must use YYYY-MM-DD") from exc


def _normalize_site_slug(value: str) -> str:
    try:
        return normalize_site_slug(value)
    except SedePilotError as exc:
        raise DataDumpError(str(exc)) from exc


def _normalize_pilot_slug(value: str) -> str:
    try:
        return normalize_pilot_slug(value)
    except SedePilotError as exc:
        raise DataDumpError(str(exc)) from exc


def _fail_if_exists(*paths: Path) -> None:
    existing = [path for path in paths if path.exists()]
    if existing:
        names = ", ".join(str(path) for path in existing)
        raise DataDumpError(f"Data Dump output path already exists: {names}")


def _write_tsv(rows: list[dict[str, Any]], path: Path, fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_hash_manifest(path: Path, files: list[Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"{sha256_file(file_path)}  {file_path}\n"
        for file_path in files
        if file_path.exists()
    ]
    path.write_text("".join(lines), encoding="utf-8")


def _processed_hash_files(processed_dir: Path) -> list[Path]:
    return [
        processed_dir / "questions.tsv",
        processed_dir / "answers.tsv",
        processed_dir / "comments.tsv",
        processed_dir / "post_links.tsv",
        processed_dir / "tags.tsv",
        processed_dir / "post_history.tsv",
        processed_dir / "validation_report.json",
    ]


def _write_audit(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _display_optional(path: Path | None, root: Path) -> str:
    return "not produced" if path is None else _display_path(path, root)


def _manifest_path(directory: Path | None, name: str) -> Path | None:
    return None if directory is None else directory / name


def _issue(code: str, message: str) -> dict[str, Any]:
    return {"code": code, "message": message, "row_id": None}


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _int(value: Any) -> int:
    try:
        return int(str(value or "0").strip())
    except ValueError:
        return 0


def _sort_datetime(value: str) -> datetime:
    parsed = parse_datetime(value)
    return parsed or datetime.max


def _tag_family(tags: str) -> str:
    text = tags.strip()
    if not text:
        return "none"
    if text.startswith("<") and ">" in text:
        return text[1 : text.find(">")].lower() or "none"
    return text.replace("<", "").replace(">", "").split()[0].lower() or "none"


def _time_period(value: str) -> str:
    parsed = parse_datetime(value)
    if parsed is None:
        return "unknown"
    if parsed < datetime(2014, 1, 1):
        return "older"
    if parsed < datetime(2020, 1, 1):
        return "middle"
    return "recent"


def _answer_latency_bucket(hours: float | None) -> str:
    if hours is None:
        return "unknown"
    if hours < 1:
        return "under_1h"
    if hours < 24:
        return "under_24h"
    if hours < 168:
        return "under_7d"
    return "over_7d"


def _score_bucket(score: int) -> str:
    if score < 0:
        return "negative"
    if score < 3:
        return "low"
    if score < 10:
        return "medium"
    return "high"


def _view_bucket(views: int) -> str:
    if views < 500:
        return "low"
    if views < 5000:
        return "medium"
    return "high"


def _comment_count_bucket(count: int) -> str:
    if count == 0:
        return "none"
    if count < 4:
        return "low"
    return "high"


def _format_counter(counter: Counter[str], *, top_n: int | None = None) -> str:
    if not counter:
        return "none"
    items = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    if top_n is not None and len(items) > top_n:
        top_items = items[:top_n]
        other = sum(value for _key, value in items[top_n:])
        return ", ".join([*(f"{key}={value}" for key, value in top_items), f"other={other}"])
    return ", ".join(f"{key}={value}" for key, value in items)


def _format_file_status(files: dict[str, dict[str, Any]]) -> str:
    if not files:
        return "none"
    return ", ".join(
        f"{name}={'present' if meta.get('present') else 'missing'}"
        for name, meta in sorted(files.items())
    )


def _format_hashes(hashes: dict[str, str]) -> str:
    if not hashes:
        return "none"
    return ", ".join(f"{name}={digest}" for name, digest in sorted(hashes.items()))


def _excluded(selection: SelectionResult | None, key: str) -> int:
    return selection.excluded_counts[key] if selection else 0


def _package_version() -> str:
    try:
        return version("stackexchange-difficulty")
    except PackageNotFoundError:
        return "0.1.0"
