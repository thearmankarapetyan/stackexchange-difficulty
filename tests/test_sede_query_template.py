from __future__ import annotations

import csv
from pathlib import Path

QUERY_PATH = Path("reports/datasets/stackexchange-difficulty/sede_pilot_query.sql")
SITE_GENERIC_QUERY_PATH = Path(
    "reports/datasets/stackexchange-difficulty/sede_pilot_query_site_generic.sql"
)
NON_CODE_QUERY_PATH = Path(
    "reports/datasets/stackexchange-difficulty/sede_pilot_query_non_code_questions.sql"
)
NON_CODING_QUERY_PATH = Path(
    "reports/datasets/stackexchange-difficulty/sede_pilot_query_non_coding_questions.sql"
)
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
    assert_expected_columns_present(query)


def test_site_generic_query_uses_selected_site_and_generic_tag_family():
    query = SITE_GENERIC_QUERY_PATH.read_text(encoding="utf-8")

    assert "Stack Exchange SEDE site-generic" in query
    assert "CHARINDEX('><', q.tags)" in query
    assert "LOWER(SUBSTRING(q.tags" in query
    assert "q.Tags LIKE '%<python>%'" not in query
    assert "SELECT TOP 20000" in query
    assert "SELECT TOP 5000" in query
    assert "FROM selected_questions AS sq" in query
    assert query.index("FROM selected_questions AS sq") < query.index("OUTER APPLY")
    assert_expected_columns_present(query)


def test_non_code_question_query_filters_rendered_code_markup():
    query = NON_CODE_QUERY_PATH.read_text(encoding="utf-8")

    assert "q.Body NOT LIKE '%<code>%'" in query
    assert "SELECT TOP 60000" in query
    assert "SELECT TOP 5000" in query
    assert "FROM selected_questions AS sq" in query
    assert query.index("FROM selected_questions AS sq") < query.index("OUTER APPLY")
    assert_expected_columns_present(query)


def test_non_coding_question_query_filters_code_and_debugging_signals():
    query = NON_CODING_QUERY_PATH.read_text(encoding="utf-8")

    assert "q.Body NOT LIKE '%<code>%'" in query
    assert "q.Tags LIKE '%<algorithm>%'" in query
    assert "q.Tags LIKE '%<design-patterns>%'" in query
    assert "q.Tags NOT LIKE '%<python>%'" in query
    assert "q.Tags NOT LIKE '%<javascript>%'" in query
    assert "q.Title NOT LIKE '%error%'" in query
    assert "q.Body NOT LIKE '%exception%'" in query
    assert "SELECT TOP 200000" in query
    assert "SELECT TOP 5000" in query
    assert "FROM selected_questions AS sq" in query
    assert query.index("FROM selected_questions AS sq") < query.index("OUTER APPLY")
    assert_expected_columns_present(query)


def assert_expected_columns_present(query: str) -> None:
    with EXPECTED_COLUMNS_PATH.open(encoding="utf-8", newline="") as handle:
        rows = csv.DictReader(handle, delimiter="\t")
        expected_columns = [row["column"] for row in rows]

    for column in expected_columns:
        assert column in query
