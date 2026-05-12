from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from stackexchange_difficulty.api import run_api_smoke


class FakeResponse:
    status_code = 200
    content = b"{}"

    @staticmethod
    def json():
        return {"quota_max": 10000, "quota_remaining": 9999, "backoff": 2, "items": [{"site": "x"}]}


def test_api_smoke_requires_explicit_live_flag():
    with pytest.raises(ValueError, match="--live"):
        run_api_smoke(live=False)


def test_api_smoke_writes_metadata_only_with_mock(tmp_path):
    out = tmp_path / "api.json"

    metadata = run_api_smoke(
        live=True,
        site="stackoverflow",
        out=out,
        http_get=lambda *args, **kwargs: FakeResponse(),
    )

    stored = json.loads(out.read_text(encoding="utf-8"))
    assert metadata["endpoint"].endswith("/2.3/info")
    assert stored["site"] == "stackoverflow"
    assert stored["http_status"] == 200
    assert stored["quota_max"] == 10000
    assert stored["backoff"] == 2
    assert "items" not in stored


def test_cli_help_works():
    result = run_cli(["--help"])

    assert result.returncode == 0
    assert "validate" in result.stdout


def test_cli_api_smoke_without_live_fails(tmp_path):
    result = run_cli(["api-smoke", "--site", "stackoverflow", "--out", str(tmp_path / "api.json")])

    assert result.returncode == 2
    assert "--live" in result.stdout
    assert not (tmp_path / "api.json").exists()


def test_cli_validate_and_derive_fixture_outputs(tmp_path):
    validation_out = tmp_path / "validation.json"
    validate_result = run_cli(
        [
            "validate",
            "--questions",
            "tests/fixtures/questions.tsv",
            "--answers",
            "tests/fixtures/answers.tsv",
            "--comments",
            "tests/fixtures/comments.tsv",
            "--provenance",
            "tests/fixtures/provenance.json",
            "--out",
            str(validation_out),
        ]
    )

    assert validate_result.returncode == 0
    assert json.loads(validation_out.read_text(encoding="utf-8"))["ok"] is True

    derive_out = tmp_path / "derived"
    derive_result = run_cli(
        [
            "derive",
            "--questions",
            "tests/fixtures/questions.tsv",
            "--answers",
            "tests/fixtures/answers.tsv",
            "--comments",
            "tests/fixtures/comments.tsv",
            "--provenance",
            "tests/fixtures/provenance.json",
            "--out-dir",
            str(derive_out),
        ]
    )

    assert derive_result.returncode == 0
    assert (derive_out / "derived_thread_indicators.tsv").exists()
    assert (derive_out / "threads.jsonl").exists()
    assert (derive_out / "validation_report.json").exists()


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
