from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from stackexchange_difficulty.inspection import LABEL_COLUMNS, REVIEW_COLUMNS
from stackexchange_difficulty.inspection_diagnostics import (
    InspectionDiagnosticsError,
    diagnose_inspection_strata,
)
from stackexchange_difficulty.validation import Table, read_table


def test_diagnostic_joins_review_and_labels_by_record_index(tmp_path):
    review_path, labels_path = write_diagnostic_fixture(tmp_path)
    out = tmp_path / "diagnostic.md"

    result = diagnose_inspection_strata(
        review=read_table(review_path, name="inspection_review"),
        labels=read_table(labels_path, name="inspection_labels"),
        output_path=out,
    )

    text = out.read_text(encoding="utf-8")
    assert result.inspected == 3
    assert result.unsafe_content_markers == 0
    assert "# Target-Scale Inspection Diagnostics" in text
    assert "## Label Summary" in text
    assert "Suitable records: yes=2, no=1, uncertain=0" in text
    assert "Answerability clear: yes=2, no=1, uncertain=0" in text
    assert "Needs comments: yes=1, no=2, uncertain=0" in text
    assert "answered;accepted;open;not_duplicate;short_latency;tag_bucket:high=2" in text
    assert "score_bucket: low=2, negative=1" in text
    assert "latency_bucket: under_1h=1, under_24h=1, under_7d=1" in text
    assert "Recommend using sample_profile=answerable_clean" in text


def test_diagnostic_rejects_duplicate_label_record_index(tmp_path):
    review_path, labels_path = write_diagnostic_fixture(tmp_path)
    rows = read_rows(labels_path)
    rows[1]["record_index"] = rows[0]["record_index"]
    write_rows(labels_path, LABEL_COLUMNS, rows)

    with pytest.raises(InspectionDiagnosticsError, match="duplicate record_index"):
        diagnose_inspection_strata(
            review=read_table(review_path, name="inspection_review"),
            labels=read_table(labels_path, name="inspection_labels"),
            output_path=tmp_path / "diagnostic.md",
        )


def test_diagnostic_rejects_label_without_matching_review_row(tmp_path):
    review_path, labels_path = write_diagnostic_fixture(tmp_path)
    rows = read_rows(labels_path)
    rows[0]["record_index"] = "999"
    write_rows(labels_path, LABEL_COLUMNS, rows)

    with pytest.raises(InspectionDiagnosticsError, match="does not match any review row"):
        diagnose_inspection_strata(
            review=read_table(review_path, name="inspection_review"),
            labels=read_table(labels_path, name="inspection_labels"),
            output_path=tmp_path / "diagnostic.md",
        )


def test_diagnostic_rejects_missing_review_columns(tmp_path):
    _review_path, labels_path = write_diagnostic_fixture(tmp_path)
    review = Table(
        name="inspection_review",
        columns=("record_index",),
        rows=[{"record_index": "1"}],
    )

    with pytest.raises(InspectionDiagnosticsError, match="inspection_review is missing"):
        diagnose_inspection_strata(
            review=review,
            labels=read_table(labels_path, name="inspection_labels"),
            output_path=tmp_path / "diagnostic.md",
        )


def test_diagnostic_rejects_missing_label_columns(tmp_path):
    review_path, _labels_path = write_diagnostic_fixture(tmp_path)
    labels = Table(
        name="inspection_labels",
        columns=("record_index",),
        rows=[{"record_index": "1"}],
    )

    with pytest.raises(InspectionDiagnosticsError, match="inspection_labels is missing"):
        diagnose_inspection_strata(
            review=read_table(review_path, name="inspection_review"),
            labels=labels,
            output_path=tmp_path / "diagnostic.md",
        )


def test_diagnostic_rejects_invalid_controlled_label_values(tmp_path):
    review_path, labels_path = write_diagnostic_fixture(tmp_path)
    rows = read_rows(labels_path)
    rows[0]["suitable"] = "maybe"
    write_rows(labels_path, LABEL_COLUMNS, rows)

    with pytest.raises(InspectionDiagnosticsError, match="invalid suitable"):
        diagnose_inspection_strata(
            review=read_table(review_path, name="inspection_review"),
            labels=read_table(labels_path, name="inspection_labels"),
            output_path=tmp_path / "diagnostic.md",
        )


def test_diagnostic_rejects_non_generic_notes(tmp_path):
    review_path, labels_path = write_diagnostic_fixture(tmp_path)
    rows = read_rows(labels_path)
    rows[0]["notes"] = "copied formula x+y from sensitive row"
    write_rows(labels_path, LABEL_COLUMNS, rows)

    with pytest.raises(InspectionDiagnosticsError, match="non-generic note"):
        diagnose_inspection_strata(
            review=read_table(review_path, name="inspection_review"),
            labels=read_table(labels_path, name="inspection_labels"),
            output_path=tmp_path / "diagnostic.md",
        )


