"""Prepares validated Stack Exchange question data for exploratory analysis.

This module contains the reusable, non-visual work required by the generic EDA
notebook: setting validation, TSV loading, type conversion, consistency checks,
period selection, aggregation, Tukey outlier identification, correlation
screening, and optional outlier export.

The notebook remains responsible for the analytical narrative and calls the
functions in this module instead of repeating preparation code in cells.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd
from scipy import stats


REQUIRED_COLUMNS = {
    "site",
    "dump_snapshot_date",
    "question_id",
    "question_url",
    "question_creation_datetime",
    "question_title",
    "question_tags",
    "question_score",
    "question_view_count",
    "question_word_count",
    "code_character_count",
    "link_count",
    "image_count",
    "tag_count",
    "stackexchange_answer_count",
    "has_stackexchange_answer",
    "stackexchange_comment_count",
    "available_answer_count",
    "has_available_answer",
    "first_answer_creation_datetime",
    "time_to_first_answer_hours",
    "median_answer_response_hours",
    "accepted_answer_id",
    "accepted_answer_available",
    "accepted_answer_creation_datetime",
    "time_to_eventually_accepted_answer_post_hours",
    "acceptance_date",
    "days_to_acceptance",
    "closed_datetime",
    "answer_score_spread",
    "available_question_comment_count",
    "comments_before_first_answer",
    "observation_days_at_dump",
}

DATE_COLUMNS = [
    "dump_snapshot_date",
    "question_creation_datetime",
    "first_answer_creation_datetime",
    "accepted_answer_creation_datetime",
    "acceptance_date",
    "closed_datetime",
]

NUMERIC_COLUMNS = [
    "question_score",
    "question_view_count",
    "question_word_count",
    "code_character_count",
    "link_count",
    "image_count",
    "tag_count",
    "stackexchange_answer_count",
    "stackexchange_comment_count",
    "available_answer_count",
    "time_to_first_answer_hours",
    "median_answer_response_hours",
    "time_to_eventually_accepted_answer_post_hours",
    "days_to_acceptance",
    "answer_score_spread",
    "available_question_comment_count",
    "comments_before_first_answer",
    "observation_days_at_dump",
]

BOOLEAN_COLUMNS = [
    "has_stackexchange_answer",
    "has_available_answer",
    "accepted_answer_available",
]

NONNEGATIVE_COLUMNS = [
    "question_view_count",
    "question_word_count",
    "code_character_count",
    "link_count",
    "image_count",
    "tag_count",
    "available_answer_count",
    "time_to_first_answer_hours",
    "median_answer_response_hours",
    "time_to_eventually_accepted_answer_post_hours",
    "days_to_acceptance",
    "answer_score_spread",
    "available_question_comment_count",
    "comments_before_first_answer",
    "observation_days_at_dump",
]

AVAILABILITY_LABELS = {
    "time_to_first_answer_hours": "Hours to first answer",
    "median_answer_response_hours": "Median answer delay",
    "time_to_eventually_accepted_answer_post_hours": "Hours to accepted-answer post",
    "days_to_acceptance": "Days to acceptance action",
    "answer_score_spread": "Answer-score spread",
    "question_view_count": "Question views",
    "question_word_count": "Question prose words",
    "code_character_count": "Code characters",
    "available_question_comment_count": "Question comments",
}

CONTENT_DISTRIBUTIONS = [
    {
        "label": "5a",
        "title": "Question score",
        "x_label": "Net community score",
        "column": "question_score",
        "whole_numbers": True,
        "signed": True,
    },
    {
        "label": "5b",
        "title": "Question views",
        "x_label": "Views at the dump snapshot",
        "column": "question_view_count",
        "whole_numbers": True,
        "coverage": 0.95,
    },
    {
        "label": "5c",
        "title": "Question prose length",
        "x_label": "Number of prose words",
        "column": "question_word_count",
        "whole_numbers": True,
    },
    {
        "label": "5d",
        "title": "Code volume",
        "x_label": "Number of code characters",
        "column": "code_character_count",
        "whole_numbers": True,
        "coverage": 0.95,
    },
    {
        "label": "5e",
        "title": "Links in the question",
        "x_label": "Number of links",
        "column": "link_count",
        "whole_numbers": True,
    },
    {
        "label": "5f",
        "title": "Question comments",
        "x_label": "Number of direct question comments",
        "column": "available_question_comment_count",
        "whole_numbers": True,
    },
]

RESPONSE_DISTRIBUTIONS = [
    {
        "label": "6a",
        "title": "Available answers",
        "x_label": "Number of available answers",
        "column": "available_answer_count",
        "whole_numbers": True,
    },
    {
        "label": "6b",
        "title": "Time to first answer",
        "x_label": "Hours from question to first answer",
        "column": "time_to_first_answer_hours",
        "coverage": 0.90,
    },
    {
        "label": "6c",
        "title": "Typical answer arrival",
        "x_label": "Median answer delay (hours)",
        "column": "median_answer_response_hours",
        "coverage": 0.90,
    },
    {
        "label": "6d",
        "title": "Accepted-answer post delay",
        "x_label": "Hours until the accepted answer was posted",
        "column": "time_to_eventually_accepted_answer_post_hours",
        "coverage": 0.90,
    },
    {
        "label": "6e",
        "title": "Acceptance-action delay",
        "x_label": "Calendar days until acceptance",
        "column": "days_to_acceptance",
        "whole_numbers": True,
        "coverage": 0.90,
    },
    {
        "label": "6f",
        "title": "Comments before first answer",
        "x_label": "Number of earlier question comments",
        "column": "comments_before_first_answer",
        "whole_numbers": True,
    },
    {
        "label": "6g",
        "title": "Answer-score spread",
        "x_label": "Highest minus lowest answer score",
        "column": "answer_score_spread",
        "whole_numbers": True,
        "coverage": 0.95,
    },
]

OUTLIER_LABELS = {
    "question_view_count": "Question views",
    "question_word_count": "Question prose words",
    "code_character_count": "Code characters",
    "available_answer_count": "Available answers",
    "available_question_comment_count": "Question comments",
    "time_to_first_answer_hours": "Hours to first answer",
    "time_to_eventually_accepted_answer_post_hours": "Hours to accepted-answer post",
    "answer_score_spread": "Answer-score spread",
}

CORRELATION_LABELS = {
    "question_word_count": "Prose words",
    "code_character_count": "Code characters",
    "link_count": "Links",
    "image_count": "Images",
    "tag_count": "Tags",
    "question_score": "Question score",
    "question_view_count": "Views",
    "available_answer_count": "Available answers",
    "available_question_comment_count": "Question comments",
    "comments_before_first_answer": "Comments before first answer",
    "time_to_first_answer_hours": "Hours to first answer",
    "median_answer_response_hours": "Median answer delay",
    "time_to_eventually_accepted_answer_post_hours": "Hours to accepted-answer post",
    "days_to_acceptance": "Days to acceptance",
    "answer_score_spread": "Answer-score spread",
    "observation_days_at_dump": "Observation days",
}

STRUCTURAL_CORRELATION_PAIRS = {frozenset(("link_count", "image_count"))}


@dataclass(frozen=True)
class EDAData:
    """Validated question table and provenance for one notebook execution."""

    questions: pd.DataFrame
    source_columns: list[str]
    source_row_count: int
    source_column_count: int
    site: str
    snapshot_date: pd.Timestamp
    analysis_end_date: pd.Timestamp
    requested_period: str
    selected_start: pd.Timestamp
    selected_end: pd.Timestamp


@dataclass(frozen=True)
class DistributionProfile:
    """Values and equal-width bins used by one readable histogram."""

    displayed_values: np.ndarray
    bin_edges: np.ndarray
    available: int
    below: int
    above: int
    lower: float
    upper: float
    minimum: float
    maximum: float
    median: float
    coverage: float


def validate_notebook_settings(
    data_file: str | Path,
    outlier_output_file: str | Path | None,
    *,
    min_tag_questions: int,
    top_tags_to_show: int,
    min_correlation_observations: int,
    min_absolute_rho: float,
    fdr_alpha: float,
    max_correlation_pairs: int,
    max_cases_to_show: int,
) -> tuple[Path, Path | None]:
    """Validates editable non-period settings and returns normalized paths."""

    if not isinstance(data_file, (str, Path)):
        raise TypeError("DATA_FILE must be a file path")
    input_path = Path(data_file)

    output_path: Path | None = None
    if outlier_output_file is not None:
        if not isinstance(outlier_output_file, (str, Path)):
            raise TypeError("OUTLIER_OUTPUT_FILE must be a file path or None")
        output_path = Path(outlier_output_file)
        if output_path.resolve() == input_path.resolve():
            raise ValueError("OUTLIER_OUTPUT_FILE must differ from DATA_FILE")

    integer_settings = {
        "MIN_TAG_QUESTIONS": min_tag_questions,
        "TOP_TAGS_TO_SHOW": top_tags_to_show,
        "MIN_CORRELATION_OBSERVATIONS": min_correlation_observations,
        "MAX_CORRELATION_PAIRS": max_correlation_pairs,
        "MAX_CASES_TO_SHOW": max_cases_to_show,
    }
    for name, value in integer_settings.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} must be a whole number greater than zero")
    if min_correlation_observations < 3:
        raise ValueError("MIN_CORRELATION_OBSERVATIONS must be at least 3")

    real_settings = {
        "MIN_ABSOLUTE_RHO": min_absolute_rho,
        "FDR_ALPHA": fdr_alpha,
    }
    for name, value in real_settings.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be a number")
    if not 0 <= min_absolute_rho <= 1:
        raise ValueError("MIN_ABSOLUTE_RHO must be between 0 and 1")
    if not 0 < fdr_alpha <= 1:
        raise ValueError("FDR_ALPHA must be greater than 0 and at most 1")
    return input_path, output_path


def _period_limits(
    period_mode: str,
    start_date: str | None,
    end_date: str | None,
    start_year: int | None,
    end_year: int | None,
) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """Validates one period mode and returns parsed explicit dates when used."""

    if period_mode not in {"all", "date_range", "year_range"}:
        raise ValueError("PERIOD_MODE must be 'all', 'date_range', or 'year_range'")

    if period_mode == "all":
        if any(
            value is not None for value in [start_date, end_date, start_year, end_year]
        ):
            raise ValueError("All date and year limits must be None in all mode")
        return None, None

    if period_mode == "date_range":
        if not isinstance(start_date, str) or not isinstance(end_date, str):
            raise TypeError(
                "START_DATE and END_DATE must use the YYYY-MM-DD text format"
            )
        parsed_start = pd.to_datetime(start_date, format="%Y-%m-%d", errors="raise")
        parsed_end = pd.to_datetime(end_date, format="%Y-%m-%d", errors="raise")
        if parsed_start > parsed_end:
            raise ValueError("START_DATE must be on or before END_DATE")
        if start_year is not None or end_year is not None:
            raise ValueError("START_YEAR and END_YEAR must be None in date_range mode")
        return parsed_start, parsed_end

    years = [start_year, end_year]
    if any(isinstance(value, bool) or not isinstance(value, int) for value in years):
        raise TypeError("START_YEAR and END_YEAR must be whole calendar years")
    if start_year > end_year:
        raise ValueError("START_YEAR must be less than or equal to END_YEAR")
    if start_date is not None or end_date is not None:
        raise ValueError("START_DATE and END_DATE must be None in year_range mode")
    return None, None


def _convert_columns(data: pd.DataFrame) -> None:
    """Converts documented date, number, and TRUE/FALSE fields in place."""

    for column in DATE_COLUMNS:
        data[column] = pd.to_datetime(data[column], errors="raise")
    for column in NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="raise")
    for column in BOOLEAN_COLUMNS:
        text = data[column].astype("string").str.upper()
        invalid = text.notna() & ~text.isin(["TRUE", "FALSE"])
        if invalid.any():
            raise ValueError(
                f"{column} contains a value outside TRUE, FALSE, and empty"
            )
        if column != "has_stackexchange_answer" and text.isna().any():
            raise ValueError(f"{column} contains an empty value")
        data[column] = text.map({"TRUE": True, "FALSE": False}).astype("boolean")


def _validate_table(data: pd.DataFrame) -> tuple[str, pd.Timestamp]:
    """Validates cross-field, dataset, and chronological invariants."""

    expected_stackexchange = data["stackexchange_answer_count"].gt(0).astype("boolean")
    expected_stackexchange[data["stackexchange_answer_count"].isna()] = pd.NA
    if not data["has_stackexchange_answer"].equals(expected_stackexchange):
        raise ValueError(
            "has_stackexchange_answer disagrees with stackexchange_answer_count"
        )

    expected_available = data["available_answer_count"].gt(0).astype("boolean")
    if not data["has_available_answer"].equals(expected_available):
        raise ValueError("has_available_answer disagrees with available_answer_count")
    if data["question_id"].isna().any() or data["question_id"].duplicated().any():
        raise ValueError("Question identifiers must be present and unique")
    for column in NONNEGATIVE_COLUMNS:
        if (data[column].dropna() < 0).any():
            raise ValueError(f"{column} contains a negative value")

    sites = data["site"].dropna().unique()
    if len(sites) != 1:
        raise ValueError(f"Expected one site, found {len(sites)}")
    snapshots = data["dump_snapshot_date"].dropna().dt.normalize().unique()
    if len(snapshots) != 1:
        raise ValueError(f"Expected one dump snapshot date, found {len(snapshots)}")
    snapshot_date = data["dump_snapshot_date"].max().normalize()

    for column in [
        "first_answer_creation_datetime",
        "accepted_answer_creation_datetime",
        "closed_datetime",
    ]:
        available = data[column].notna()
        if (
            data.loc[available, column]
            < data.loc[available, "question_creation_datetime"]
        ).any():
            raise ValueError(f"{column} contains a date before its question")
        if (data[column].dropna() > snapshot_date).any():
            raise ValueError(f"{column} contains a date after the dump snapshot")

    acceptance_available = data["acceptance_date"].notna()
    question_days = data["question_creation_datetime"].dt.normalize()
    if (
        data.loc[acceptance_available, "acceptance_date"]
        < question_days[acceptance_available]
    ).any():
        raise ValueError("acceptance_date contains a day before its question")
    if (data["acceptance_date"].dropna() > snapshot_date).any():
        raise ValueError("acceptance_date contains a day after the dump snapshot")
    if (
        data["question_creation_datetime"] > snapshot_date + pd.Timedelta(days=1)
    ).any():
        raise ValueError(
            "question_creation_datetime contains a date after the dump snapshot"
        )
    return str(sites[0]), snapshot_date


def load_questions(
    data_file: str | Path,
    *,
    period_mode: str,
    start_date: str | None,
    end_date: str | None,
    start_year: int | None,
    end_year: int | None,
) -> EDAData:
    """Loads, validates, and selects one compatible characteristic TSV."""

    path = Path(data_file)
    parsed_start, parsed_end = _period_limits(
        period_mode, start_date, end_date, start_year, end_year
    )
    if not path.is_file():
        raise FileNotFoundError(f"Characteristic table not found: {path.resolve()}")

    data = pd.read_csv(path, sep="\t", low_memory=False)
    if data.empty:
        raise ValueError("The characteristic table contains no question rows")
    source_columns = data.columns.tolist()
    missing = sorted(REQUIRED_COLUMNS - set(source_columns))
    if missing:
        raise ValueError("Missing required column(s): " + ", ".join(missing))

    source_row_count = len(data)
    _convert_columns(data)
    site, snapshot_date = _validate_table(data)
    question_days = data["question_creation_datetime"].dt.normalize()

    if period_mode == "all":
        selected = pd.Series(True, index=data.index)
        requested_period = "All question rows in the TSV"
        analysis_end = data["question_creation_datetime"].max().normalize()
    elif period_mode == "date_range":
        selected = question_days.between(parsed_start, parsed_end, inclusive="both")
        requested_period = f"{parsed_start:%Y-%m-%d} through {parsed_end:%Y-%m-%d}"
        analysis_end = min(parsed_end, snapshot_date)
    else:
        selected = data["question_creation_datetime"].dt.year.between(
            start_year, end_year
        )
        requested_period = f"calendar years {start_year} through {end_year}"
        analysis_end = min(pd.Timestamp(end_year, 12, 31), snapshot_date)

    data = data.loc[selected].copy().reset_index(drop=True)
    if data.empty:
        raise ValueError(
            f"No question rows match the selected period: {requested_period}"
        )
    data["has_accepted_answer"] = data["accepted_answer_id"].notna()
    data["is_closed"] = data["closed_datetime"].notna()

    return EDAData(
        questions=data,
        source_columns=source_columns,
        source_row_count=source_row_count,
        source_column_count=len(source_columns),
        site=site,
        snapshot_date=snapshot_date,
        analysis_end_date=analysis_end,
        requested_period=requested_period,
        selected_start=data["question_creation_datetime"].min().normalize(),
        selected_end=data["question_creation_datetime"].max().normalize(),
    )


def dataset_summary(run: EDAData) -> pd.DataFrame:
    """Returns the compact provenance table displayed near the notebook start."""

    return pd.DataFrame(
        {
            "Item": [
                "Site",
                "Rows in source TSV",
                "Questions selected",
                "Source columns",
                "Requested period",
                "Selected question dates",
                "Outcome observation end",
                "Dump snapshot",
            ],
            "Value": [
                run.site,
                f"{run.source_row_count:,}",
                f"{len(run.questions):,}",
                f"{run.source_column_count:,}",
                run.requested_period,
                f"{run.selected_start:%Y-%m-%d} to {run.selected_end:%Y-%m-%d}",
                f"{run.analysis_end_date:%Y-%m-%d}",
                f"{run.snapshot_date:%Y-%m-%d}",
            ],
        }
    )


def overall_outcomes(data: pd.DataFrame) -> pd.DataFrame:
    """Returns exact counts and shares for the four main question outcomes."""

    total = len(data)
    counts = {
        "Received an answer": int(data["has_available_answer"].sum()),
        "Received no answer": int((~data["has_available_answer"]).sum()),
        "Has an accepted answer": int(data["has_accepted_answer"].sum()),
        "Closed": int(data["is_closed"].sum()),
    }
    return pd.DataFrame(
        {
            "Outcome": counts.keys(),
            "Questions": counts.values(),
            "Percentage": [100 * value / total for value in counts.values()],
        }
    )


def availability_summary(
    data: pd.DataFrame, labels: Mapping[str, str], *, limit: int = 8
) -> pd.DataFrame:
    """Returns the least-available analysis measurements with explicit counts."""

    rows = []
    for column, label in labels.items():
        available = int(data[column].notna().sum())
        rows.append(
            {
                "Measurement": label,
                "Available values": available,
                "Available (%)": 100 * available / len(data),
            }
        )
    return pd.DataFrame(rows).nsmallest(limit, "Available (%)")


def consistency_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Returns exact source-versus-reconstruction difference counts."""

    checks = {
        "Answer count differs": data["stackexchange_answer_count"].notna()
        & data["stackexchange_answer_count"].ne(data["available_answer_count"]),
        "Question-comment count differs": data["stackexchange_comment_count"].notna()
        & data["stackexchange_comment_count"].ne(
            data["available_question_comment_count"]
        ),
        "Accepted answer row unavailable": data["has_accepted_answer"]
        & ~data["accepted_answer_available"].fillna(False),
        "Acceptance date unavailable": data["has_accepted_answer"]
        & data["acceptance_date"].isna(),
    }
    return pd.DataFrame(
        {
            "Check": checks.keys(),
            "Questions": [int(mask.sum()) for mask in checks.values()],
            "Percentage": [100 * mask.mean() for mask in checks.values()],
        }
    )


