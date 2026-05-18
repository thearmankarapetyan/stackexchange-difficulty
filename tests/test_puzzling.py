from __future__ import annotations

import json
import os
import subprocess
import sys
from html import escape
from pathlib import Path

import pytest

from stackexchange_difficulty.puzzling import (
    PUZZLING_RIDDLE_CLEAN_PROFILE,
    PuzzlingError,
    PuzzlingPilotConfig,
    PuzzlingPreflightConfig,
    preflight_puzzling_dump,
    run_puzzling_pilot,
)
from stackexchange_difficulty.validation import read_table


def test_preflight_puzzling_dump_accepts_required_xml(tmp_path):
    root, dump_dir = make_puzzling_project(tmp_path)

    result = preflight_puzzling_dump(
        PuzzlingPreflightConfig(project_root=root, dump_dir=dump_dir, dump_date="2026-04-21")
    )

    assert result.ok is True
    assert result.site_slug == "puzzling"
    assert result.files["Posts.xml"]["present"] is True
    assert result.files["PostLinks.xml"]["present"] is True
    assert "Posts.xml" in result.raw_file_hashes


def test_run_puzzling_pilot_rejects_missing_required_xml(tmp_path):
    root, dump_dir = make_puzzling_project(tmp_path)
    (dump_dir / "Posts.xml").unlink()

    result = run_puzzling_pilot(
        PuzzlingPilotConfig(
            project_root=root,
            dump_dir=dump_dir,
            dump_date="2026-04-21",
            pilot_slug="puzzling-riddle-clean",
            sample_size=2,
        )
    )

    assert result.ok is False
    assert result.decision == "puzzling_preflight_failed"
    assert any(issue["code"] == "missing_required_dump_file" for issue in result.issues)


def test_run_puzzling_pilot_requires_postlinks_for_duplicate_filtering(tmp_path):
    root, dump_dir = make_puzzling_project(tmp_path)
    (dump_dir / "PostLinks.xml").unlink()

    result = run_puzzling_pilot(
        PuzzlingPilotConfig(
            project_root=root,
            dump_dir=dump_dir,
            dump_date="2026-04-21",
            pilot_slug="puzzling-riddle-clean",
            sample_size=2,
        )
    )

    assert result.ok is False
    assert result.decision == "puzzling_duplicate_filter_incomplete"


def test_puzzling_riddle_clean_filters_and_writes_safe_outputs(tmp_path):
    root, dump_dir = make_puzzling_project(tmp_path)

    result = run_puzzling_pilot(
        PuzzlingPilotConfig(
            project_root=root,
            dump_dir=dump_dir,
            dump_date="2026-04-21",
            pilot_slug="puzzling-riddle-clean",
            sample_profile=PUZZLING_RIDDLE_CLEAN_PROFILE,
            sample_size=3,
        )
    )

    assert result.ok is True
    assert result.decision == "puzzling_parser_validated"
    assert result.selected_questions == 3
    assert result.processed_dir is not None
    assert result.derived_dir is not None

    questions = read_table(result.processed_dir / "questions.tsv", name="questions")
    assert {row["question_id"] for row in questions.rows} == {"101", "108", "109"}
    answers = read_table(result.processed_dir / "answers.tsv", name="answers")
    assert len(answers.rows) == 3
    comments = read_table(result.processed_dir / "comments.tsv", name="comments")
    assert {row["post_id"] for row in comments.rows} <= {"101", "108", "109", "201", "208", "209"}
    assert (result.derived_dir / "threads.jsonl").is_file()
    assert (result.processed_dir / "processed-output.sha256").is_file()

    audit = result.audit.read_text(encoding="utf-8")
    assert "Decision: puzzling_parser_validated" in audit
    assert "Sample profile: `puzzling_riddle_clean`" in audit
    assert "Target-tag candidates: deduction=1, lateral-thinking=1, riddle=1" in audit
    assert "Excluded-tag exclusions: cipher=1, image=1, mathematics=1" in audit
    assert "Closed question exclusions: 1" in audit
    assert "Duplicate-link exclusions: 1" in audit
    assert "No accepted-answer exclusions: 1" in audit
    assert "Accepted-answer parent mismatch exclusions: 1" in audit
    assert "Synthetic puzzle title" not in audit
    assert "Synthetic accepted solution" not in audit

    provenance = json.loads(result.provenance.read_text(encoding="utf-8"))
    assert provenance["source_site_slug"] == "puzzling"
    assert provenance["source_url"] == "https://puzzling.stackexchange.com/"
    assert provenance["sample_profile"] == PUZZLING_RIDDLE_CLEAN_PROFILE
    assert "filtered answerable riddle/language puzzle candidates" in provenance[
        "transformation_steps"
    ]


