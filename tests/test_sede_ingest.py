from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

from stackexchange_difficulty.provenance import load_provenance
from stackexchange_difficulty.sede import normalize_sede_export, validate_sede_export
from stackexchange_difficulty.validation import read_table, validate_dataset


def test_synthetic_sede_export_normalizes_and_validates():
    export = read_table("tests/fixtures/sede_pilot_export.tsv", name="sede_export")
    provenance = load_provenance("tests/fixtures/sede_provenance.json")

    assert validate_sede_export(export) == []
    questions, answers, comments = normalize_sede_export(export)
    report = validate_dataset(
        questions,
        answers=answers,
        comments=comments,
        provenance=provenance,
    )

    assert report.ok
    assert len(questions.rows) == 2
    assert len(answers.rows) == 1
    assert comments.columns == ("comment_id", "post_id", "text", "score", "creation_date")


def test_sede_export_missing_required_columns_fails():
    export = read_table("tests/fixtures/sede_pilot_export.tsv", name="sede_export")
    broken = type(export)(
        name=export.name,
        rows=export.rows,
        columns=tuple(column for column in export.columns if column != "body_html"),
    )

    issues = validate_sede_export(broken)

    assert len(issues) == 1
    assert issues[0].code == "missing_required_columns"
    assert "body_html" in issues[0].message


def test_ingest_sede_cli_rejects_artificial_ids(tmp_path):
    export_path = tmp_path / "sede.tsv"
    with Path("tests/fixtures/sede_pilot_export.tsv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    rows[0]["question_id"] = "1000000010"
    write_rows(export_path, rows)

    out_dir = tmp_path / "out"
    result = run_cli(
        [
            "ingest-sede",
            "--export",
            str(export_path),
            "--provenance",
            "tests/fixtures/sede_provenance.json",
            "--out-dir",
            str(out_dir),
        ]
    )

    assert result.returncode == 1
    report = json.loads((out_dir / "validation_report.json").read_text(encoding="utf-8"))
    assert any(issue["code"] == "artificial_post_id" for issue in report["issues"])
    assert not (out_dir / "questions.tsv").exists()


def test_ingest_sede_cli_rejects_incomplete_provenance(tmp_path):
    provenance_path = tmp_path / "bad_provenance.json"
    provenance_path.write_text('{"source_method": "sede_pilot_export"}\n', encoding="utf-8")
    out_dir = tmp_path / "out"

    result = run_cli(
        [
            "ingest-sede",
            "--export",
            "tests/fixtures/sede_pilot_export.tsv",
            "--provenance",
            str(provenance_path),
            "--out-dir",
            str(out_dir),
        ]
    )

    assert result.returncode == 1
    report = json.loads((out_dir / "validation_report.json").read_text(encoding="utf-8"))
    assert any(issue["code"] == "provenance_missing_required_key" for issue in report["issues"])
    assert not (out_dir / "questions.tsv").exists()


def test_ingest_sede_cli_writes_normalized_outputs(tmp_path):
    out_dir = tmp_path / "out"

    result = run_cli(
        [
            "ingest-sede",
            "--export",
            "tests/fixtures/sede_pilot_export.tsv",
            "--provenance",
            "tests/fixtures/sede_provenance.json",
            "--out-dir",
            str(out_dir),
        ]
    )

    assert result.returncode == 0
    assert (out_dir / "questions.tsv").exists()
    assert (out_dir / "answers.tsv").exists()
    assert (out_dir / "comments.tsv").exists()
    assert (out_dir / "provenance.json").exists()
    assert json.loads((out_dir / "validation_report.json").read_text(encoding="utf-8"))["ok"]


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
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