def outcomes_by_period(data: pd.DataFrame, frequency: str) -> pd.DataFrame:
    """Aggregates posting-cohort outcomes by complete month or calendar year."""

    if frequency not in {"month", "year"}:
        raise ValueError("frequency must be 'month' or 'year'")
    if frequency == "month":
        period = data["question_creation_datetime"].dt.to_period("M")
        full_index = pd.period_range(period.min(), period.max(), freq="M")
        index_name = "creation_period"
    else:
        period = data["question_creation_datetime"].dt.year
        full_index = pd.Index(range(int(period.min()), int(period.max()) + 1))
        index_name = "creation_period"

    rows = data.assign(creation_period=period)
    result = rows.groupby("creation_period").agg(
        questions=("question_id", "size"),
        answered=("has_available_answer", "sum"),
        accepted=("has_accepted_answer", "sum"),
        closed=("is_closed", "sum"),
    )
    result = result.reindex(full_index, fill_value=0)
    result.index.name = index_name
    result["unanswered"] = result["questions"] - result["answered"]
    return result.astype(int)


def cumulative_outcomes(data: pd.DataFrame, analysis_end: pd.Timestamp) -> pd.DataFrame:
    """Returns monthly stocks and cumulative events on one complete timeline."""

    first_month = data["question_creation_datetime"].min().to_period("M").to_timestamp()
    last_month = analysis_end.to_period("M").to_timestamp()
    months = pd.date_range(first_month, last_month, freq="MS")

    def cumulative_count(column: str) -> pd.Series:
        """Returns cumulative event counts through the inclusive analysis end."""

        event_dates = data[column].dropna()
        event_dates = event_dates[
            event_dates.dt.normalize().le(analysis_end.normalize())
        ]
        event_months = event_dates.dt.to_period("M").dt.to_timestamp()
        return event_months.value_counts().reindex(months, fill_value=0).cumsum()

    result = pd.DataFrame(index=months)
    result.index.name = "month"
    result["posted"] = cumulative_count("question_creation_datetime")
    result["answered"] = cumulative_count("first_answer_creation_datetime")
    result["waiting"] = result["posted"] - result["answered"]
    result["accepted"] = cumulative_count("acceptance_date")
    result["closed"] = cumulative_count("closed_datetime")
    if (result["waiting"] < 0).any():
        raise RuntimeError("Cumulative first-answer counts exceed posted questions")
    return result.astype(int)