def test_diagnostic_output_excludes_row_content_and_individual_ids(tmp_path):
    review_path, labels_path = write_diagnostic_fixture(tmp_path)
    out = tmp_path / "diagnostic.md"

    diagnose_inspection_strata(
        review=read_table(review_path, name="inspection_review"),
        labels=read_table(labels_path, name="inspection_labels"),
        output_path=out,
    )

    text = out.read_text(encoding="utf-8")
    assert "question_id" not in text
    assert "Sensitive diagnostic title" not in text
    assert "Sensitive diagnostic body" not in text
    assert "Sensitive diagnostic answer" not in text
    assert "answers_for_review" not in text
    assert "<p>" not in text
    assert "https://" not in text


def test_diagnostic_cli_writes_aggregate_output(tmp_path):
    review_path, labels_path = write_diagnostic_fixture(tmp_path)
    out = tmp_path / "diagnostic.md"

    result = run_cli(
        [
            "diagnose-inspection-strata",
            "--review",
            str(review_path),
            "--labels",
            str(labels_path),
            "--out",
            str(out),
        ]
    )

    payload = json.loads(result.stdout)
    text = out.read_text(encoding="utf-8")
    assert result.returncode == 0
    assert payload["ok"] is True
    assert payload["inspected"] == 3
    assert payload["unsafe_content_markers"] == 0
    assert "Sensitive diagnostic title" not in result.stdout
    assert "Sensitive diagnostic title" not in text
    assert "## Metadata Buckets" in text


def write_diagnostic_fixture(tmp_path: Path) -> tuple[Path, Path]:
    review_path = tmp_path / "review.tsv"
    labels_path = tmp_path / "labels.tsv"
    review_rows = [
        review_row(
            "1",
            question_id="101",
            sample_stratum="answered;accepted;open;not_duplicate;short_latency;tag_bucket:high",
            score="2",
            view_count="1000",
            comment_count="0",
            latency="0.5",
            tag_bucket="high",
        ),
        review_row(
            "2",
            question_id="102",
            sample_stratum="answered;accepted;open;not_duplicate;long_latency;tag_bucket:low",
            score="-1",
            view_count="100",
            comment_count="5",
            latency="48",
            tag_bucket="low",
        ),
        review_row(
            "3",
            question_id="103",
            sample_stratum="answered;accepted;open;not_duplicate;short_latency;tag_bucket:high",
            score="1",
            view_count="6000",
            comment_count="1",
            latency="3",
            tag_bucket="high",
        ),
    ]
    label_rows = [
        label_row("1", sample_stratum=review_rows[0]["sample_stratum"], reason_code="good"),
        label_row(
            "2",
            sample_stratum=review_rows[1]["sample_stratum"],
            suitable="no",
            answerability_clear="no",
            needs_comments="yes",
            reason_code="unclear_answerability",
            notes="generic_answerability_unclear",
        ),
        label_row("3", sample_stratum=review_rows[2]["sample_stratum"], reason_code="good"),
    ]
    write_rows(review_path, REVIEW_COLUMNS, review_rows)
    write_rows(labels_path, LABEL_COLUMNS, label_rows)
    return review_path, labels_path


def review_row(
    record_index: str,
    *,
    question_id: str,
    sample_stratum: str,
    score: str,
    view_count: str,
    comment_count: str,
    latency: str,
    tag_bucket: str,
) -> dict[str, str]:
    return {
        "record_index": record_index,
        "sample_stratum": sample_stratum,
        "question_id": question_id,
        "title": f"Sensitive diagnostic title {question_id}",
        "body_html": f"<p>Sensitive diagnostic body {question_id}</p>",
        "tags": "<diagnostic>",
        "creation_date": "2026-01-01T00:00:00+00:00",
        "score": score,
        "view_count": view_count,
        "answer_count": "1",
        "comment_count": comment_count,
        "closed_date": "",
        "accepted_answer_id": f"2{question_id}",
        "is_duplicate": "false",
        "content_license": "CC BY-SA 4.0",
        "indicator_has_answer": "true",
        "indicator_has_accepted_answer": "true",
        "indicator_is_unanswered": "false",
        "indicator_is_closed": "false",
        "indicator_is_duplicate": "false",
        "indicator_time_to_first_answer_hours": latency,
        "indicator_tag_popularity_bucket": tag_bucket,
        "answers_for_review": (
            f"answer_id=2{question_id}\nSensitive diagnostic answer {question_id}"
        ),
    }


def label_row(
    record_index: str,
    *,
    sample_stratum: str,
    suitable: str = "yes",
    answerability_clear: str = "yes",
    math_notation_readable: str = "yes",
    needs_comments: str = "no",
    reason_code: str,
    notes: str = "",
) -> dict[str, str]:
    return {
        "record_index": record_index,
        "sample_stratum": sample_stratum,
        "suitable": suitable,
        "answerability_clear": answerability_clear,
        "math_notation_readable": math_notation_readable,
        "needs_comments": needs_comments,
        "reason_code": reason_code,
        "notes": notes,
    }


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_rows(
    path: Path,
    fieldnames: tuple[str, ...] | list[str],
    rows: list[dict[str, str]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


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
