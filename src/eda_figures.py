"""This module creates accessible figures for the generic Stack Exchange EDA notebook.

The functions in this module apply one visual grammar throughout the notebook:
linear scales, zero baselines for bars and filled areas, complete axis labels,
consistent comparison scales, restrained colour use, direct numeric labels, and
simple chart types matched to the statistical relationship being shown.

Every function returns Matplotlib figures. Notebook cells remain short and keep
the figures beside their plain-language interpretations.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.container import BarContainer
from matplotlib.ticker import MaxNLocator, PercentFormatter

from eda_support import DistributionProfile, distribution_profile


# Restrained, colour-vision-friendly palette based on Okabe–Ito colours.
BLUE = "#0072B2"
LIGHT_BLUE = "#56B4E9"
GREEN = "#009E73"
ORANGE = "#E69F00"
VERMILION = "#D55E00"
PURPLE = "#CC79A7"
GREY = "#767676"
DARK = "#202020"
LIGHT_GREY = "#D9D9D9"


def _style_axis(
    axis: plt.Axes,
    *,
    numeric_axis: str,
    percent: bool = False,
    integer: bool = False,
) -> None:
    """Applies the shared readable style to one completed axis."""

    axis.set_axisbelow(True)
    axis.spines[["top", "right"]].set_visible(False)
    if numeric_axis == "x":
        axis.grid(axis="x", color=LIGHT_GREY, linewidth=0.8)
        if percent:
            axis.xaxis.set_major_formatter(PercentFormatter(100))
        if integer:
            axis.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=7))
    else:
        axis.grid(axis="y", color=LIGHT_GREY, linewidth=0.8)
        if percent:
            axis.yaxis.set_major_formatter(PercentFormatter(100))
        if integer:
            axis.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=7))


def _label_horizontal_bars(
    axis: plt.Axes,
    bars: BarContainer,
    labels: Sequence[str],
    *,
    padding: int = 4,
) -> None:
    """Adds readable values to horizontal bars."""

    axis.bar_label(bars, labels=labels, padding=padding, fontsize=9)


def _show_all_months(axis: plt.Axes, dates: Sequence[pd.Timestamp]) -> None:
    """Labels every month while repeating the year only when it changes."""

    months = pd.DatetimeIndex(dates)
    labels = [
        date.strftime("%b\n%Y")
        if index == 0 or date.month == 1
        else date.strftime("%b")
        for index, date in enumerate(months)
    ]
    axis.set_xticks(months, labels)
    if len(months) == 1:
        center = months[0]
        axis.set_xlim(center - pd.Timedelta(days=20), center + pd.Timedelta(days=20))


def plot_overview(
    outcomes: pd.DataFrame,
    availability: pd.DataFrame,
    consistency: pd.DataFrame,
) -> Figure:
    """Plots outcome shares, field availability, and consistency differences."""

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.6), layout="constrained")

    outcome_colors = [GREEN, ORANGE, BLUE, PURPLE]
    bars = axes[0].barh(
        outcomes["Outcome"], outcomes["Percentage"], color=outcome_colors
    )
    axes[0].invert_yaxis()
    axes[0].set_title(
        "Figure 1a — Snapshot question outcomes", loc="left", fontweight="bold"
    )
    axes[0].set_xlabel("Percentage of selected questions")
    axes[0].set_ylabel("Outcome")
    axes[0].set_xlim(0, 100)
    _label_horizontal_bars(
        axes[0],
        bars,
        [
            f"{row.Percentage:.1f}% (n={row.Questions:,})"
            for row in outcomes.itertuples()
        ],
    )
    _style_axis(axes[0], numeric_axis="x", percent=True)

    available = availability.sort_values("Available (%)")
    bars = axes[1].barh(
        available["Measurement"], available["Available (%)"], color=LIGHT_BLUE
    )
    axes[1].set_title("Figure 1b — Field availability", loc="left", fontweight="bold")
    axes[1].set_xlabel("Percentage with an available value")
    axes[1].set_ylabel("Measurement")
    axes[1].set_xlim(0, 100)
    _label_horizontal_bars(
        axes[1],
        bars,
        [f"{row._2:.1f}% (n={row._1:,})" for row in available.itertuples(index=False)],
    )
    _style_axis(axes[1], numeric_axis="x", percent=True)

    issues = consistency.sort_values("Percentage")
    bars = axes[2].barh(issues["Check"], issues["Percentage"], color=VERMILION)
    axes[2].set_title("Figure 1c — Source differences", loc="left", fontweight="bold")
    axes[2].set_xlabel("Percentage of selected questions")
    axes[2].set_ylabel("Consistency check")
    upper = max(5.0, float(issues["Percentage"].max()) * 1.3)
    axes[2].set_xlim(0, min(100, upper))
    _label_horizontal_bars(
        axes[2],
        bars,
        [f"{row.Percentage:.1f}% (n={row.Questions:,})" for row in issues.itertuples()],
    )
    _style_axis(axes[2], numeric_axis="x", percent=True)
    return fig


def _period_axis(
    axis: plt.Axes, table: pd.DataFrame, frequency: str
) -> np.ndarray | pd.DatetimeIndex:
    """Configures one month or year x-axis and returns plotting positions."""

    if frequency == "month":
        positions = table.index.to_timestamp()
        _show_all_months(axis, positions)
    else:
        positions = np.arange(len(table))
        axis.set_xticks(positions, table.index.astype(str))
    return positions


def plot_period_outcomes(
    table: pd.DataFrame, *, frequency: str, figure_label: str
) -> Figure:
    """Plots flow counts with columns and a common zero-based scale."""

    if frequency not in {"month", "year"}:
        raise ValueError("frequency must be 'month' or 'year'")
    period_text = "posting month" if frequency == "month" else "posting year"
    fig, axes = plt.subplots(2, 2, figsize=(16, 10), layout="constrained")
    y_max = max(1, int(table["questions"].max())) * 1.08

    panels = [
        ("questions", "All questions", GREY),
        ("accepted", "Questions with an accepted answer", BLUE),
        ("closed", "Closed questions", PURPLE),
    ]
    for axis, (column, title, color) in zip(
        [axes[0, 0], axes[1, 0], axes[1, 1]], panels
    ):
        positions = _period_axis(axis, table, frequency)
        width = pd.Timedelta(days=24) if frequency == "month" else 0.72
        bars = axis.bar(
            positions, table[column], width=width, color=color, edgecolor="white"
        )
        axis.set_title(title, loc="left", fontweight="bold")
        axis.set_xlabel(f"Question {period_text}")
        axis.set_ylabel("Number of questions")
        axis.set_ylim(0, y_max)
        _style_axis(axis, numeric_axis="y", integer=True)
        if frequency == "year" and len(table) <= 5:
            axis.bar_label(
                bars, labels=[f"{value:,}" for value in table[column]], padding=3
            )

    axis = axes[0, 1]
    positions = _period_axis(axis, table, frequency)
    width = pd.Timedelta(days=24) if frequency == "month" else 0.72
    answered_bars = axis.bar(
        positions,
        table["answered"],
        width=width,
        color=GREEN,
        edgecolor="white",
        label="Received an answer",
    )
    unanswered_bars = axis.bar(
        positions,
        table["unanswered"],
        bottom=table["answered"],
        width=width,
        color=ORANGE,
        edgecolor=DARK,
        linewidth=0.5,
        hatch="//",
        label="Received no answer",
    )
    axis.set_title("Answered and unanswered questions", loc="left", fontweight="bold")
    axis.set_xlabel(f"Question {period_text}")
    axis.set_ylabel("Number of questions")
    axis.set_ylim(0, y_max)
    _style_axis(axis, numeric_axis="y", integer=True)
    if frequency == "year" and len(table) <= 5:
        axis.bar_label(
            answered_bars,
            labels=[f"{value:,}" for value in table["answered"]],
            label_type="center",
            color="white",
        )
        axis.bar_label(
            unanswered_bars,
            labels=[f"{value:,}" for value in table["unanswered"]],
            label_type="center",
            color=DARK,
        )

    handles, labels = axis.get_legend_handles_labels()
    axes[1, 1].legend(
        handles,
        labels,
        frameon=False,
        loc="upper right",
        title="Answer status",
    )
    fig.suptitle(
        f"Figure {figure_label} — Snapshot outcomes by {period_text}",
        fontsize=15,
        fontweight="bold",
    )
    return fig


def plot_cumulative_outcomes(table: pd.DataFrame) -> Figure:
    """Plots cumulative stocks and events as separate aligned line charts."""

    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True, layout="constrained")
    months = table.index

    axes[0].plot(
        months,
        table["posted"],
        color=GREY,
        linewidth=2.2,
        marker="o",
        markersize=3,
        label="Questions posted",
    )
    axes[0].plot(
        months,
        table["answered"],
        color=GREEN,
        linewidth=2.2,
        marker="o",
        markersize=3,
        label="Received a first answer",
    )
    axes[0].set_title(
        "Figure 3a — Questions posted and answered", loc="left", fontweight="bold"
    )
    axes[0].set_ylabel("Cumulative questions")
    axes[0].set_ylim(bottom=0)
    axes[0].legend(frameon=False, loc="upper left")
    _style_axis(axes[0], numeric_axis="y", integer=True)

    axes[1].plot(
        months, table["waiting"], color=ORANGE, linewidth=2.2, marker="s", markersize=3
    )
    axes[1].set_title(
        "Figure 3b — Questions still waiting for a first answer",
        loc="left",
        fontweight="bold",
    )
    axes[1].set_ylabel("Questions waiting")
    axes[1].set_ylim(bottom=0)
    _style_axis(axes[1], numeric_axis="y", integer=True)

    axes[2].plot(
        months,
        table["accepted"],
        color=BLUE,
        linewidth=2.2,
        marker="o",
        markersize=3,
        label="Acceptance events",
    )
    axes[2].plot(
        months,
        table["closed"],
        color=PURPLE,
        linewidth=2.2,
        marker="s",
        markersize=3,
        label="Closure events",
    )
    axes[2].set_title(
        "Figure 3c — Acceptance and closure events", loc="left", fontweight="bold"
    )
    axes[2].set_xlabel("Calendar month")
    axes[2].set_ylabel("Cumulative events")
    axes[2].set_ylim(bottom=0)
    axes[2].legend(frameon=False, loc="upper left")
    _style_axis(axes[2], numeric_axis="y", integer=True)

    _show_all_months(axes[2], months)
    return fig


def plot_cohort_evolution(evolution: pd.DataFrame) -> list[Figure]:
    """Plots one comparable 0–100% first-response panel per posting cohort."""

    figures = []
    cohort_months = sorted(evolution["cohort_month"].unique())
    for year in sorted({month.year for month in cohort_months}):
        year_months = [month for month in cohort_months if month.year == year]
        columns = min(3, len(year_months))
        rows = int(np.ceil(len(year_months) / columns))
        fig, axes = plt.subplots(
            rows,
            columns,
            figsize=(6 * columns, 3.8 * rows),
            squeeze=False,
            layout="constrained",
        )
        for axis, cohort_month in zip(axes.flat, year_months):
            cohort = evolution[evolution["cohort_month"].eq(cohort_month)]
            dates = cohort["observation_month"].dt.to_timestamp()
            percentages = cohort["answered_percentage"]
            size = int(cohort["cohort_size"].iloc[0])
            axis.step(dates, percentages, where="post", color=BLUE, linewidth=2)
            axis.plot(dates, percentages, "o", color=BLUE, markersize=3)
            axis.set_title(
                f"{cohort_month.strftime('%B %Y')} (n={size:,})",
                loc="left",
                fontsize=10,
                fontweight="bold",
            )
            axis.set_xlabel("Observation month")
            axis.set_ylabel("Cohort answered (%)")
            axis.set_ylim(0, 100)
            _show_all_months(axis, dates)
            axis.annotate(
                f"{percentages.iloc[-1]:.1f}%",
                (dates.iloc[-1], percentages.iloc[-1]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8,
                color=DARK,
            )
            _style_axis(axis, numeric_axis="y", percent=True)
        for axis in axes.flat[len(year_months) :]:
            axis.set_axis_off()
        fig.suptitle(
            f"Figure 4 — First-response acquisition for {year} posting cohorts",
            fontsize=15,
            fontweight="bold",
        )
        figures.append(fig)
    return figures


def _format_number(value: float) -> str:
    """Formats an axis annotation without unnecessary decimal places."""

    if abs(value) >= 1000:
        return f"{value:,.0f}"
    if float(value).is_integer():
        return f"{value:.0f}"
    return f"{value:.1f}"


def plot_distributions(
    data: pd.DataFrame,
    specs: Sequence[Mapping[str, object]],
    *,
    figure_number: str,
) -> tuple[list[Figure], list[tuple[Mapping[str, object], DistributionProfile | None]]]:
    """Plots readable equal-width histograms in pages of at most four panels."""

    results = []
    for spec in specs:
        profile = distribution_profile(
            data[str(spec["column"])],
            coverage=float(spec.get("coverage", 0.99)),
            signed=bool(spec.get("signed", False)),
            whole_numbers=bool(spec.get("whole_numbers", False)),
        )
        results.append((spec, profile))

    figures = []
    for page_start in range(0, len(results), 4):
        page = results[page_start : page_start + 4]
        fig, axes = plt.subplots(
            2, 2, figsize=(12, 8), squeeze=False, layout="constrained"
        )
        for axis, (spec, profile) in zip(axes.flat, page):
            title = f"Figure {spec['label']} — {spec['title']}"
            if profile is None:
                axis.text(0.5, 0.5, "No available values", ha="center", va="center")
                axis.set_title(title, loc="left", fontweight="bold")
                axis.set_axis_off()
                continue
            whole_numbers = bool(spec.get("whole_numbers", False))
            discrete = whole_numbers and np.allclose(np.diff(profile.bin_edges), 1)
            if discrete:
                values = np.arange(int(profile.lower), int(profile.upper) + 1)
                counts = pd.Series(profile.displayed_values).value_counts()
                heights = [int(counts.get(value, 0)) for value in values]
                axis.bar(
                    values,
                    heights,
                    width=0.82,
                    color=LIGHT_BLUE,
                    edgecolor=DARK,
                    linewidth=0.5,
                )
                axis.set_xlim(values[0] - 0.5, values[-1] + 0.5)
                step = max(1, int(np.ceil(len(values) / 7)))
                ticks = list(values[::step])
                if ticks[-1] != values[-1]:
                    ticks.append(values[-1])
                axis.set_xticks(ticks)
            else:
                axis.hist(
                    profile.displayed_values,
                    bins=profile.bin_edges,
                    color=LIGHT_BLUE,
                    edgecolor=DARK,
                    linewidth=0.5,
                )
                axis.set_xlim(profile.lower, profile.upper)
            axis.axvline(profile.median, color=VERMILION, linestyle="--", linewidth=1.8)
            axis.set_title(title, loc="left", fontsize=10, fontweight="bold")
            axis.set_xlabel(str(spec["x_label"]))
            axis.set_ylabel("Number of questions")
            axis.set_ylim(bottom=0)
            if not discrete:
                axis.xaxis.set_major_locator(
                    MaxNLocator(nbins=6, integer=whole_numbers)
                )
            axis.text(
                0.98,
                0.96,
                f"Median: {_format_number(profile.median)}\n"
                f"Displayed: {len(profile.displayed_values):,}/{profile.available:,} "
                f"({100 * len(profile.displayed_values) / profile.available:.1f}%)\n"
                f"Below/above range: {profile.below:,}/{profile.above:,}\n"
                f"Observed min/max: {_format_number(profile.minimum)}/{_format_number(profile.maximum)}",
                transform=axis.transAxes,
                ha="right",
                va="top",
                fontsize=8,
                bbox={"facecolor": "white", "edgecolor": LIGHT_GREY, "alpha": 0.92},
            )
            _style_axis(axis, numeric_axis="y", integer=True)
        for axis in axes.flat[len(page) :]:
            axis.set_axis_off()
        page_number = page_start // 4 + 1
        page_total = int(np.ceil(len(results) / 4))
        fig.suptitle(
            f"Figure {figure_number} — Numeric distributions (page {page_number} of {page_total})",
            fontsize=15,
            fontweight="bold",
        )
        figures.append(fig)
    return figures, results


def plot_outlier_evidence(summary: pd.DataFrame, flags: pd.DataFrame) -> Figure:
    """Plots measurement-specific outlier shares and flags per question."""

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.8), layout="constrained")
    ordered = summary.sort_values("Share of available values (%)")
    axes[0].scatter(
        ordered["Share of available values (%)"],
        ordered["Measurement"],
        color=VERMILION,
        marker="o",
        s=55,
        zorder=3,
    )
    for row in ordered.itertuples(index=False):
        axes[0].text(
            row._6 + 0.25,
            row.Measurement,
            f"{row._6:.1f}% ({row._5:,}/{row._1:,})",
            va="center",
            fontsize=8,
        )
    axes[0].set_title(
        "Figure 7a — Tukey high-outlier share", loc="left", fontweight="bold"
    )
    axes[0].set_xlabel("Percentage of available values")
    axes[0].set_ylabel("Measurement")
    axes[0].set_xlim(
        0, max(5, float(ordered["Share of available values (%)"].max()) * 1.35)
    )
    _style_axis(axes[0], numeric_axis="x", percent=True)

    flag_counts = flags.sum(axis=1).value_counts().sort_index()
    full_index = range(0, int(flags.shape[1]) + 1)
    flag_counts = flag_counts.reindex(full_index, fill_value=0)
    percentages = 100 * flag_counts / len(flags)
    bars = axes[1].bar(flag_counts.index, percentages, color=BLUE, edgecolor="white")
    axes[1].set_title(
        "Figure 7b — Number of flags per question", loc="left", fontweight="bold"
    )
    axes[1].set_xlabel("Tukey high-outlier flags on one question")
    axes[1].set_ylabel("Percentage of selected questions")
    axes[1].set_ylim(0, max(5, float(percentages.max()) * 1.2))
    axes[1].set_xticks(list(full_index))
    axes[1].bar_label(
        bars,
        labels=[
            f"{value:.1f}%\n(n={count:,})"
            for value, count in zip(percentages, flag_counts)
        ],
        padding=3,
        fontsize=8,
    )
    _style_axis(axes[1], numeric_axis="y", percent=True)
    return fig


def _connected_dots(
    axis: plt.Axes,
    table: pd.DataFrame,
    *,
    category: str,
    first_value: str,
    second_value: str,
    first_label: str,
    second_label: str,
    title: str,
) -> None:
    """Draws a two-group percentage comparison with colour and marker redundancy."""

    positions = np.arange(len(table))
    axis.hlines(
        positions,
        table[first_value],
        table[second_value],
        color=LIGHT_GREY,
        linewidth=2,
    )
    axis.scatter(
        table[first_value],
        positions,
        color=GREY,
        marker="s",
        s=55,
        label=first_label,
        zorder=3,
    )
    axis.scatter(
        table[second_value],
        positions,
        color=VERMILION,
        marker="o",
        s=60,
        label=second_label,
        zorder=3,
    )
    axis.set_yticks(positions, table[category])
    axis.set_xlim(0, 100)
    axis.set_title(title, loc="left", fontweight="bold")
    axis.set_xlabel("Percentage of questions in the group")
    axis.set_ylabel(category)
    _style_axis(axis, numeric_axis="x", percent=True)


def plot_outlier_patterns(
    outcome_comparison: pd.DataFrame,
    tag_comparison: pd.DataFrame,
) -> Figure:
    """Compares mutually exclusive outlier groups by outcomes and tag prevalence."""

    fig, axes = plt.subplots(1, 2, figsize=(15, 6), layout="constrained")
    group_sizes = outcome_comparison.groupby("Group")["Group size"].first()
    unflagged_label = f"No flag (n={int(group_sizes['No high-outlier flag']):,})"
    flagged_label = (
        f"At least one flag (n={int(group_sizes['At least one high-outlier flag']):,})"
    )
    outcome_wide = outcome_comparison.pivot(
        index="Outcome", columns="Group", values="Percentage"
    ).reset_index()
    _connected_dots(
        axes[0],
        outcome_wide,
        category="Outcome",
        first_value="No high-outlier flag",
        second_value="At least one high-outlier flag",
        first_label=unflagged_label,
        second_label=flagged_label,
        title="Figure 8a — Outcome percentages",
    )

    if tag_comparison.empty:
        axes[1].text(0.5, 0.5, "No tags are available", ha="center", va="center")
        axes[1].set_axis_off()
    else:
        tags = tag_comparison.reset_index().rename(columns={"tag": "Tag"})
        _connected_dots(
            axes[1],
            tags,
            category="Tag",
            first_value="Unflagged prevalence (%)",
            second_value="Flagged prevalence (%)",
            first_label=unflagged_label,
            second_label=flagged_label,
            title="Figure 8b — Frequent-tag prevalence",
        )
    axes[0].legend(frameon=False, loc="lower right")
    return fig


def plot_correlations(relationships: pd.DataFrame) -> Figure | None:
    """Plots retained Spearman coefficients on a signed common scale."""

    if relationships.empty:
        return None
    height = max(4, 0.48 * len(relationships) + 1.8)
    fig, axis = plt.subplots(figsize=(10, height), layout="constrained")
    positions = np.arange(len(relationships))
    axis.hlines(positions, 0, relationships["rho"], color=LIGHT_GREY, linewidth=2)
    positive = relationships["rho"].ge(0)
    axis.scatter(
        relationships.loc[positive, "rho"],
        positions[positive],
        color=BLUE,
        marker="o",
        s=65,
        label="Positive relationship",
        zorder=3,
    )
    axis.scatter(
        relationships.loc[~positive, "rho"],
        positions[~positive],
        color=ORANGE,
        marker="^",
        s=70,
        label="Negative relationship",
        zorder=3,
    )
    axis.set_yticks(positions, relationships["pair_label"])
    axis.set_xlim(-1, 1)
    axis.axvline(0, color=DARK, linewidth=1.2)
    axis.set_title(
        "Figure 9 — Retained Spearman relationships", loc="left", fontweight="bold"
    )
    axis.set_xlabel("Spearman correlation coefficient (rho)")
    axis.set_ylabel("Characteristic pair")
    for y, row in enumerate(relationships.itertuples()):
        offset = 0.025 if row.rho >= 0 else -0.025
        axis.text(
            row.rho + offset,
            y,
            f"{row.rho:.2f}",
            ha="left" if row.rho >= 0 else "right",
            va="center",
            fontsize=8,
        )
    _style_axis(axis, numeric_axis="x")
    return fig


def plot_tag_counts(top_tags: pd.DataFrame) -> Figure | None:
    """Plots each tag count on separate panels with one shared baseline."""

    if top_tags.empty:
        return None
    ordered = top_tags.sort_values("questions")
    panels = [
        ("questions", "All questions", GREY),
        ("answered", "Received an answer", GREEN),
        ("unanswered", "Received no answer", ORANGE),
        ("accepted", "Has an accepted answer", BLUE),
        ("closed", "Closed", PURPLE),
    ]
    height = max(8, 0.42 * len(ordered) * 2)
    fig, axes = plt.subplots(
        3, 2, figsize=(14, height), sharex=True, layout="constrained"
    )
    maximum = max(1, int(ordered["questions"].max())) * 1.13
    for axis, (column, title, color) in zip(axes.flat, panels):
        bars = axis.barh(ordered.index, ordered[column], color=color)
        axis.set_title(title, loc="left", fontweight="bold")
        axis.set_xlabel("Number of questions carrying the tag")
        axis.set_ylabel("Tag")
        axis.set_xlim(0, maximum)
        axis.bar_label(
            bars,
            labels=[f"{value:,}" for value in ordered[column]],
            padding=3,
            fontsize=8,
        )
        _style_axis(axis, numeric_axis="x", integer=True)
    axes.flat[-1].set_axis_off()
    fig.suptitle(
        "Figure 10a — Exact outcome counts for frequent tags",
        fontsize=15,
        fontweight="bold",
    )
    return fig


def plot_tag_percentages(eligible_tags: pd.DataFrame, minimum: int) -> Figure | None:
    """Plots tag outcome percentages in three separate aligned panels."""

    if eligible_tags.empty:
        return None
    ordered = eligible_tags.sort_values("answered_percentage")
    panels = [
        ("answered_percentage", "Received an answer", GREEN),
        ("accepted_percentage", "Has an accepted answer", BLUE),
        ("closed_percentage", "Closed", PURPLE),
    ]
    height = max(5.5, 0.4 * len(ordered) + 1.8)
    fig, axes = plt.subplots(
        1, 3, figsize=(15, height), sharey=True, layout="constrained"
    )
    labels = [
        f"{tag} (n={int(ordered.loc[tag, 'questions']):,})" for tag in ordered.index
    ]
    positions = np.arange(len(ordered))
    for axis, (column, title, color) in zip(axes, panels):
        axis.scatter(ordered[column], positions, color=color, s=55, zorder=3)
        axis.set_yticks(positions, labels)
        axis.set_xlim(0, 100)
        axis.set_title(title, loc="left", fontweight="bold")
        axis.set_xlabel("Percentage of questions carrying the tag")
        _style_axis(axis, numeric_axis="x", percent=True)
    axes[0].set_ylabel("Tag and number of questions")
    fig.suptitle(
        f"Figure 10b — Outcome percentages for tags with at least {minimum} questions",
        fontsize=15,
        fontweight="bold",
    )
    return fig
