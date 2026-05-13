from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from stackexchange_difficulty.inspection import (
    InspectionError,
    prepare_comment_reinspection_files,
    prepare_inspection_files,
    summarize_comment_reinspection_labels,
    summarize_inspection_labels,
)
from stackexchange_difficulty.validation import Table, read_table


def test_prepare_inspection_is_deterministic_and_covers_available_strata(tmp_path):
    questions, answers, indicators = inspection_tables()
    out_one = tmp_path / "data/processed/stackexchange-difficulty/inspection-one"
    out_two = tmp_path / "data/processed/stackexchange-difficulty/inspection-two"

    first = prepare_inspection_files(
        questions=questions,
        answers=answers,
        indicators=indicators,
        site_slug="math",
        pilot_date="2026-05-13",
        sample_size=6,
        out_dir=out_one,
        seed=7,
    )
    second = prepare_inspection_files(
        questions=questions,
        answers=answers,
        indicators=indicators,
        site_slug="math",
        pilot_date="2026-05-13",
        sample_size=6,
        out_dir=out_two,
        seed=7,
    )

    first_labels = first.labels_path.read_text(encoding="utf-8")
    second_labels = second.labels_path.read_text(encoding="utf-8")
    assert first_labels == second_labels
    assert "unanswered" in first_labels
    assert "closed" in first_labels
    assert "duplicate" in first_labels
    assert "long_latency" in first_labels
    assert "tag_bucket:low" in first_labels


