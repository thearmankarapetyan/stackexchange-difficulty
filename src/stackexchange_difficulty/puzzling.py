"""Separate Puzzling Stack Exchange Data Dump and qualitative workflow."""

from __future__ import annotations

import csv
import json
import random
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from stackexchange_difficulty.derive import derive_indicators, elapsed_hours, parse_datetime
from stackexchange_difficulty.derive import parse_tags as parse_stackexchange_tags
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
    POST_LINK_COLUMNS,
    QUESTION_REQUIRED_COLUMNS,
    TAG_COLUMNS,
)
from stackexchange_difficulty.validation import Table, validate_dataset, write_validation_report

PUZZLING_SITE_SLUG = "puzzling"
PUZZLING_SITE_NAME = "Puzzling"
PUZZLING_SOURCE_URL = "https://puzzling.stackexchange.com/"
PUZZLING_SEDE_URL = "https://data.stackexchange.com/puzzling/query/new"
PUZZLING_RIDDLE_CLEAN_PROFILE = "puzzling_riddle_clean"
PUZZLING_DEFAULT_PILOT_SLUG = "puzzling-riddle-clean"
PUZZLING_DEFAULT_QUALITATIVE_SLUG = "puzzling-riddle-recent"
PUZZLING_DEFAULT_SAMPLE_SEED = 20260518
PUZZLING_DUMP_FILES = ("Posts.xml", "PostLinks.xml", "Comments.xml", "Tags.xml", "PostHistory.xml")
PUZZLING_REQUIRED_FILES = {"Posts.xml", "PostLinks.xml"}
PUZZLING_SUPPORTED_SAMPLE_PROFILES = {PUZZLING_RIDDLE_CLEAN_PROFILE}
PUZZLING_TARGET_TAGS = (
    "riddle",
    "lateral-thinking",
    "word",
    "wordplay",
    "enigmatic-puzzle",
    "logic-puzzle",
    "deduction",
    "what-am-i",
)
PUZZLING_EXCLUDED_TAGS = (
    "mathematics",
    "chess",
    "cipher",
    "cryptogram",
    "image",
    "visual",
    "programming",
    "computer-puzzle",
)

PUZZLING_QUALITATIVE_REVIEW_COLUMNS = (
    "record_index",
    "sample_group",
    "question_id",
    "creation_date",
    "tags",
    "score",
    "view_count",
    "answer_count",
    "comment_count",
    "accepted_answer_id",
    "indicator_time_to_first_answer_hours",
    "indicator_tag_popularity_bucket",
    "indicator_question_length",
    "title",
    "body_html",
    "accepted_solution_for_review",
    "other_answers_for_review",
    "comments_for_review",
)

PUZZLING_QUALITATIVE_CODE_COLUMNS = (
    "record_index",
    "sample_group",
    "puzzle_type",
    "qualitative_difficulty",
    "solution_clarity",
    "reasoning_type",
    "language_dependence",
    "misdirection_level",
    "outside_knowledge_needed",
    "answer_explanation_quality",
    "comments_or_hints_role",
    "model_evaluation_suitability",
    "corpus_design_implication",
    "analytic_note",
)

PUZZLING_SAMPLE_GROUPS = (
    "clear_direct",
    "ordinary_intermediate",
    "high_effort_or_ambiguous",
    "language_or_lateral",
)

PUZZLING_CONTROLLED_VALUES = {
    "puzzle_type": {
        "riddle",
        "wordplay",
        "lateral_thinking",
        "logic_deduction",
        "clue_puzzle",
        "mixed",
        "other",
    },
    "qualitative_difficulty": {"low", "medium", "high", "uncertain"},
    "solution_clarity": {
        "unique_solution",
        "multiple_plausible_solutions",
        "unclear_solution",
    },
    "reasoning_type": {
        "direct_inference",
        "deduction",
        "lateral_inference",
        "semantic_association",
        "constraint_satisfaction",
        "outside_knowledge",
        "other",
    },
    "language_dependence": {"low", "medium", "high"},
    "misdirection_level": {"none", "mild", "strong"},
    "outside_knowledge_needed": {"yes", "no", "uncertain"},
    "answer_explanation_quality": {"explicit", "partial", "minimal", "unclear"},
    "comments_or_hints_role": {
        "not_needed",
        "clarify_prompt",
        "provide_hint",
        "challenge_solution",
        "unclear",
    },
    "model_evaluation_suitability": {"good", "diagnostic_only", "exclude", "uncertain"},
    "corpus_design_implication": {
        "keep_riddle_clean_profile",
        "add_diagnostic_subset",
        "include_comments_or_hints",
        "revise_tag_filters",
        "exclude_from_model_eval",
        "other",
    },
}

PUZZLING_UNSAFE_NOTE_PATTERN = re.compile(
    r"(https?://|www\.|<[^>]+>|@|question_id|answer_id|comment_id|post_id|"
    r"body_html|HF_TOKEN|hf_[A-Za-z0-9]{20,})",
    re.IGNORECASE,
)

PUZZLING_UNSAFE_MEMO_PATTERN = re.compile(
    r"(question_id|body_html|accepted_solution_for_review|other_answers_for_review|"
    r"comments_for_review|https?://|www\.|<[^>]+>|HF_TOKEN|hf_[A-Za-z0-9]{20,}|"
    r"Sensitive puzzle)",
    re.IGNORECASE,
)


class PuzzlingError(RuntimeError):
    """Raised when the Puzzling workflow cannot continue safely."""


@dataclass(frozen=True)
class PuzzlingPreflightConfig:
    project_root: Path
    dump_dir: Path
    dump_date: str