def test_puzzling_riddle_clean_fails_when_sample_size_unavailable(tmp_path):
    root, dump_dir = make_puzzling_project(tmp_path)

    result = run_puzzling_pilot(
        PuzzlingPilotConfig(
            project_root=root,
            dump_dir=dump_dir,
            dump_date="2026-04-21",
            pilot_slug="puzzling-riddle-clean",
            sample_size=4,
        )
    )

    assert result.ok is False
    assert result.decision == "puzzling_sampling_failed"
    assert result.selected_questions == 0


def test_run_puzzling_pilot_rejects_existing_outputs(tmp_path):
    root, dump_dir = make_puzzling_project(tmp_path)
    existing = root / "data/processed/stackexchange-difficulty/puzzling-riddle-clean-2026-04-21"
    existing.mkdir(parents=True)

    with pytest.raises(PuzzlingError, match="already exists"):
        run_puzzling_pilot(
            PuzzlingPilotConfig(
                project_root=root,
                dump_dir=dump_dir,
                dump_date="2026-04-21",
                pilot_slug="puzzling-riddle-clean",
                sample_size=2,
            )
        )


def test_puzzling_cli_prints_aggregate_json_without_post_text(tmp_path):
    root, dump_dir = make_puzzling_project(tmp_path)

    preflight = run_cli(
        [
            "preflight-puzzling-dump",
            "--dump-dir",
            str(dump_dir),
            "--dump-date",
            "2026-04-21",
            "--project-root",
            str(root),
        ]
    )
    assert preflight.returncode == 0
    assert json.loads(preflight.stdout)["ok"] is True
    assert "Synthetic puzzle title" not in preflight.stdout

    pilot = run_cli(
        [
            "run-puzzling-pilot",
            "--dump-dir",
            str(dump_dir),
            "--dump-date",
            "2026-04-21",
            "--pilot-slug",
            "puzzling-riddle-clean",
            "--sample-profile",
            PUZZLING_RIDDLE_CLEAN_PROFILE,
            "--sample-size",
            "2",
            "--project-root",
            str(root),
        ]
    )
    assert pilot.returncode == 0
    payload = json.loads(pilot.stdout)
    assert payload["decision"] == "puzzling_parser_validated"
    assert "Synthetic puzzle title" not in pilot.stdout
    assert "Synthetic accepted solution" not in pilot.stdout


def test_puzzling_cli_help_commands_work():
    for command in (
        "preflight-puzzling-dump",
        "run-puzzling-pilot",
        "prepare-puzzling-qualitative-sample",
        "summarize-puzzling-qualitative-coding",
    ):
        result = run_cli([command, "--help"])
        assert result.returncode == 0
        assert command in result.stdout