def test_prepare_inspection_cli_does_not_print_sampled_content(tmp_path):
    questions, answers, indicators = inspection_tables()
    questions_path = tmp_path / "questions.tsv"
    answers_path = tmp_path / "answers.tsv"
    indicators_path = tmp_path / "derived_thread_indicators.tsv"
    write_table(questions_path, questions)
    write_table(answers_path, answers)
    write_table(indicators_path, indicators)
    out_dir = tmp_path / "data/processed/stackexchange-difficulty/inspection"

    result = run_cli(
        [
            "prepare-inspection",
            "--questions",
            str(questions_path),
            "--answers",
            str(answers_path),
            "--indicators",
            str(indicators_path),
            "--site-slug",
            "math",
            "--pilot-date",
            "2026-05-13",
            "--sample-size",
            "4",
            "--out-dir",
            str(out_dir),
        ]
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["ok"] is True
    assert "Sensitive synthetic title" not in result.stdout
    assert "Sensitive synthetic body" not in result.stdout
    assert "Sensitive synthetic answer" not in result.stdout
    labels = read_table(payload["labels"], name="labels")
    assert "question_id" not in labels.columns
    assert "title" not in labels.columns
    assert "body_html" not in labels.columns


def test_prepare_inspection_rejects_tracked_looking_out_dir(tmp_path):
    questions, answers, indicators = inspection_tables()

    with pytest.raises(InspectionError, match="data/processed/stackexchange-difficulty"):
        prepare_inspection_files(
            questions=questions,
            answers=answers,
            indicators=indicators,
            site_slug="math",
            pilot_date="2026-05-13",
            sample_size=2,
            out_dir=tmp_path / "reports/inspection",
        )


def test_prepare_comment_reinspection_selects_only_records_needing_comments(tmp_path):
    review_path = tmp_path / "review.tsv"
    review_path.write_text(
        "\t".join(
            [
                "record_index",
                "sample_stratum",
                "question_id",
                "title",
                "body_html",
                "tags",
                "creation_date",
                "score",
                "view_count",
                "answer_count",
                "comment_count",
                "closed_date",
                "accepted_answer_id",
                "is_duplicate",
                "content_license",
                "indicator_has_answer",
                "indicator_has_accepted_answer",
                "indicator_is_unanswered",
                "indicator_is_closed",
                "indicator_is_duplicate",
                "indicator_time_to_first_answer_hours",
                "indicator_tag_popularity_bucket",
                "answers_for_review",
            ]
        )
        + "\n"
        + "1\tanswered\t101\tSensitive title\tSensitive body\t<math>\t2026-01-01\t"
        + "0\t1\t1\t1\t\t201\tfalse\tCC BY-SA\ttrue\ttrue\tfalse\tfalse\tfalse\t"
        + "1.0\tlow\tanswer_id=201\n"
        + "2\tanswered\t102\tOther title\tOther body\t<math>\t2026-01-02\t"
        + "0\t1\t1\t0\t\t\tfalse\tCC BY-SA\ttrue\tfalse\tfalse\tfalse\tfalse\t"
        + "1.0\tlow\tanswer_id=202\n",
        encoding="utf-8",
    )
    labels_path = tmp_path / "labels.tsv"
    labels_path.write_text(
        "\t".join(
            [
                "record_index",
                "sample_stratum",
                "suitable",
                "answerability_clear",
                "math_notation_readable",
                "needs_comments",
                "reason_code",
                "notes",
            ]
        )
        + "\n1\tanswered\tuncertain\tuncertain\tyes\tyes\tneeds_comments\t\n"
        + "2\tanswered\tyes\tyes\tyes\tno\tgood\t\n",
        encoding="utf-8",
    )
    comments_path = tmp_path / "comments.tsv"
    comments_path.write_text(
        "comment_id\tpost_id\tquestion_id\ttext\tscore\tcreation_date\n"
        "301\t101\t101\tSensitive comment text\t1\t2026-01-01T00:00:00+00:00\n"
        "302\t201\t101\tSensitive answer comment\t0\t2026-01-01T01:00:00+00:00\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "data/processed/stackexchange-difficulty/reinspection"

    result = prepare_comment_reinspection_files(
        review=read_table(review_path, name="inspection_review"),
        labels=read_table(labels_path, name="inspection_labels"),
        comments=read_table(comments_path, name="comments"),
        out_dir=out_dir,
    )

    review_text = result.review_path.read_text(encoding="utf-8")
    labels = read_table(result.labels_path, name="labels")
    assert result.selected_records == 1
    assert "Sensitive comment text" in review_text
    assert "Sensitive answer comment" in review_text
    assert "Other title" not in review_text
    assert len(labels.rows) == 1
    assert labels.rows[0]["record_index"] == "1"


def test_summarize_inspection_updates_audit_with_aggregate_counts_only(tmp_path):
    labels_path = tmp_path / "labels.tsv"
    labels_path.write_text(
        "\t".join(
            [
                "record_index",
                "sample_stratum",
                "suitable",
                "answerability_clear",
                "math_notation_readable",
                "needs_comments",
                "reason_code",
                "notes",
            ]
        )
        + "\n"
        + "1\tanswered\tyes\tyes\tyes\tno\tgood\tDo not leak this title\n"
        + "2\tunanswered\tno\tno\tyes\tyes\tneeds_comments\tAnother copied note\n",
        encoding="utf-8",
    )
    audit = tmp_path / "audit.md"
    audit.write_text(
        "# SEDE Pilot Audit\n\n"
        "## Manual Inspection\n\n"
        "Pending.\n\n"
        "## Decision\n\n"
        "- Decision: pending.\n",
        encoding="utf-8",
    )

    result = summarize_inspection_labels(
        labels=read_table(labels_path, name="inspection_labels"),
        audit_path=audit,
        labeler="llm_assisted",
    )

    text = audit.read_text(encoding="utf-8")
    assert result.inspected == 2
    assert "## Inspection Summary" in text
    assert "Labeling method: llm_assisted" in text
    assert "Decision profile: standard" in text
    assert "Suitable records: yes=1, no=1, uncertain=0" in text
    assert "Top reason codes: good=1, needs_comments=1" in text
    assert "Do not leak this title" not in text
    assert "Another copied note" not in text


def test_standard_inspection_profile_preserves_larger_design_recommendation(tmp_path):
    labels_path = tmp_path / "labels.tsv"
    write_labels(labels_path, rows=5, suitable_yes=4, answerability_yes=5, notation_yes=5)
    audit = write_pending_audit(tmp_path)

    result = summarize_inspection_labels(
        labels=read_table(labels_path, name="inspection_labels"),
        audit_path=audit,
    )

    text = audit.read_text(encoding="utf-8")
    assert result.recommendation == "go_for_larger_design"
    assert "Decision profile: standard" in text
    assert "Recommendation: go_for_larger_design" in text


def test_answerable_pilot_profile_returns_ready_when_thresholds_pass(tmp_path):
    labels_path = tmp_path / "labels.tsv"
    write_labels(
        labels_path,
        rows=100,
        suitable_yes=93,
        answerability_yes=95,
        notation_yes=100,
        needs_comments_yes=4,
        copied_note="Do not leak this formula or answer text",
    )
    audit = write_pending_audit(tmp_path)

    result = summarize_inspection_labels(
        labels=read_table(labels_path, name="inspection_labels"),
        audit_path=audit,
        labeler="llm_assisted",
        decision_profile="answerable_pilot",
    )

    text = audit.read_text(encoding="utf-8")
    assert result.inspected == 100
    assert result.recommendation == "ready_for_data_dump_design"
    assert "Labeling method: llm_assisted" in text
    assert "Decision profile: answerable_pilot" in text
    assert "Suitable records: yes=93, no=7, uncertain=0" in text
    assert "Answerability clear: yes=95, no=5, uncertain=0" in text
    assert "Math notation readable: yes=100, no=0, uncertain=0" in text
    assert "Needs comments: yes=4, no=96, uncertain=0" in text
    assert "Recommendation: ready_for_data_dump_design" in text
    assert "Decision: ready_for_data_dump_design" in text
    assert "Do not leak this formula" not in text


def test_answerable_pilot_profile_requires_100_records(tmp_path):
    labels_path = tmp_path / "labels.tsv"
    write_labels(labels_path, rows=99, suitable_yes=99, answerability_yes=99, notation_yes=99)
    audit = write_pending_audit(tmp_path)

    result = summarize_inspection_labels(
        labels=read_table(labels_path, name="inspection_labels"),
        audit_path=audit,
        decision_profile="answerable_pilot",
    )

    assert result.recommendation == "inspection_review_required"


def test_answerable_pilot_profile_requests_comment_enrichment(tmp_path):
    labels_path = tmp_path / "labels.tsv"
    write_labels(
        labels_path,
        rows=100,
        suitable_yes=100,
        answerability_yes=100,
        notation_yes=100,
        needs_comments_yes=11,
    )
    audit = write_pending_audit(tmp_path)

    result = summarize_inspection_labels(
        labels=read_table(labels_path, name="inspection_labels"),
        audit_path=audit,
        decision_profile="answerable_pilot",
    )

    assert result.recommendation == "needs_comment_enrichment"


@pytest.mark.parametrize(
    ("suitable_yes", "answerability_yes", "notation_yes"),
    [
        (79, 100, 100),
        (100, 79, 100),
        (100, 100, 94),
    ],
)
def test_answerable_pilot_profile_revises_query_when_thresholds_fail(
    tmp_path,
    suitable_yes,
    answerability_yes,
    notation_yes,
):
    labels_path = tmp_path / "labels.tsv"
    write_labels(
        labels_path,
        rows=100,
        suitable_yes=suitable_yes,
        answerability_yes=answerability_yes,
        notation_yes=notation_yes,
    )
    audit = write_pending_audit(tmp_path)

    result = summarize_inspection_labels(
        labels=read_table(labels_path, name="inspection_labels"),
        audit_path=audit,
        decision_profile="answerable_pilot",
    )

    assert result.recommendation == "revise_sede_query"


def test_summarize_inspection_rejects_unknown_decision_profile(tmp_path):
    labels_path = tmp_path / "labels.tsv"
    write_labels(labels_path, rows=1)
    audit = write_pending_audit(tmp_path)

    with pytest.raises(InspectionError, match="unknown decision profile"):
        summarize_inspection_labels(
            labels=read_table(labels_path, name="inspection_labels"),
            audit_path=audit,
            decision_profile="broad_pilot",
        )


def test_summarize_inspection_cli_accepts_answerable_profile(tmp_path):
    labels_path = tmp_path / "labels.tsv"
    write_labels(
        labels_path,
        rows=100,
        suitable_yes=100,
        answerability_yes=100,
        notation_yes=100,
    )
    audit = write_pending_audit(tmp_path)

    result = run_cli(
        [
            "summarize-inspection",
            "--labels",
            str(labels_path),
            "--audit",
            str(audit),
            "--labeler",
            "llm_assisted",
            "--decision-profile",
            "answerable_pilot",
        ]
    )

    payload = json.loads(result.stdout)
    text = audit.read_text(encoding="utf-8")
    assert result.returncode == 0
    assert payload["recommendation"] == "ready_for_data_dump_design"
    assert "Decision profile: answerable_pilot" in text


def test_summarize_inspection_missing_columns_fails(tmp_path):
    labels = tmp_path / "labels.tsv"
    labels.write_text("record_index\tsuitable\n1\tyes\n", encoding="utf-8")
    audit = tmp_path / "audit.md"
    audit.write_text("# Audit\n", encoding="utf-8")

    with pytest.raises(InspectionError, match="missing required columns"):
        summarize_inspection_labels(
            labels=read_table(labels, name="inspection_labels"),
            audit_path=audit,
        )


def test_summarize_inspection_rejects_free_text_reason_codes(tmp_path):
    labels = tmp_path / "labels.tsv"
    labels.write_text(
        "\t".join(
            [
                "record_index",
                "sample_stratum",
                "suitable",
                "answerability_clear",
                "math_notation_readable",
                "needs_comments",
                "reason_code",
                "notes",
            ]
        )
        + "\n1\tanswered\tyes\tyes\tyes\tno\tcopied sentence here\t\n",
        encoding="utf-8",
    )
    audit = tmp_path / "audit.md"
    audit.write_text("# Audit\n", encoding="utf-8")

    with pytest.raises(InspectionError, match="reason_code"):
        summarize_inspection_labels(
            labels=read_table(labels, name="inspection_labels"),
            audit_path=audit,
        )


def test_summarize_inspection_rejects_unsafe_labeler(tmp_path):
    labels = tmp_path / "labels.tsv"
    labels.write_text(
        "\t".join(
            [
                "record_index",
                "sample_stratum",
                "suitable",
                "answerability_clear",
                "math_notation_readable",
                "needs_comments",
                "reason_code",
                "notes",
            ]
        )
        + "\n1\tanswered\tyes\tyes\tyes\tno\tgood\t\n",
        encoding="utf-8",
    )
    audit = tmp_path / "audit.md"
    audit.write_text("# Audit\n", encoding="utf-8")

    with pytest.raises(InspectionError, match="labeler"):
        summarize_inspection_labels(
            labels=read_table(labels, name="inspection_labels"),
            audit_path=audit,
            labeler="LLM assisted with copied text",
        )


def test_summarize_comment_reinspection_preserves_original_inspection_summary(tmp_path):
    labels_path = tmp_path / "llm_reinspection_labels.tsv"
    labels_path.write_text(
        "\t".join(
            [
                "record_index",
                "sample_stratum",
                "suitable",
                "answerability_clear",
                "math_notation_readable",
                "needs_comments",
                "reason_code",
                "notes",
            ]
        )
        + "\n"
        + "1\tanswered\tyes\tyes\tyes\tno\tresolved_with_comments\t"
        + "Do not leak this comment\n"
        + "2\tanswered\tyes\tyes\tyes\tno\tresolved_with_comments\t"
        + "Do not leak this title\n",
        encoding="utf-8",
    )
    audit = tmp_path / "audit.md"
    audit.write_text(
        "# SEDE Pilot Audit\n\n"
        "## Inspection Summary\n\n"
        "- Original summary stays here.\n\n"
        "## Comment Enrichment\n\n"
        "- Comment rows: 12.\n\n"
        "## Comment-Enriched LLM Reinspection\n\n"
        "- Status: pending.\n\n"
        "## Comment-Enriched Decision\n\n"
        "- Decision: needs_more_comment_coverage.\n\n"
        "## Decision\n\n"
        "- Decision: needs_comment_enrichment.\n",
        encoding="utf-8",
    )

    result = summarize_comment_reinspection_labels(
        labels=read_table(labels_path, name="comment_reinspection_labels"),
        audit_path=audit,
    )

    text = audit.read_text(encoding="utf-8")
    assert result.inspected == 2
    assert result.recommendation == "ready_for_data_dump_design"
    assert "## Inspection Summary" in text
    assert "- Original summary stays here." in text
    assert "## Comment-Enriched LLM Reinspection" in text
    assert "Reinspected records: 2" in text
    assert "Still needs comments: yes=0, no=2, uncertain=0" in text
    assert "Recommendation: ready_for_data_dump_design" in text
    assert "## Comment-Enriched Decision" in text
    assert "Decision: ready_for_data_dump_design" in text
    assert "Do not leak this comment" not in text
    assert "Do not leak this title" not in text


def test_summarize_comment_reinspection_can_request_more_comment_coverage(tmp_path):
    labels_path = tmp_path / "llm_reinspection_labels.tsv"
    labels_path.write_text(
        "\t".join(
            [
                "record_index",
                "sample_stratum",
                "suitable",
                "answerability_clear",
                "math_notation_readable",
                "needs_comments",
                "reason_code",
                "notes",
            ]
        )
        + "\n"
        + "1\tanswered\tyes\tyes\tyes\tyes\tstill_missing_context\t\n"
        + "2\tanswered\tyes\tyes\tyes\tno\tresolved_with_comments\t\n",
        encoding="utf-8",
    )
    audit = tmp_path / "audit.md"
    audit.write_text(
        "# SEDE Pilot Audit\n\n## Decision\n\n- Decision: pending.\n",
        encoding="utf-8",
    )

    result = summarize_comment_reinspection_labels(
        labels=read_table(labels_path, name="comment_reinspection_labels"),
        audit_path=audit,
        labeler="llm_assisted_comment_enriched",
    )

    text = audit.read_text(encoding="utf-8")
    assert result.recommendation == "needs_more_comment_coverage"
    assert "## Comment-Enriched LLM Reinspection" in text
    assert "Recommendation: needs_more_comment_coverage" in text
    assert "Decision: needs_more_comment_coverage" in text


def test_summarize_comment_reinspection_missing_columns_fails(tmp_path):
    labels = tmp_path / "llm_reinspection_labels.tsv"
    labels.write_text("record_index\tsuitable\n1\tyes\n", encoding="utf-8")
    audit = tmp_path / "audit.md"
    audit.write_text("# Audit\n", encoding="utf-8")

    with pytest.raises(InspectionError, match="missing required columns"):
        summarize_comment_reinspection_labels(
            labels=read_table(labels, name="comment_reinspection_labels"),
            audit_path=audit,
        )


def test_summarize_comment_reinspection_cli_does_not_print_label_notes(tmp_path):
    labels_path = tmp_path / "llm_reinspection_labels.tsv"
    labels_path.write_text(
        "\t".join(
            [
                "record_index",
                "sample_stratum",
                "suitable",
                "answerability_clear",
                "math_notation_readable",
                "needs_comments",
                "reason_code",
                "notes",
            ]
        )
        + "\n1\tanswered\tyes\tyes\tyes\tno\tresolved_with_comments\t"
        + "Sensitive copied post text\n",
        encoding="utf-8",
    )
    audit = tmp_path / "audit.md"
    audit.write_text("# Audit\n", encoding="utf-8")

    result = run_cli(
        [
            "summarize-comment-reinspection",
            "--labels",
            str(labels_path),
            "--audit",
            str(audit),
        ]
    )

    assert result.returncode == 0
    assert "Sensitive copied post text" not in result.stdout
    assert "Sensitive copied post text" not in audit.read_text(encoding="utf-8")


def test_inspection_paths_are_ignored_by_git():
    paths = [
        "data/processed/stackexchange-difficulty/pilot-math-2026-05-13-inspection/review.tsv",
        "data/processed/stackexchange-difficulty/pilot-math-2026-05-13-inspection/labels.tsv",
    ]
    for path in paths:
        result = subprocess.run(
            ["git", "check-ignore", path],
            cwd=Path.cwd(),
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, path


def inspection_tables() -> tuple[Table, Table, Table]:
    questions = Table(
        name="questions",
        columns=(
            "question_id",
            "title",
            "body_html",
            "tags",
            "creation_date",
            "score",
            "view_count",
            "answer_count",
            "comment_count",
            "closed_date",
            "accepted_answer_id",
            "is_duplicate",
            "content_license",
        ),
        rows=[
            question("101", answer_count="1", accepted_answer_id="201", tags="<algebra>"),
            question("102", answer_count="0", tags="<topology>", closed_date="2026-01-02"),
            question("103", answer_count="1", tags="<logic>", is_duplicate="true"),
            question("104", answer_count="1", tags="<rare>"),
            question("105", answer_count="1", tags="<analysis>"),
            question("106", answer_count="1", tags="<geometry>"),
            question("107", answer_count="1", tags="<number-theory>"),
            question("108", answer_count="0", tags="<probability>"),
        ],
    )
    answers = Table(
        name="answers",
        columns=("answer_id", "question_id", "body_html", "score", "creation_date", "is_accepted"),
        rows=[
            answer("201", "101", is_accepted="true"),
            answer("203", "103"),
            answer("204", "104"),
            answer("205", "105"),
            answer("206", "106"),
            answer("207", "107"),
        ],
    )
    indicators = Table(
        name="derived_thread_indicators",
        columns=(
            "question_id",
            "has_answer",
            "has_accepted_answer",
            "is_unanswered",
            "is_closed",
            "is_duplicate",
            "time_to_first_answer_hours",
            "tag_popularity_bucket",
        ),
        rows=[
            indicator("101", has_answer="True", accepted="True", bucket="high"),
            indicator("102", has_answer="False", closed="True", timing="", bucket="medium"),
            indicator("103", duplicate="True", timing="48", bucket="low"),
            indicator("104", bucket="low"),
            indicator("105", bucket="medium"),
            indicator("106", bucket="high"),
            indicator("107", bucket="high"),
            indicator("108", has_answer="False", timing="", bucket="none"),
        ],
    )
    return questions, answers, indicators


def question(
    question_id: str,
    *,
    answer_count: str,
    accepted_answer_id: str = "",
    tags: str,
    closed_date: str = "",
    is_duplicate: str = "false",
) -> dict[str, str]:
    return {
        "question_id": question_id,
        "title": f"Sensitive synthetic title {question_id}",
        "body_html": f"<p>Sensitive synthetic body {question_id}</p>",
        "tags": tags,
        "creation_date": "2026-01-01T00:00:00+00:00",
        "score": "1",
        "view_count": "10",
        "answer_count": answer_count,
        "comment_count": "0",
        "closed_date": closed_date,
        "accepted_answer_id": accepted_answer_id,
        "is_duplicate": is_duplicate,
        "content_license": "CC BY-SA 4.0",
    }


def answer(answer_id: str, question_id: str, *, is_accepted: str = "false") -> dict[str, str]:
    return {
        "answer_id": answer_id,
        "question_id": question_id,
        "body_html": f"<p>Sensitive synthetic answer {answer_id}</p>",
        "score": "2",
        "creation_date": "2026-01-01T01:00:00+00:00",
        "is_accepted": is_accepted,
    }


def indicator(
    question_id: str,
    *,
    has_answer: str = "True",
    accepted: str = "False",
    closed: str = "False",
    duplicate: str = "False",
    timing: str = "1",
    bucket: str,
) -> dict[str, str]:
    return {
        "question_id": question_id,
        "has_answer": has_answer,
        "has_accepted_answer": accepted,
        "is_unanswered": str(has_answer == "False"),
        "is_closed": closed,
        "is_duplicate": duplicate,
        "time_to_first_answer_hours": timing,
        "tag_popularity_bucket": bucket,
    }


def write_table(path: Path, table: Table) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table.columns), delimiter="\t")
        writer.writeheader()
        writer.writerows(table.rows)


LABEL_FIELDNAMES = [
    "record_index",
    "sample_stratum",
    "suitable",
    "answerability_clear",
    "math_notation_readable",
    "needs_comments",
    "reason_code",
    "notes",
]


def write_labels(
    path: Path,
    *,
    rows: int,
    suitable_yes: int | None = None,
    answerability_yes: int | None = None,
    notation_yes: int | None = None,
    needs_comments_yes: int = 0,
    copied_note: str = "",
) -> None:
    suitable_cutoff = rows if suitable_yes is None else suitable_yes
    answerability_cutoff = rows if answerability_yes is None else answerability_yes
    notation_cutoff = rows if notation_yes is None else notation_yes
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LABEL_FIELDNAMES, delimiter="\t")
        writer.writeheader()
        for index in range(1, rows + 1):
            suitable = "yes" if index <= suitable_cutoff else "no"
            answerability = "yes" if index <= answerability_cutoff else "no"
            notation = "yes" if index <= notation_cutoff else "no"
            needs_comments = "yes" if index <= needs_comments_yes else "no"
            if needs_comments == "yes":
                reason = "still_missing_context"
            elif suitable == "no":
                reason = "unsuitable"
            elif answerability == "no":
                reason = "unclear_answerability"
            elif notation == "no":
                reason = "notation_issue"
            else:
                reason = "good"
            writer.writerow(
                {
                    "record_index": str(index),
                    "sample_stratum": "answered",
                    "suitable": suitable,
                    "answerability_clear": answerability,
                    "math_notation_readable": notation,
                    "needs_comments": needs_comments,
                    "reason_code": reason,
                    "notes": copied_note if index == 1 else "",
                }
            )


def write_pending_audit(tmp_path: Path) -> Path:
    audit = tmp_path / "audit.md"
    audit.write_text(
        "# SEDE Pilot Audit\n\n## Decision\n\n- Decision: pending.\n",
        encoding="utf-8",
    )
    return audit


def run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path.cwd() / "src")
    return subprocess.run(
        [sys.executable, "-m", "stackexchange_difficulty", *args],
        cwd=Path.cwd(),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
