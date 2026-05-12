from __future__ import annotations

import csv
from pathlib import Path

QUERY_PATH = Path("reports/datasets/stackexchange-difficulty/sede_pilot_query.sql")
EXPECTED_COLUMNS_PATH = Path(
    "reports/datasets/stackexchange-difficulty/sede_expected_columns.tsv"
)


def test_sede_pilot_query_uses_bounded_seed_before_answer_joins():
    query = QUERY_PATH.read_text(encoding="utf-8")

    assert "SELECT TOP 20000" in query
    assert "selected_questions AS" in query
    assert "SELECT TOP 5000" in query
    assert "FROM selected_questions AS sq" in query
    assert query.index("FROM selected_questions AS sq") < query.index("OUTER APPLY")


def test_sede_pilot_query_avoids_full_table_stratum_parameter():
    query = QUERY_PATH.read_text(encoding="utf-8")

    assert "@RowsPerStratum" not in query
    assert "answer_context AS" not in query
    assert "FROM answer_context" not in query


def test_sede_pilot_query_selects_expected_export_columns():
    query = QUERY_PATH.read_text(encoding="utf-8")
    with EXPECTED_COLUMNS_PATH.open(encoding="utf-8", newline="") as handle:
        rows = csv.DictReader(handle, delimiter="\t")
        expected_columns = [row["column"] for row in rows]

    for column in expected_columns:
        assert column in query