def test_puzzling_paths_are_ignored_by_git():
    paths = [
        "data/raw/stackexchange-difficulty/data-dump/puzzling-2026-04-21/Posts.xml",
        "data/raw/stackexchange-difficulty/data-dump/puzzling-2026-04-21/PostLinks.xml",
        "data/processed/stackexchange-difficulty/puzzling-riddle-clean-2026-04-21/questions.tsv",
        "data/processed/stackexchange-difficulty/puzzling-riddle-clean-2026-04-21/comments.tsv",
        "data/processed/stackexchange-difficulty/puzzling-riddle-clean-2026-04-21-derived/threads.jsonl",
        "data/processed/stackexchange-difficulty/puzzling-riddle-recent-2026-04-21-qualitative/qualitative_review.tsv",
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


def make_puzzling_project(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "project"
    dump_dir = root / "data/raw/stackexchange-difficulty/data-dump/puzzling-2026-04-21"
    report_dir = root / "reports/datasets/stackexchange-difficulty"
    (report_dir / "audits").mkdir(parents=True)
    (root / "data/processed/stackexchange-difficulty").mkdir(parents=True)
    dump_dir.mkdir(parents=True)
    write_puzzling_fixture(dump_dir)
    (report_dir / "provenance_data_dump_template.json").write_text(
        json.dumps(
            {
                "dataset_name": "stackexchange-difficulty",
                "source_method": "stack_exchange_data_dump",
                "access_date": "2026-04-21",
                "license": "CC BY-SA",
                "transformation_steps": [],
                "output_hash": "sha256:pending-before-processing",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return root, dump_dir


def write_puzzling_fixture(dump_dir: Path) -> None:
    questions = [
        question(101, 201, "<riddle><wordplay>", "2025-06-01T00:00:00", title="one"),
        question(102, 202, "<image><riddle>", "2025-06-02T00:00:00", title="image"),
        question(103, 203, "<mathematics><logic-puzzle>", "2025-06-03T00:00:00", title="math"),
        question(104, 204, "<cipher><riddle>", "2025-06-04T00:00:00", title="cipher"),
        question(105, 205, "<riddle>", "2025-06-05T00:00:00", closed=True, title="closed"),
        question(106, "", "<riddle>", "2025-06-06T00:00:00", title="no accepted"),
        question(107, 207, "<riddle>", "2025-06-07T00:00:00", title="duplicate"),
        question(108, 208, "<lateral-thinking>", "2025-06-08T00:00:00", title="lateral"),
        question(109, 209, "<deduction>", "2025-06-09T00:00:00", title="deduction"),
        question(110, 299, "<riddle>", "2025-06-10T00:00:00", title="mismatch"),
    ]
    answers = [
        answer(201, 101, "2025-06-01T02:00:00"),
        answer(202, 102, "2025-06-02T02:00:00"),
        answer(203, 103, "2025-06-03T02:00:00"),
        answer(204, 104, "2025-06-04T02:00:00"),
        answer(205, 105, "2025-06-05T02:00:00"),
        answer(206, 106, "2025-06-06T02:00:00"),
        answer(207, 107, "2025-06-07T02:00:00"),
        answer(208, 108, "2025-06-08T02:00:00"),
        answer(209, 109, "2025-06-09T02:00:00"),
        answer(210, 110, "2025-06-10T01:00:00"),
        answer(299, 999, "2025-06-10T02:00:00"),
    ]
    rows = "\n".join([*questions, *answers])
    (dump_dir / "Posts.xml").write_text(f"<posts>\n{rows}\n</posts>\n", encoding="utf-8")
    (dump_dir / "PostLinks.xml").write_text(
        "<postlinks>\n"
        '  <row Id="1" CreationDate="2025-06-07T03:00:00" PostId="107" '
        'RelatedPostId="101" LinkTypeId="3" />\n'
        "</postlinks>\n",
        encoding="utf-8",
    )
    (dump_dir / "Comments.xml").write_text(
        "<comments>\n"
        '  <row Id="301" PostId="101" Score="0" Text="Synthetic comment for selected" '
        'CreationDate="2025-06-01T01:00:00" ContentLicense="CC BY-SA 4.0" />\n'
        '  <row Id="302" PostId="208" Score="0" Text="Synthetic answer comment" '
        'CreationDate="2025-06-08T01:00:00" ContentLicense="CC BY-SA 4.0" />\n'
        '  <row Id="303" PostId="102" Score="0" Text="Synthetic comment for excluded" '
        'CreationDate="2025-06-02T01:00:00" ContentLicense="CC BY-SA 4.0" />\n'
        "</comments>\n",
        encoding="utf-8",
    )
    (dump_dir / "Tags.xml").write_text(
        "<tags>\n"
        '  <row Id="1" TagName="riddle" Count="10" />\n'
        '  <row Id="2" TagName="lateral-thinking" Count="5" />\n'
        '  <row Id="3" TagName="deduction" Count="3" />\n'
        '  <row Id="4" TagName="cipher" Count="3" />\n'
        "</tags>\n",
        encoding="utf-8",
    )


def question(
    question_id: int,
    accepted: int | str,
    tags: str,
    created: str,
    *,
    title: str,
    closed: bool = False,
) -> str:
    accepted_attr = f' AcceptedAnswerId="{accepted}"' if accepted else ""
    closed_attr = ' ClosedDate="2025-07-01T00:00:00"' if closed else ""
    encoded_tags = escape(tags, quote=True)
    return (
        f'  <row Id="{question_id}" PostTypeId="1"{accepted_attr} '
        f'Title="Synthetic puzzle title {title}" '
        f'Body="&lt;p&gt;Synthetic puzzle body {title}&lt;/p&gt;" Tags="{encoded_tags}" '
        f'CreationDate="{created}" Score="2" ViewCount="1000" AnswerCount="1" '
        f'CommentCount="1"{closed_attr} ContentLicense="CC BY-SA 4.0" />'
    )


def answer(answer_id: int, parent_id: int, created: str) -> str:
    return (
        f'  <row Id="{answer_id}" PostTypeId="2" ParentId="{parent_id}" '
        f'Body="&lt;p&gt;Synthetic accepted solution {answer_id}&lt;/p&gt;" '
        f'CreationDate="{created}" Score="1" ContentLicense="CC BY-SA 4.0" />'
    )


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
