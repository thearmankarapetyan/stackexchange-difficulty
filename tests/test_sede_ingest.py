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


def test_preflight_sede_cli_writes_hash_and_accepts_custom_row_bounds(tmp_path):
    hash_out = tmp_path / "sede.tsv.sha256"

    result = run_cli(
        [
            "preflight-sede",
            "--export",
            "tests/fixtures/sede_pilot_export.tsv",
            "--min-rows",
            "1",
            "--max-rows",
            "10",
            "--hash-out",
            str(hash_out),
        ]
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["ok"] is True
    assert payload["rows"] == 2
    assert payload["hash_out"] == str(hash_out)
    assert hash_out.exists()


def test_preflight_sede_cli_rejects_out_of_range_row_count(tmp_path):
    result = run_cli(
        [
            "preflight-sede",
            "--export",
            "tests/fixtures/sede_pilot_export.tsv",
            "--min-rows",
            "5000",
            "--max-rows",
            "10000",
            "--hash-out",
            str(tmp_path / "sede.tsv.sha256"),
        ]
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["ok"] is False
    assert any(issue["code"] == "row_count_out_of_range" for issue in payload["issues"])


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


def test_ingest_sede_outputs_can_feed_derive_cli(tmp_path):
    out_dir = tmp_path / "out"
    derived_dir = tmp_path / "derived"

    ingest_result = run_cli(
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
    derive_result = run_cli(
        [
            "derive",
            "--questions",
            str(out_dir / "questions.tsv"),
            "--answers",
            str(out_dir / "answers.tsv"),
            "--comments",
            str(out_dir / "comments.tsv"),
            "--provenance",
            str(out_dir / "provenance.json"),
            "--out-dir",
            str(derived_dir),
        ]
    )

    assert ingest_result.returncode == 0
    assert derive_result.returncode == 0
    assert (derived_dir / "derived_thread_indicators.tsv").exists()
    assert (derived_dir / "threads.jsonl").exists()


def test_finalize_provenance_cli_replaces_pending_output_hash(tmp_path):
    provenance_path = tmp_path / "provenance.json"
    hash_manifest = tmp_path / "processed-output.sha256"
    out_path = tmp_path / "finalized.json"
    provenance = load_provenance("tests/fixtures/sede_provenance.json")
    provenance["processed_output_hash"] = "sha256:pending-before-processing"
    provenance["output_hash"] = "sha256:pending-before-processing"
    provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
    hash_manifest.write_text("abc123  questions.tsv\n", encoding="utf-8")

    result = run_cli(
        [
            "finalize-provenance",
            "--provenance",
            str(provenance_path),
            "--hash-file",
            str(hash_manifest),
            "--out",
            str(out_path),
        ]
    )

    finalized = json.loads(out_path.read_text(encoding="utf-8"))
    assert result.returncode == 0
    assert finalized["processed_output_hash"].startswith("sha256:")
    assert finalized["processed_output_hash"] == finalized["output_hash"]
    assert "pending" not in finalized["output_hash"]
    assert finalized["processed_hash_manifest"] == str(hash_manifest)


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