@dataclass(frozen=True)
class PuzzlingPilotConfig(PuzzlingPreflightConfig):
    pilot_slug: str = PUZZLING_DEFAULT_PILOT_SLUG
    sample_profile: str = PUZZLING_RIDDLE_CLEAN_PROFILE
    sample_size: int = 2000
    sample_seed: int = PUZZLING_DEFAULT_SAMPLE_SEED


@dataclass(frozen=True)
class PuzzlingPreflightResult:
    ok: bool
    dump_dir: Path
    dump_date: str
    site_slug: str
    site_name: str
    files: dict[str, dict[str, Any]]
    raw_file_hashes: dict[str, str]
    issues: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "dump_dir": str(self.dump_dir),
            "dump_date": self.dump_date,
            "site_slug": self.site_slug,
            "site_name": self.site_name,
            "files": self.files,
            "raw_file_hashes": self.raw_file_hashes,
            "issues": self.issues,
            "warnings": self.warnings,
        }


@dataclass(frozen=True)
class PuzzlingPilotResult:
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
class PuzzlingCandidate:
    question_id: str
    accepted_answer_id: str
    tags: tuple[str, ...]
    creation_date: str
    score: int
    view_count: int
    answer_count: int
    comment_count: int
    first_answer_creation_date: str
    tag_family: str
    stratum: tuple[str, str, str, str, str, str, str]


@dataclass(frozen=True)
class PuzzlingAnswerMeta:
    answer_id: str
    question_id: str
    creation_date: str


@dataclass
class PuzzlingSelectionResult:
    selected_ids: set[str]
    selected_candidates: list[PuzzlingCandidate]
    excluded_counts: Counter[str]
    target_tag_counts: Counter[str]
    excluded_tag_counts: Counter[str]
    total_questions: int
    eligible_questions: int
    decision: str = "puzzling_parser_validated"
    issues: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class PuzzlingQualitativePrepareResult:
    review_path: Path
    codes_path: Path
    readme_path: Path
    manifest_path: Path
    selected_records: int
    date_from: str
    date_to: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "ok": True,
            "review": str(self.review_path),
            "codes": str(self.codes_path),
            "readme": str(self.readme_path),
            "manifest": str(self.manifest_path),
            "selected_records": self.selected_records,
            "date_from": self.date_from,
            "date_to": self.date_to,
        }


@dataclass(frozen=True)
class PuzzlingQualitativeSummaryResult:
    output_path: Path
    coded_records: int
    unsafe_content_markers: int

    def to_payload(self) -> dict[str, Any]:
        return {
            "ok": True,
            "output": str(self.output_path),
            "coded_records": self.coded_records,
            "unsafe_content_markers": self.unsafe_content_markers,
        }


def iter_puzzling_xml_rows(path: Path) -> Iterator[dict[str, str]]:
    try:
        for _event, elem in ET.iterparse(path, events=("end",)):
            if elem.tag == "row":
                yield {str(key): str(value) for key, value in elem.attrib.items()}
            elem.clear()
    except ET.ParseError as exc:
        raise PuzzlingError(f"XML parse failed for {path}: {exc}") from exc


def preflight_puzzling_dump(config: PuzzlingPreflightConfig) -> PuzzlingPreflightResult:
    _validate_dump_date(config.dump_date)
    issues: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    files: dict[str, dict[str, Any]] = {}
    raw_hashes: dict[str, str] = {}

    if not config.dump_dir.is_dir():
        issues.append(
            _issue("dump_dir_missing", f"dump directory does not exist: {config.dump_dir}")
        )

    for filename in PUZZLING_DUMP_FILES:
        path = config.dump_dir / filename
        required = filename in PUZZLING_REQUIRED_FILES
        entry: dict[str, Any] = {"present": path.is_file(), "required": required}
        if not path.is_file():
            if required:
                issues.append(
                    _issue("missing_required_dump_file", f"required file missing: {filename}")
                )
            else:
                warnings.append(
                    _issue("missing_optional_dump_file", f"optional file missing: {filename}")
                )
            files[filename] = entry
            continue
        if filename == "PostHistory.xml":
            entry["skipped"] = True
            entry["reason"] = "post history is intentionally ignored for Puzzling v1"
            files[filename] = entry
            continue
        digest = sha256_file(path)
        entry["sha256"] = f"sha256:{digest}"
        entry["rows"] = _xml_row_count(path)
        raw_hashes[filename] = f"sha256:{digest}"
        files[filename] = entry

    return PuzzlingPreflightResult(
        ok=not issues,
        dump_dir=config.dump_dir,
        dump_date=config.dump_date,
        site_slug=PUZZLING_SITE_SLUG,
        site_name=PUZZLING_SITE_NAME,
        files=files,
        raw_file_hashes=raw_hashes,
        issues=issues,
        warnings=warnings,
    )


