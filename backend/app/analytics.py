"""Pure analytics helpers — heatmap intensity, day-of-week, Pearson correlation.

Kept free of FastAPI/SQLAlchemy imports so they're easy to unit test.
"""

from __future__ import annotations

import math
from datetime import date, timedelta

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def date_range(start: date, end: date) -> list[date]:
    """Inclusive list of dates from start to end."""
    days = (end - start).days
    return [start + timedelta(days=i) for i in range(days + 1)]


def heatmap_intensity(series: list[bool]) -> list[int]:
    """GitHub-style 0..4 intensity for a chronological boolean series.

    A day with `completed=False` is always 0. A completed day's level scales with
    the rolling 7-day completion count (the day itself + the previous 6) so streaks
    appear visibly darker than isolated completions.
    """
    intensities: list[int] = []
    for i, done in enumerate(series):
        if not done:
            intensities.append(0)
            continue
        window_start = max(0, i - 6)
        window_count = sum(1 for v in series[window_start : i + 1] if v)
        # window_count is between 1 and 7 because today is True.
        if window_count <= 2:
            level = 1
        elif window_count <= 4:
            level = 2
        elif window_count <= 6:
            level = 3
        else:
            level = 4
        intensities.append(level)
    return intensities


def day_of_week_rates(series_by_habit: dict[int, list[bool]]) -> list[tuple[int, float]]:
    """Average completion rate per weekday across all habits.

    `series_by_habit` maps habit_id to a chronological boolean series where index 0
    corresponds to the same `start_date` for every habit. We assume the caller
    already aligned the series. The first day's weekday is provided externally via
    `aligned_day_of_week_rates`.
    """
    raise NotImplementedError("Use aligned_day_of_week_rates instead.")


def aligned_day_of_week_rates(
    start: date, series_by_habit: dict[int, list[bool]]
) -> list[tuple[int, str, float]]:
    """Average completion rate per weekday (0=Mon..6=Sun) across all habits.

    All series must share the same length and start on `start`.
    """
    totals = [0] * 7
    counts = [0] * 7
    for series in series_by_habit.values():
        for i, done in enumerate(series):
            day = start + timedelta(days=i)
            wd = day.weekday()
            counts[wd] += 1
            if done:
                totals[wd] += 1
    return [
        (wd, WEEKDAY_NAMES[wd], (totals[wd] / counts[wd]) if counts[wd] else 0.0)
        for wd in range(7)
    ]


def pearson(xs: list[float], ys: list[float]) -> float | None:
    """Pearson correlation. Returns None when undefined (constant series or n<2)."""
    n = len(xs)
    if n < 2 or n != len(ys):
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sx = sy = sxy = 0.0
    for x, y in zip(xs, ys, strict=True):
        dx = x - mean_x
        dy = y - mean_y
        sx += dx * dx
        sy += dy * dy
        sxy += dx * dy
    if sx == 0.0 or sy == 0.0:
        return None
    denom = math.sqrt(sx * sy)
    return sxy / denom


def correlation_explanation(name_a: str, name_b: str, r: float) -> str:
    """Plain-language description of a Pearson correlation between two boolean habit series."""
    abs_r = abs(r)
    if abs_r >= 0.7:
        strength = "Very strong"
    elif abs_r >= 0.5:
        strength = "Strong"
    elif abs_r >= 0.3:
        strength = "Moderate"
    elif abs_r >= 0.15:
        strength = "Weak"
    else:
        strength = "Very weak"

    if r >= 0.15:
        return (
            f"{strength} positive link (r={r:+.2f}): on days you complete "
            f"\u201c{name_a}\u201d you tend to also complete \u201c{name_b}\u201d."
        )
    if r <= -0.15:
        return (
            f"{strength} negative link (r={r:+.2f}): "
            f"\u201c{name_a}\u201d and \u201c{name_b}\u201d tend to trade off — "
            "you usually do one or the other, not both."
        )
    return (
        f"{strength} link (r={r:+.2f}): no meaningful relationship between "
        f"\u201c{name_a}\u201d and \u201c{name_b}\u201d."
    )


def top_correlated_pairs(
    habits: list[tuple[int, str]],
    series_by_habit: dict[int, list[bool]],
    top_k: int = 3,
) -> list[tuple[int, int, float, int]]:
    """Return up to `top_k` (habit_a_id, habit_b_id, r, n) ranked by |r| descending.

    Pairs whose correlation is undefined (constant series) are skipped.
    """
    results: list[tuple[int, int, float, int]] = []
    for i in range(len(habits)):
        for j in range(i + 1, len(habits)):
            a_id, _ = habits[i]
            b_id, _ = habits[j]
            xs = [1.0 if v else 0.0 for v in series_by_habit[a_id]]
            ys = [1.0 if v else 0.0 for v in series_by_habit[b_id]]
            r = pearson(xs, ys)
            if r is None:
                continue
            results.append((a_id, b_id, r, len(xs)))
    results.sort(key=lambda t: abs(t[2]), reverse=True)
    return results[:top_k]