def first_response_cohorts(
    data: pd.DataFrame, analysis_end: pd.Timestamp
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns monthly first-response acquisition for each posting cohort."""

    creation_period = data["question_creation_datetime"].dt.to_period("M")
    answer_dates = data["first_answer_creation_datetime"].where(
        data["first_answer_creation_datetime"]
        .dt.normalize()
        .le(analysis_end.normalize())
    )
    answer_period = answer_dates.dt.to_period("M")
    observation_end = analysis_end.to_period("M")
    evolution_rows = []
    summary_rows = []

    for cohort_month in sorted(creation_period.unique()):
        cohort_mask = creation_period.eq(cohort_month)
        cohort_size = int(cohort_mask.sum())
        cohort_answers = answer_period[cohort_mask].dropna()
        timeline = pd.period_range(cohort_month, observation_end, freq="M")
        for observation_month in timeline:
            answered = int(cohort_answers.le(observation_month).sum())
            evolution_rows.append(
                {
                    "cohort_month": cohort_month,
                    "observation_month": observation_month,
                    "answered": answered,
                    "answered_percentage": 100 * answered / cohort_size,
                    "cohort_size": cohort_size,
                }
            )
        answered_by_end = int(cohort_answers.le(observation_end).sum())
        summary_rows.append(
            {
                "Posting month": str(cohort_month),
                "Questions": cohort_size,
                "First answer in posting month": int(
                    cohort_answers.eq(cohort_month).sum()
                ),
                "First answer by observation end": answered_by_end,
                "Answered by observation end (%)": 100 * answered_by_end / cohort_size,
            }
        )
    return pd.DataFrame(evolution_rows), pd.DataFrame(summary_rows)


def distribution_profile(
    series: pd.Series,
    *,
    coverage: float = 0.99,
    signed: bool = False,
    whole_numbers: bool = False,
) -> DistributionProfile | None:
    """Prepares equal-width histogram bins for a disclosed central range."""

    if not 0.5 <= coverage < 1:
        raise ValueError("coverage must be at least 0.5 and below 1")
    values = series.dropna().astype(float).to_numpy()
    if values.size == 0:
        return None

    tail = (1 - coverage) / 2
    lower = (
        float(np.quantile(values, tail)) if signed else max(0.0, float(values.min()))
    )
    upper_quantile = 1 - tail if signed else coverage
    upper = float(np.quantile(values, upper_quantile))
    if whole_numbers:
        lower = float(np.floor(lower))
        upper = float(np.ceil(upper))
    if upper <= lower:
        upper = max(float(values.max()), lower + 1)

    displayed = values[(values >= lower) & (values <= upper)]
    below = int((values < lower).sum())
    above = int((values > upper).sum())
    if displayed.size + below + above != values.size:
        raise RuntimeError("Distribution accounting failed")

    if whole_numbers and upper - lower <= 30:
        edges = np.arange(int(lower) - 0.5, int(upper) + 1.5, 1.0)
    elif np.unique(displayed).size < 2:
        center = float(displayed[0])
        edges = np.array([center - 0.5, center + 0.5])
    else:
        raw_edges = np.histogram_bin_edges(displayed, bins="fd")
        bin_count = min(30, max(8, len(raw_edges) - 1))
        edges = np.linspace(lower, upper, bin_count + 1)

    return DistributionProfile(
        displayed_values=displayed,
        bin_edges=edges,
        available=int(values.size),
        below=below,
        above=above,
        lower=lower,
        upper=upper,
        minimum=float(values.min()),
        maximum=float(values.max()),
        median=float(np.median(values)),
        coverage=coverage,
    )


def distribution_summary_table(
    results: Sequence[tuple[Mapping[str, object], DistributionProfile | None]],
) -> pd.DataFrame:
    """Returns exact range and tail accounting for a set of histograms."""

    rows = []
    for specification, profile in results:
        row = {
            "Figure": str(specification["label"]),
            "Measurement": str(specification["title"]),
        }
        if profile is None:
            row.update(
                {
                    "Available values": 0,
                    "Displayed values": 0,
                    "Displayed (%)": np.nan,
                    "Median": np.nan,
                    "Shown range": "Unavailable",
                    "Below shown range": 0,
                    "Above shown range": 0,
                    "Observed minimum": np.nan,
                    "Observed maximum": np.nan,
                }
            )
        else:
            row.update(
                {
                    "Available values": profile.available,
                    "Displayed values": len(profile.displayed_values),
                    "Displayed (%)": 100
                    * len(profile.displayed_values)
                    / profile.available,
                    "Median": profile.median,
                    "Shown range": f"{profile.lower:,.1f} to {profile.upper:,.1f}",
                    "Below shown range": profile.below,
                    "Above shown range": profile.above,
                    "Observed minimum": profile.minimum,
                    "Observed maximum": profile.maximum,
                }
            )
        rows.append(row)
    return pd.DataFrame(rows)


def tukey_high_outliers(
    data: pd.DataFrame, labels: Mapping[str, str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns Tukey high-outlier thresholds and one Boolean flag per field."""

    flags = pd.DataFrame(False, index=data.index, columns=labels)
    rows = []
    for column, label in labels.items():
        values = data[column].dropna()
        if values.empty:
            q1 = q3 = threshold = np.nan
            count = 0
        else:
            q1, q3 = values.quantile([0.25, 0.75])
            threshold = q3 + 1.5 * (q3 - q1)
            flags[column] = data[column].gt(threshold).fillna(False)
            count = int(flags[column].sum())
        available = len(values)
        rows.append(
            {
                "Measurement": label,
                "Available values": available,
                "Q1 (25th percentile)": q1,
                "Q3 (75th percentile)": q3,
                "High-outlier threshold": threshold,
                "High outliers": count,
                "Share of available values (%)": 100 * count / available
                if available
                else np.nan,
            }
        )
    return pd.DataFrame(rows), flags


def build_outlier_dataset(
    data: pd.DataFrame,
    source_columns: Sequence[str],
    flags: pd.DataFrame,
    labels: Mapping[str, str],
    output_path: Path | None,
) -> tuple[pd.DataFrame, str]:
    """Builds the separate question-level outlier table and optionally writes it."""

    flag_count = flags.sum(axis=1)
    reasons = flags.apply(
        lambda row: "; ".join(labels[column] for column, value in row.items() if value),
        axis=1,
    )
    derived = data.copy()
    derived["high_outlier_field_count"] = flag_count
    derived["high_outlier_measurements"] = reasons
    outliers = derived.loc[
        flag_count.gt(0),
        list(source_columns)
        + ["high_outlier_field_count", "high_outlier_measurements"],
    ].copy()

    if output_path is None:
        return outliers, "In-memory dataset: outlier_questions"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    outliers.to_csv(output_path, sep="\t", index=False)
    return outliers, f"Written TSV: {output_path}"


def outlier_group_outcomes(data: pd.DataFrame, flags: pd.DataFrame) -> pd.DataFrame:
    """Compares outcomes between mutually exclusive flagged and unflagged groups."""

    flagged = flags.any(axis=1)
    outcome_masks = {
        "Received an answer": data["has_available_answer"],
        "Has an accepted answer": data["has_accepted_answer"],
        "Closed": data["is_closed"],
    }
    rows = []
    for group_label, group_mask in {
        "No high-outlier flag": ~flagged,
        "At least one high-outlier flag": flagged,
    }.items():
        group_size = int(group_mask.sum())
        for outcome, outcome_mask in outcome_masks.items():
            count = int((group_mask & outcome_mask).sum())
            rows.append(
                {
                    "Group": group_label,
                    "Group size": group_size,
                    "Outcome": outcome,
                    "Questions": count,
                    "Percentage": 100 * count / group_size if group_size else np.nan,
                }
            )
    return pd.DataFrame(rows)


def _tag_rows(data: pd.DataFrame) -> pd.DataFrame:
    """Returns one unique question-tag row for every available tag."""

    rows = (
        data[["question_id", "question_tags"]].dropna(subset=["question_tags"]).copy()
    )
    rows["tag"] = rows["question_tags"].str.split(";")
    rows = rows.explode("tag")
    rows["tag"] = rows["tag"].str.strip()
    return rows[rows["tag"].ne("")].drop_duplicates(["question_id", "tag"])


def outlier_tag_prevalence(
    data: pd.DataFrame, flags: pd.DataFrame, *, limit: int
) -> pd.DataFrame:
    """Compares frequent-tag prevalence in flagged and unflagged questions."""

    flagged = flags.any(axis=1)
    group_lookup = pd.DataFrame(
        {
            "question_id": data["question_id"],
            "Group": np.where(
                flagged, "At least one high-outlier flag", "No high-outlier flag"
            ),
        }
    )
    rows = _tag_rows(data).merge(group_lookup, on="question_id", how="inner")
    sizes = group_lookup.groupby("Group")["question_id"].nunique()
    counts = (
        rows.groupby(["tag", "Group"])["question_id"].nunique().unstack(fill_value=0)
    )
    for group in ["At least one high-outlier flag", "No high-outlier flag"]:
        if group not in counts:
            counts[group] = 0
    counts = counts.rename(
        columns={
            "At least one high-outlier flag": "Flagged questions",
            "No high-outlier flag": "Unflagged questions",
        }
    )
    flagged_size = int(sizes.get("At least one high-outlier flag", 0))
    unflagged_size = int(sizes.get("No high-outlier flag", 0))
    counts["Flagged prevalence (%)"] = (
        100 * counts["Flagged questions"] / flagged_size if flagged_size else np.nan
    )
    counts["Unflagged prevalence (%)"] = (
        100 * counts["Unflagged questions"] / unflagged_size
        if unflagged_size
        else np.nan
    )
    counts["Difference (percentage points)"] = (
        counts["Flagged prevalence (%)"] - counts["Unflagged prevalence (%)"]
    )
    return counts.nlargest(limit, "Flagged questions").sort_values(
        "Flagged prevalence (%)"
    )


def spearman_relationships(
    data: pd.DataFrame,
    labels: Mapping[str, str],
    *,
    min_observations: int,
    min_absolute_rho: float,
    fdr_alpha: float,
    max_pairs: int,
    excluded_pairs: set[frozenset[str]] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculates unique Spearman pairs and retains supported relationships."""

    excluded_pairs = excluded_pairs or set()
    rows = []
    for first, second in combinations(labels, 2):
        if frozenset((first, second)) in excluded_pairs:
            continue
        pair = data[[first, second]].dropna()
        if len(pair) < min_observations:
            continue
        if pair[first].nunique() < 2 or pair[second].nunique() < 2:
            continue
        rho, p_value = stats.spearmanr(pair[first], pair[second])
        rows.append(
            {
                "first": first,
                "second": second,
                "rho": float(rho),
                "p_value": float(p_value),
                "observations": len(pair),
            }
        )

    all_pairs = pd.DataFrame(rows)
    if all_pairs.empty:
        return all_pairs, all_pairs.copy()
    all_pairs["q_value"] = stats.false_discovery_control(
        all_pairs["p_value"].to_numpy(), method="bh"
    )
    retained = all_pairs[
        all_pairs["rho"].abs().ge(min_absolute_rho) & all_pairs["q_value"].le(fdr_alpha)
    ].copy()
    retained["pair_label"] = [
        f"{labels[first]} ↔ {labels[second]}"
        for first, second in zip(retained["first"], retained["second"])
    ]
    retained = retained.loc[retained["rho"].abs().nlargest(max_pairs).index]
    retained = retained.sort_values("rho")
    return all_pairs, retained


def tag_outcomes(data: pd.DataFrame) -> pd.DataFrame:
    """Returns exact question and outcome counts for every available tag."""

    rows = _tag_rows(data).merge(
        data[
            ["question_id", "has_available_answer", "has_accepted_answer", "is_closed"]
        ],
        on="question_id",
        how="left",
    )
    summary = rows.groupby("tag").agg(
        questions=("question_id", "nunique"),
        answered=("has_available_answer", "sum"),
        accepted=("has_accepted_answer", "sum"),
        closed=("is_closed", "sum"),
    )
    summary["unanswered"] = summary["questions"] - summary["answered"]
    for outcome in ["answered", "accepted", "closed"]:
        summary[f"{outcome}_percentage"] = 100 * summary[outcome] / summary["questions"]
    return summary.sort_values("questions", ascending=False)