def run_puzzling_pilot(config: PuzzlingPilotConfig) -> PuzzlingPilotResult:
    root = config.project_root.resolve()
    _validate_dump_date(config.dump_date)
    _validate_puzzling_sample_profile(config.sample_profile)
    if config.sample_size < 1:
        raise PuzzlingError("sample size must be at least 1")
    if not _valid_slug(config.pilot_slug):
        raise PuzzlingError("pilot slug must contain only lowercase letters, numbers, and hyphens")

    processed_dir = (
        root / f"data/processed/stackexchange-difficulty/{config.pilot_slug}-{config.dump_date}"
    )
    derived_dir = (
        root
        / f"data/processed/stackexchange-difficulty/{config.pilot_slug}-{config.dump_date}-derived"
    )
    report_slug = config.pilot_slug.replace("-", "_")
    audit_path = (
        root
        / "reports/datasets/stackexchange-difficulty/audits"
        / f"{report_slug}_{config.dump_date}.md"
    )
    provenance_path = (
        root
        / "reports/datasets/stackexchange-difficulty"
        / f"provenance_{report_slug}_{config.dump_date}.json"
    )
    _fail_if_exists(processed_dir, derived_dir, audit_path, provenance_path)

    preflight = preflight_puzzling_dump(config)
    if not preflight.ok:
        decision = (
            "puzzling_duplicate_filter_incomplete"
            if any(
                issue["code"] == "missing_required_dump_file"
                and "PostLinks.xml" in issue["message"]
                for issue in preflight.issues
            )
            else "puzzling_preflight_failed"
        )
        _write_audit(
            audit_path,
            _build_puzzling_audit(
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
        return PuzzlingPilotResult(
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

    selection = _select_puzzling_questions(config)
    if selection.decision != "puzzling_parser_validated":
        _write_audit(
            audit_path,
            _build_puzzling_audit(
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
        return PuzzlingPilotResult(
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
    tables = _write_puzzling_outputs(config, selection, processed_dir)
    provenance = _build_puzzling_provenance(config, preflight, root=root)
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
        decision = "puzzling_validation_failed"
        _write_audit(
            audit_path,
            _build_puzzling_audit(
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
        return PuzzlingPilotResult(
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
        decision = "puzzling_validation_failed"
        _write_audit(
            audit_path,
            _build_puzzling_audit(
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
        return PuzzlingPilotResult(
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
    decision = "puzzling_parser_validated"
    _write_audit(
        audit_path,
        _build_puzzling_audit(
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
    return PuzzlingPilotResult(
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


def prepare_puzzling_qualitative_sample(
    *,
    questions: Table,
    answers: Table,
    comments: Table,
    indicators: Table,
    date_from: str,
    date_to: str,
    sample_size: int,
    out_dir: Path,
    seed: int = PUZZLING_DEFAULT_SAMPLE_SEED,
) -> PuzzlingQualitativePrepareResult:
    if sample_size <= 0:
        raise PuzzlingError("sample size must be positive")
    _require_ignored_processed_out_dir(out_dir)
    _require_columns(questions, QUESTION_REQUIRED_COLUMNS)
    _require_columns(answers, ANSWER_REQUIRED_COLUMNS)
    _require_columns(comments, (*COMMENT_REQUIRED_COLUMNS, "content_license"))
    _require_columns(indicators, DERIVED_COLUMNS)
    start = _parse_date(date_from)
    end = _parse_date(date_to)
    if start > end:
        raise PuzzlingError("date-from must be on or before date-to")

    records = _recent_puzzling_records(
        questions,
        answers,
        comments,
        indicators,
        start=start,
        end=end,
    )
    actual_size = sample_size
    partial_sample = False
    if len(records) < sample_size:
        if sample_size >= 30 and len(records) >= 30:
            actual_size = len(records)
            partial_sample = True
        else:
            raise PuzzlingError(
                f"fewer than minimum qualitative records: {len(records)} < {min(sample_size, 30)}"
            )

    selected, candidate_counts = _select_puzzling_qualitative_sample(
        records,
        sample_size=actual_size,
        seed=seed,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    review_path = out_dir / "qualitative_review.tsv"
    codes_path = out_dir / "qualitative_codes.tsv"
    readme_path = out_dir / "README.md"
    manifest_path = out_dir / "sample_manifest.json"
    _write_puzzling_review(review_path, selected)
    _write_puzzling_codes_template(codes_path, selected)
    manifest = {
        "site_slug": PUZZLING_SITE_SLUG,
        "source_slug": PUZZLING_DEFAULT_PILOT_SLUG,
        "date_from": date_from,
        "date_to": date_to,
        "requested_sample_size": sample_size,
        "selected_records": len(selected),
        "partial_sample": partial_sample,
        "seed": seed,
        "recent_candidate_count": len(records),
        "candidate_group_counts": candidate_counts,
        "sample_group_counts": dict(Counter(row["sample_group"] for row in selected)),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    readme_path.write_text(
        "\n".join(
            [
                "# Local Recent Puzzling Qualitative Sample",
                "",
                "This directory is ignored by Git because review files may contain real "
                "Puzzling Stack Exchange post content.",
                "",
                "Use the Puzzling controlled coding schema. Keep analytic notes blank "
                "or paraphrased, and do not copy puzzle text, answers, comments, URLs, "
                "handles, or post identifiers.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return PuzzlingQualitativePrepareResult(
        review_path=review_path,
        codes_path=codes_path,
        readme_path=readme_path,
        manifest_path=manifest_path,
        selected_records=len(selected),
        date_from=date_from,
        date_to=date_to,
    )


def summarize_puzzling_qualitative_coding(
    *,
    codes: Table,
    manifest_path: Path,
    output_path: Path,
    labeler: str,
    sample_size: int | None = None,
) -> PuzzlingQualitativeSummaryResult:
    _require_columns(codes, PUZZLING_QUALITATIVE_CODE_COLUMNS)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = sample_size or int(manifest.get("selected_records", 50))
    rows = _validated_puzzling_code_rows(codes)
    if len(rows) != expected:
        raise PuzzlingError(f"expected {expected} coded records, got {len(rows)}")
    markdown = _puzzling_qualitative_memo(rows=rows, manifest=manifest, labeler=labeler)
    unsafe_markers = len(PUZZLING_UNSAFE_MEMO_PATTERN.findall(markdown))
    if unsafe_markers:
        raise PuzzlingError("Puzzling qualitative memo contains unsafe row-level content markers")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    return PuzzlingQualitativeSummaryResult(
        output_path=output_path,
        coded_records=len(rows),
        unsafe_content_markers=unsafe_markers,
    )


def _select_puzzling_questions(config: PuzzlingPilotConfig) -> PuzzlingSelectionResult:
    duplicate_ids = _duplicate_question_ids(config.dump_dir / "PostLinks.xml")
    minimal_candidates: dict[str, dict[str, str]] = {}
    accepted_ids: set[str] = set()
    excluded = Counter()
    total_questions = 0

    for row in iter_puzzling_xml_rows(config.dump_dir / "Posts.xml"):
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
    answer_by_id: dict[str, PuzzlingAnswerMeta] = {}
    answer_counts = Counter()
    first_answer_by_question: dict[str, PuzzlingAnswerMeta] = {}
    for row in iter_puzzling_xml_rows(config.dump_dir / "Posts.xml"):
        if row.get("PostTypeId") != "2":
            continue
        answer_id = _clean(row.get("Id"))
        parent_id = _clean(row.get("ParentId"))
        if answer_id not in accepted_ids and parent_id not in candidate_ids:
            continue
        meta = PuzzlingAnswerMeta(
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

    eligible: list[PuzzlingCandidate] = []
    target_tag_counts = Counter()
    excluded_tag_counts = Counter()
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
        tags = tuple(parse_stackexchange_tags(row["tags"]))
        excluded_tags = [tag for tag in PUZZLING_EXCLUDED_TAGS if tag in tags]
        if excluded_tags:
            excluded["excluded_first_pass_tag"] += 1
            for tag in excluded_tags:
                excluded_tag_counts[tag] += 1
            continue
        target_tags = [tag for tag in PUZZLING_TARGET_TAGS if tag in tags]
        if not target_tags:
            excluded["missing_target_tag"] += 1
            continue
        for tag in target_tags:
            target_tag_counts[tag] += 1
        first_answer = first_answer_by_question.get(question_id)
        eligible.append(_puzzling_candidate_from_row(row, tags=tags, first_answer=first_answer))

    if len(eligible) < config.sample_size:
        return PuzzlingSelectionResult(
            selected_ids=set(),
            selected_candidates=[],
            excluded_counts=excluded,
            target_tag_counts=target_tag_counts,
            excluded_tag_counts=excluded_tag_counts,
            total_questions=total_questions,
            eligible_questions=len(eligible),
            decision="puzzling_sampling_failed",
            issues=[
                _issue(
                    "sample_size_unavailable",
                    (
                        f"eligible Puzzling records {len(eligible)} are fewer than "
                        f"requested sample size {config.sample_size}"
                    ),
                )
            ],
        )

    selected = _stratified_puzzling_sample(
        eligible,
        sample_size=config.sample_size,
        seed=config.sample_seed,
    )
    return PuzzlingSelectionResult(
        selected_ids={candidate.question_id for candidate in selected},
        selected_candidates=selected,
        excluded_counts=excluded,
        target_tag_counts=Counter(
            tag
            for candidate in selected
            for tag in candidate.tags
            if tag in PUZZLING_TARGET_TAGS
        ),
        excluded_tag_counts=excluded_tag_counts,
        total_questions=total_questions,
        eligible_questions=len(eligible),
    )


def _puzzling_candidate_from_row(
    row: dict[str, str],
    *,
    tags: tuple[str, ...],
    first_answer: PuzzlingAnswerMeta | None,
) -> PuzzlingCandidate:
    first_answer_creation = first_answer.creation_date if first_answer else ""
    latency = elapsed_hours(
        parse_datetime(row["creation_date"]),
        parse_datetime(first_answer_creation),
    )
    tag_family = _puzzling_tag_family(tags)
    stratum = (
        tag_family,
        _time_period(row["creation_date"]),
        _answer_latency_bucket(latency),
        _score_bucket(_int(row["score"])),
        _view_bucket(_int(row["view_count"])),
        _puzzling_comment_count_bucket(_int(row["comment_count"])),
        _puzzling_answer_count_bucket(_int(row["answer_count"])),
    )
    return PuzzlingCandidate(
        question_id=row["question_id"],
        accepted_answer_id=row["accepted_answer_id"],
        tags=tags,
        creation_date=row["creation_date"],
        score=_int(row["score"]),
        view_count=_int(row["view_count"]),
        answer_count=_int(row["answer_count"]),
        comment_count=_int(row["comment_count"]),
        first_answer_creation_date=first_answer_creation,
        tag_family=tag_family,
        stratum=stratum,
    )


def _write_puzzling_outputs(
    config: PuzzlingPilotConfig,
    selection: PuzzlingSelectionResult,
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

    for row in iter_puzzling_xml_rows(config.dump_dir / "Posts.xml"):
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

    return {
        "questions": Table("questions", question_rows, QUESTION_REQUIRED_COLUMNS),
        "answers": Table("answers", answer_rows, ANSWER_REQUIRED_COLUMNS),
        "comments": Table("comments", comment_rows, (*COMMENT_REQUIRED_COLUMNS, "content_license")),
    }


def _build_puzzling_provenance(
    config: PuzzlingPilotConfig,
    preflight: PuzzlingPreflightResult,
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
            "dataset_version": f"{config.pilot_slug}-{config.dump_date}",
            "source_method": "stack_exchange_data_dump",
            "source_site_slug": PUZZLING_SITE_SLUG,
            "source_site_name": PUZZLING_SITE_NAME,
            "source_url": PUZZLING_SOURCE_URL,
            "sede_url": PUZZLING_SEDE_URL,
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
                "read local extracted Puzzling Stack Exchange Data Dump XML files",
                "excluded artificial post IDs 1000000001 and 1000000010",
                "filtered answerable riddle/language puzzle candidates",
                "excluded closed, duplicate, unanswered, and no-accepted-answer records",
                "excluded visual/cipher/math/programming-heavy first-pass tags",
                "sampled deterministically across Puzzling metadata strata",
                "validated canonical tables and accepted-answer consistency",
                "derived indicators and JSONL locally",
                "wrote aggregate audit without copied Puzzling post content",
            ],
            "raw_file_hashes": preflight.raw_file_hashes,
            "processed_output_hash": "sha256:pending-before-processing",
            "output_hash": "sha256:pending-before-processing",
            "script_version": _package_version(),
        }
    )
    return record


def _build_puzzling_audit(
    *,
    config: PuzzlingPilotConfig,
    preflight: PuzzlingPreflightResult,
    selection: PuzzlingSelectionResult | None,
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
    derived_manifest = _display_optional(_manifest_path(derived_dir, "derived-output.sha256"), root)
    return "\n".join(
        [
            "# Puzzling Riddle Data Dump Pilot Audit",
            "",
            "## Source And Scope",
            "",
            "- Source: Puzzling Stack Exchange Data Dump.",
            f"- Site slug: `{PUZZLING_SITE_SLUG}`.",
            f"- Pilot slug: `{config.pilot_slug}`.",
            f"- Dump date: `{config.dump_date}`.",
            f"- Sample profile: `{config.sample_profile}`.",
            f"- Requested sample size: {config.sample_size}.",
            "- Puzzling accepted answers are treated as accepted or intended solution candidates.",
            "- No API crawling, HTML scraping, archive download, PostHistory parsing, "
            "credential handling, or corpus release was performed.",
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
            "- Target-tag candidates: "
            f"{_format_counter(selection.target_tag_counts if selection else Counter())}.",
            "- Excluded-tag exclusions: "
            f"{_format_counter(selection.excluded_tag_counts if selection else Counter())}.",
            f"- Artificial ID exclusions: {_excluded(selection, 'artificial_post_id')}.",
            f"- Closed question exclusions: {_excluded(selection, 'closed_question')}.",
            f"- Unanswered exclusions: {_excluded(selection, 'unanswered_question')}.",
            f"- No accepted-answer exclusions: {_excluded(selection, 'no_accepted_answer')}.",
            "- Missing accepted-answer exclusions: "
            f"{_excluded(selection, 'accepted_answer_missing')}.",
            "- Accepted-answer parent mismatch exclusions: "
            f"{_excluded(selection, 'accepted_answer_parent_mismatch')}.",
            f"- Duplicate-link exclusions: {_excluded(selection, 'duplicate_question')}.",
            f"- Missing target-tag exclusions: {_excluded(selection, 'missing_target_tag')}.",
            "- First-pass excluded-tag exclusions: "
            f"{_excluded(selection, 'excluded_first_pass_tag')}.",
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
            "- Tag-family distribution: "
            f"{_format_counter(Counter(c.stratum[0] for c in selected), top_n=25)}.",
            "- Time-period distribution: "
            f"{_format_counter(Counter(c.stratum[1] for c in selected))}.",
            "- Answer-latency distribution: "
            f"{_format_counter(Counter(c.stratum[2] for c in selected))}.",
            f"- Score buckets: {_format_counter(Counter(c.stratum[3] for c in selected))}.",
            f"- View buckets: {_format_counter(Counter(c.stratum[4] for c in selected))}.",
            "- Comment-count buckets: "
            f"{_format_counter(Counter(c.stratum[5] for c in selected))}.",
            "- Answer-count buckets: "
            f"{_format_counter(Counter(c.stratum[6] for c in selected))}.",
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
            "- This audit contains aggregate counts and hashes only. It excludes Puzzling "
            "post titles, puzzle bodies, solution text, comments, URLs, handles, row-level "
            "review files, coding files, credentials, and release artifacts.",
            "",
            "## Decision",
            "",
            f"- Decision: {decision}.",
            "",
        ]
    )


def _recent_puzzling_records(
    questions: Table,
    answers: Table,
    comments: Table,
    indicators: Table,
    *,
    start: datetime,
    end: datetime,
) -> list[dict[str, Any]]:
    answers_by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for answer in answers.rows:
        answers_by_question[str(answer.get("question_id", "")).strip()].append(answer)
    comments_by_post: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for comment in comments.rows:
        comments_by_post[str(comment.get("post_id", "")).strip()].append(comment)
    indicators_by_question = {
        str(row.get("question_id", "")).strip(): row for row in indicators.rows
    }
    records = []
    for question in questions.rows:
        created = _parse_datetime(question.get("creation_date"))
        if created is None or not (start <= created <= end):
            continue
        question_id = str(question.get("question_id", "")).strip()
        question_answers = sorted(
            answers_by_question.get(question_id, []),
            key=lambda row: str(row.get("creation_date", "")),
        )
        answer_ids = {str(row.get("answer_id", "")).strip() for row in question_answers}
        selected_comments = []
        for post_id in {question_id, *answer_ids}:
            selected_comments.extend(comments_by_post.get(post_id, []))
        selected_comments.sort(key=lambda row: str(row.get("creation_date", "")))
        records.append(
            {
                "question": question,
                "answers": question_answers,
                "comments": selected_comments,
                "indicators": indicators_by_question.get(question_id, {}),
            }
        )
    return sorted(records, key=lambda row: _int_or_text(row["question"].get("question_id")))


def _select_puzzling_qualitative_sample(
    records: list[dict[str, Any]],
    *,
    sample_size: int,
    seed: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    pools = {group: [] for group in PUZZLING_SAMPLE_GROUPS}
    for record in records:
        for group in _matching_puzzling_groups(record):
            pools[group].append(record)
    candidate_counts = {group: len(rows) for group, rows in pools.items()}
    targets = _group_targets(sample_size, PUZZLING_SAMPLE_GROUPS)
    rng = random.Random(seed)
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    for group in PUZZLING_SAMPLE_GROUPS:
        selected.extend(
            _take_from_pool(
                pools[group],
                group=group,
                count=targets[group],
                rng=rng,
                selected_ids=selected_ids,
            )
        )
    while len(selected) < sample_size:
        made_progress = False
        for group in PUZZLING_SAMPLE_GROUPS:
            if len(selected) >= sample_size:
                break
            taken = _take_from_pool(
                pools[group],
                group=group,
                count=1,
                rng=rng,
                selected_ids=selected_ids,
            )
            if taken:
                selected.extend(taken)
                made_progress = True
        if not made_progress:
            break
    if len(selected) != sample_size:
        raise PuzzlingError(f"could not select requested qualitative sample: {len(selected)}")
    return _with_record_indexes(selected), candidate_counts


def _matching_puzzling_groups(record: dict[str, Any]) -> list[str]:
    question = record["question"]
    indicator = record["indicators"]
    latency = _float_or_none(indicator.get("time_to_first_answer_hours"))
    comment_count = _int_or_none(question.get("comment_count")) or 0
    answer_count = _int_or_none(question.get("answer_count")) or 0
    tags = set(parse_stackexchange_tags(question.get("tags", "")))
    groups = []
    if (
        latency is not None
        and latency < 1
        and comment_count <= 2
        and answer_count <= 2
    ):
        groups.append("clear_direct")
    if latency is not None and 1 <= latency < 24 and answer_count >= 1 and comment_count <= 6:
        groups.append("ordinary_intermediate")
    if (latency is not None and latency >= 24) or comment_count >= 7 or answer_count >= 5:
        groups.append("high_effort_or_ambiguous")
    if tags & {"word", "wordplay", "lateral-thinking", "what-am-i", "enigmatic-puzzle"}:
        groups.append("language_or_lateral")
    return groups or ["ordinary_intermediate"]


def _write_puzzling_review(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=PUZZLING_QUALITATIVE_REVIEW_COLUMNS,
            delimiter="\t",
        )
        writer.writeheader()
        for record in records:
            question = record["question"]
            answers = record["answers"]
            indicator = record["indicators"]
            accepted_id = str(question.get("accepted_answer_id", "")).strip()
            accepted = [
                answer
                for answer in answers
                if str(answer.get("answer_id", "")).strip() == accepted_id
            ]
            other_answers = [
                answer
                for answer in answers
                if str(answer.get("answer_id", "")).strip() != accepted_id
            ]
            writer.writerow(
                {
                    "record_index": record["record_index"],
                    "sample_group": record["sample_group"],
                    "question_id": question.get("question_id", ""),
                    "creation_date": question.get("creation_date", ""),
                    "tags": question.get("tags", ""),
                    "score": question.get("score", ""),
                    "view_count": question.get("view_count", ""),
                    "answer_count": question.get("answer_count", ""),
                    "comment_count": question.get("comment_count", ""),
                    "accepted_answer_id": question.get("accepted_answer_id", ""),
                    "indicator_time_to_first_answer_hours": indicator.get(
                        "time_to_first_answer_hours", ""
                    ),
                    "indicator_tag_popularity_bucket": indicator.get(
                        "tag_popularity_bucket", ""
                    ),
                    "indicator_question_length": indicator.get("question_length", ""),
                    "title": question.get("title", ""),
                    "body_html": question.get("body_html", ""),
                    "accepted_solution_for_review": _answers_for_review(accepted),
                    "other_answers_for_review": _answers_for_review(other_answers),
                    "comments_for_review": _comments_for_review(record["comments"]),
                }
            )


def _write_puzzling_codes_template(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=PUZZLING_QUALITATIVE_CODE_COLUMNS,
            delimiter="\t",
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "record_index": record["record_index"],
                    "sample_group": record["sample_group"],
                    "puzzle_type": "",
                    "qualitative_difficulty": "",
                    "solution_clarity": "",
                    "reasoning_type": "",
                    "language_dependence": "",
                    "misdirection_level": "",
                    "outside_knowledge_needed": "",
                    "answer_explanation_quality": "",
                    "comments_or_hints_role": "",
                    "model_evaluation_suitability": "",
                    "corpus_design_implication": "",
                    "analytic_note": "",
                }
            )


def _validated_puzzling_code_rows(codes: Table) -> list[dict[str, str]]:
    seen: set[str] = set()
    rows = []
    for row in codes.rows:
        record_index = str(row.get("record_index", "")).strip()
        if not record_index:
            raise PuzzlingError("code row has blank record_index")
        if record_index in seen:
            raise PuzzlingError(f"duplicate record_index: {record_index}")
        seen.add(record_index)
        sample_group = str(row.get("sample_group", "")).strip()
        if sample_group not in PUZZLING_SAMPLE_GROUPS:
            raise PuzzlingError(f"invalid sample_group={sample_group!r}")
        normalized = {"record_index": record_index, "sample_group": sample_group}
        for column, allowed in PUZZLING_CONTROLLED_VALUES.items():
            value = str(row.get(column, "")).strip()
            if value not in allowed:
                raise PuzzlingError(f"invalid {column}={value!r}")
            normalized[column] = value
        note = str(row.get("analytic_note", "")).strip()
        if len(note) > 120:
            raise PuzzlingError(f"analytic_note too long for record_index={record_index}")
        if PUZZLING_UNSAFE_NOTE_PATTERN.search(note):
            raise PuzzlingError(f"unsafe analytic_note for record_index={record_index}")
        normalized["analytic_note"] = note
        rows.append(normalized)
    return rows


def _puzzling_qualitative_memo(
    *,
    rows: list[dict[str, str]],
    manifest: dict[str, Any],
    labeler: str,
) -> str:
    counters = {
        column: Counter(row[column] for row in rows)
        for column in PUZZLING_CONTROLLED_VALUES
    }
    sample_groups = Counter(row["sample_group"] for row in rows)
    suitability = counters["model_evaluation_suitability"]
    accepted_or_diagnostic = suitability["good"] + suitability["diagnostic_only"]
    exclude_count = suitability["exclude"]
    unclear_solution = counters["solution_clarity"]["unclear_solution"]
    gate = _puzzling_qualitative_acceptance_gate(
        coded_records=len(rows),
        accepted_or_diagnostic=accepted_or_diagnostic,
        exclude_count=exclude_count,
        unclear_solution=unclear_solution,
    )
    return "\n".join(
        [
            "# Qualitative Analysis Of Recent Puzzling/Riddle Threads - 2026-04-21",
            "",
            "## Objective",
            "",
            "This memo summarizes a recent Puzzling Stack Exchange slice for natural-language "
            "problem-solving, riddle, wordplay, and lateral-reasoning difficulty analysis.",
            "",
            "## Source And Sample",
            "",
            f"- Site slug: `{manifest.get('site_slug', PUZZLING_SITE_SLUG)}`.",
            f"- Source slug: `{manifest.get('source_slug', '')}`.",
            f"- Date range: `{manifest.get('date_from', '')}` to `{manifest.get('date_to', '')}`.",
            f"- Coded records: {len(rows)}.",
            f"- Partial sample: {str(bool(manifest.get('partial_sample', False))).lower()}.",
            f"- Sample groups: {_format_counter(sample_groups)}.",
            "",
            "## Coding Method",
            "",
            f"- Labeling method: {labeler}.",
            "- Coding used controlled categories for puzzle type, qualitative difficulty, "
            "solution clarity, reasoning type, language dependence, misdirection, outside "
            "knowledge, answer explanation, comments or hints, model-evaluation suitability, "
            "and corpus-design implication.",
            "",
            "## Aggregate Coding Counts",
            "",
            *[
                f"- {column}: {_format_counter(counters[column])}."
                for column in PUZZLING_CONTROLLED_VALUES
            ],
            "",
            "## Observed Puzzle-Difficulty Patterns",
            "",
            "- Direct riddles are best suited for clean natural-language difficulty checks when "
            "the prompt and accepted solution relation are explicit.",
            "- Wordplay and lateral puzzles are useful diagnostic cases because difficulty can "
            "come from ambiguity, hidden assumptions, or deliberate misdirection.",
            "- Puzzling accepted answers are treated as accepted or intended solution candidates, "
            "not as identical to ordinary help-forum answerability.",
            "",
            "## Language And Misdirection Patterns",
            "",
            "- Language dependence and misdirection should be tracked separately from generic "
            "difficulty because they may favor or penalize language models differently.",
            "- Strongly lateral or word-dependent records should remain visible as a diagnostic "
            "subset even when excluded from strict answerability benchmarks.",
            "",
            "## Role Of Accepted Answers",
            "",
            "- Accepted answers provide a practical solution anchor for the pilot.",
            "- They still require qualitative interpretation because Puzzling can have multiple "
            "plausible or community-negotiated solutions.",
            "",
            "## Role Of Comments And Hints",
            "",
            "- Comments and hints may clarify puzzle constraints or reveal intended directions.",
            "- The main pipeline keeps comments local but records whether they are needed for "
            "interpretation through aggregate coding.",
            "",
            "## Model-Evaluation Suitability",
            "",
            f"- Good or diagnostic-only records: {accepted_or_diagnostic}.",
            f"- Excluded records: {exclude_count}.",
            f"- Unclear-solution records: {unclear_solution}.",
            f"- Qualitative acceptance gate: {gate}.",
            "",
            "## Corpus-Design Implications",
            "",
            "- Keep Puzzling as a separate natural-language problem-solving track.",
            "- Keep Mathematics as the formal-reasoning baseline rather than replacing it.",
            "- Use Puzzling coding outcomes to decide whether the main corpus should include "
            "riddles, a diagnostic riddle subset, or both formal and natural-language tracks.",
            "",
            "## Discussion Points For Supervisor",
            "",
            "- Decide whether Puzzling is the preferred site for difficulty in words.",
            "- Decide whether wordplay/lateral cases should be benchmark material or diagnostic "
            "material.",
            "- Decide how much comment and hint context is acceptable in later model evaluation.",
            "",
            "## Content Safety",
            "",
            "- This memo contains aggregate counts and paraphrased methodological patterns only. "
            "It excludes post identifiers, puzzle titles, puzzle text, answer text, comment "
            "text, URLs, user handles, local review files, local coding files, and credentials.",
            "",
        ]
    )


def _selected_comments(
    path: Path,
    question_ids: set[str],
    answer_ids: set[str],
) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    valid_posts = question_ids | answer_ids
    rows = []
    for row in iter_puzzling_xml_rows(path):
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
    rows = []
    for row in iter_puzzling_xml_rows(path):
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
    rows = []
    for row in iter_puzzling_xml_rows(path):
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


def _duplicate_question_ids(path: Path) -> set[str]:
    duplicates = set()
    for row in iter_puzzling_xml_rows(path):
        if _clean(row.get("LinkTypeId")) == DUPLICATE_LINK_TYPE_ID:
            duplicates.add(_clean(row.get("PostId")))
    return duplicates


def _stratified_puzzling_sample(
    candidates: list[PuzzlingCandidate],
    *,
    sample_size: int,
    seed: int,
) -> list[PuzzlingCandidate]:
    rng = random.Random(seed)
    groups: dict[tuple[str, str, str, str, str, str, str], list[PuzzlingCandidate]] = (
        defaultdict(list)
    )
    for candidate in candidates:
        groups[candidate.stratum].append(candidate)
    for key, rows in groups.items():
        rows.sort(key=lambda candidate: _int(candidate.question_id))
        rng.shuffle(rows)
        groups[key] = rows
    selected = []
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


def _answers_for_review(answers: list[dict[str, Any]]) -> str:
    return "\n\n--- answer ---\n\n".join(
        "\n".join(
            [
                f"answer_id={answer.get('answer_id', '')}",
                f"is_accepted={answer.get('is_accepted', '')}",
                f"score={answer.get('score', '')}",
                f"creation_date={answer.get('creation_date', '')}",
                str(answer.get("body_html", "")),
            ]
        )
        for answer in answers
    )


def _comments_for_review(comments: list[dict[str, Any]]) -> str:
    return "\n\n--- comment ---\n\n".join(
        "\n".join(
            [
                f"comment_id={comment.get('comment_id', '')}",
                f"post_id={comment.get('post_id', '')}",
                f"score={comment.get('score', '')}",
                f"creation_date={comment.get('creation_date', '')}",
                str(comment.get("text", "")),
            ]
        )
        for comment in comments
    )


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
        processed_dir / "validation_report.json",
    ]


def _xml_row_count(path: Path) -> int:
    return sum(1 for _row in iter_puzzling_xml_rows(path))


def _require_ignored_processed_out_dir(out_dir: Path) -> None:
    parts = out_dir.parts
    required = ("data", "processed", "stackexchange-difficulty")
    for index in range(len(parts) - len(required) + 1):
        if parts[index : index + len(required)] == required:
            return
    raise PuzzlingError(
        "Puzzling qualitative out-dir must be under data/processed/stackexchange-difficulty"
    )


def _require_columns(table: Table, columns: tuple[str, ...]) -> None:
    missing = [column for column in columns if column not in table.columns]
    if missing:
        raise PuzzlingError(f"{table.name} is missing required columns: {', '.join(missing)}")


def _validate_puzzling_sample_profile(value: str) -> str:
    if value not in PUZZLING_SUPPORTED_SAMPLE_PROFILES:
        supported = ", ".join(sorted(PUZZLING_SUPPORTED_SAMPLE_PROFILES))
        raise PuzzlingError(f"sample profile must be one of: {supported}")
    return value


def _validate_dump_date(value: str) -> None:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise PuzzlingError("dump date must use YYYY-MM-DD") from exc


def _valid_slug(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value))


def _fail_if_exists(*paths: Path) -> None:
    existing = [path for path in paths if path.exists()]
    if existing:
        names = ", ".join(str(path) for path in existing)
        raise PuzzlingError(f"Puzzling output path already exists: {names}")


def _write_audit(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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


def _puzzling_tag_family(tags: tuple[str, ...]) -> str:
    for target in PUZZLING_TARGET_TAGS:
        if target in tags:
            return target
    return tags[0] if tags else "none"


def _time_period(value: str) -> str:
    parsed = parse_datetime(value)
    if parsed is None:
        return "unknown"
    if parsed < datetime(2014, 1, 1):
        return "older"
    if parsed < datetime(2020, 1, 1):
        return "middle"
    if parsed < datetime(2025, 5, 1):
        return "recent_pre_window"
    return "recent_window"


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


def _puzzling_comment_count_bucket(count: int) -> str:
    if count == 0:
        return "none"
    if count <= 5:
        return "low"
    return "high"


def _puzzling_answer_count_bucket(count: int) -> str:
    if count <= 1:
        return "single_answer"
    if count <= 4:
        return "several_answers"
    return "many_answers"


def _group_targets(sample_size: int, groups: tuple[str, ...]) -> dict[str, int]:
    base = sample_size // len(groups)
    remainder = sample_size % len(groups)
    return {group: base + (1 if index < remainder else 0) for index, group in enumerate(groups)}


def _take_from_pool(
    pool: list[dict[str, Any]],
    *,
    group: str,
    count: int,
    rng: random.Random,
    selected_ids: set[str],
) -> list[dict[str, Any]]:
    candidates = list(pool)
    rng.shuffle(candidates)
    taken = []
    for candidate in candidates:
        question_id = str(candidate["question"].get("question_id", "")).strip()
        if question_id in selected_ids:
            continue
        selected_ids.add(question_id)
        taken.append({**candidate, "sample_group": group})
        if len(taken) >= count:
            break
    return taken


def _with_record_indexes(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**record, "record_index": str(index)} for index, record in enumerate(records, 1)]


def _parse_date(value: str) -> datetime:
    parsed = _parse_datetime(value)
    if parsed is None:
        raise PuzzlingError(f"invalid date: {value}")
    return parsed


def _parse_datetime(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).replace(tzinfo=None)
    except ValueError:
        try:
            return datetime.strptime(text[:10], "%Y-%m-%d")
        except ValueError:
            return None


def _float_or_none(value: Any) -> float | None:
    try:
        text = str(value).strip()
        return float(text) if text else None
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    try:
        text = str(value).strip()
        return int(float(text)) if text else None
    except (TypeError, ValueError):
        return None


def _int_or_text(value: Any) -> tuple[int, str]:
    text = str(value or "").strip()
    try:
        return (int(text), text)
    except ValueError:
        return (0, text)


def _puzzling_qualitative_acceptance_gate(
    *,
    coded_records: int,
    accepted_or_diagnostic: int,
    exclude_count: int,
    unclear_solution: int,
) -> str:
    if coded_records < 30:
        return "not_accepted"
    if accepted_or_diagnostic / coded_records < 0.70:
        return "not_accepted"
    if exclude_count / coded_records > 0.20:
        return "not_accepted"
    if unclear_solution / coded_records > 0.30:
        return "not_accepted"
    return "accepted"


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


def _excluded(selection: PuzzlingSelectionResult | None, key: str) -> int:
    return selection.excluded_counts[key] if selection else 0


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _display_optional(path: Path | None, root: Path) -> str:
    return "not produced" if path is None else _display_path(path, root)


def _package_version() -> str:
    try:
        return version("stackexchange-difficulty")
    except PackageNotFoundError:
        return "0.1.0"
