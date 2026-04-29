import asyncio
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import analytics
from ..database import get_db
from ..models import Completion, Habit
from ..schemas import (
    CorrelationPair,
    DayOfWeekPoint,
    HeatmapCell,
    HeatmapResponse,
    WeeklyInsight,
)
from ..services.claude import weekly_insight as build_weekly_insight

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

HEATMAP_DAYS = 365
CORRELATION_DAYS = 90
WEEKDAY_NAMES = analytics.WEEKDAY_NAMES


def _completion_set(db: Session, habit_id: int, start: date, end: date) -> set[date]:
    rows = (
        db.query(Completion.date)
        .filter(
            Completion.habit_id == habit_id,
            Completion.completed.is_(True),
            Completion.date >= start,
            Completion.date <= end,
        )
        .all()
    )
    return {r[0] for r in rows}


def _series(completed: set[date], dates: list[date]) -> list[bool]:
    return [d in completed for d in dates]


@router.get("/heatmap/{habit_id}", response_model=HeatmapResponse)
def heatmap(habit_id: int, db: Session = Depends(get_db), today: date | None = None) -> HeatmapResponse:
    habit = db.get(Habit, habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")

    end = today or date.today()
    start = end - timedelta(days=HEATMAP_DAYS - 1)
    dates = analytics.date_range(start, end)

    completed = _completion_set(db, habit_id, start, end)
    series = _series(completed, dates)
    intensities = analytics.heatmap_intensity(series)

    cells = [
        HeatmapCell(date=d, completed=done, intensity=lvl)
        for d, done, lvl in zip(dates, series, intensities, strict=True)
    ]
    rate = sum(1 for v in series if v) / len(series) if series else 0.0
    return HeatmapResponse(
        habit_id=habit.id,
        habit_name=habit.name,
        color=habit.color,
        start_date=start,
        end_date=end,
        cells=cells,
        completion_rate=rate,
    )


@router.get("/day-of-week", response_model=list[DayOfWeekPoint])
def day_of_week(db: Session = Depends(get_db), today: date | None = None) -> list[DayOfWeekPoint]:
    end = today or date.today()
    start = end - timedelta(days=HEATMAP_DAYS - 1)
    dates = analytics.date_range(start, end)
    habits = db.query(Habit).all()

    series_by_habit: dict[int, list[bool]] = {}
    for h in habits:
        completed = _completion_set(db, h.id, start, end)
        series_by_habit[h.id] = _series(completed, dates)

    if not series_by_habit:
        return [
            DayOfWeekPoint(weekday=wd, name=WEEKDAY_NAMES[wd], rate=0.0) for wd in range(7)
        ]

    rates = analytics.aligned_day_of_week_rates(start, series_by_habit)
    return [DayOfWeekPoint(weekday=wd, name=name, rate=rate) for wd, name, rate in rates]


@router.get("/correlations", response_model=list[CorrelationPair])
def correlations(
    db: Session = Depends(get_db), today: date | None = None
) -> list[CorrelationPair]:
    end = today or date.today()
    start = end - timedelta(days=CORRELATION_DAYS - 1)
    dates = analytics.date_range(start, end)

    habits = db.query(Habit).order_by(Habit.id.asc()).all()
    if len(habits) < 2:
        return []

    series_by_habit: dict[int, list[bool]] = {}
    name_by_id: dict[int, str] = {}
    for h in habits:
        completed = _completion_set(db, h.id, start, end)
        series_by_habit[h.id] = _series(completed, dates)
        name_by_id[h.id] = h.name

    pairs = analytics.top_correlated_pairs(
        [(h.id, h.name) for h in habits], series_by_habit, top_k=3
    )

    return [
        CorrelationPair(
            habit_a_id=a_id,
            habit_a_name=name_by_id[a_id],
            habit_b_id=b_id,
            habit_b_name=name_by_id[b_id],
            correlation=round(r, 4),
            days_compared=n,
            explanation=analytics.correlation_explanation(name_by_id[a_id], name_by_id[b_id], r),
        )
        for a_id, b_id, r, n in pairs
    ]


def _habit_week_stats(db: Session, habits: list[Habit], today: date) -> list[dict]:
    week_end = today
    week_start = week_end - timedelta(days=6)
    prev_end = week_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=6)

    stats: list[dict] = []
    for h in habits:
        this_set = _completion_set(db, h.id, week_start, week_end)
        prev_set = _completion_set(db, h.id, prev_start, prev_end)
        this_count = len(this_set)
        prev_count = len(prev_set)

        per_day: list[tuple[str, bool]] = [
            (analytics.WEEKDAY_NAMES[(week_start + timedelta(days=i)).weekday()],
             (week_start + timedelta(days=i)) in this_set)
            for i in range(7)
        ]
        completed_days = [name for name, done in per_day if done]
        missed_days = [name for name, done in per_day if not done]

        stats.append({
            "name": h.name,
            "this_week": this_count,
            "prev_week": prev_count,
            "this_week_rate": this_count / 7.0,
            "best_day": completed_days[0] if completed_days else None,
            "worst_day": missed_days[0] if missed_days else None,
        })
    return stats


def _collect_weekly_stats(db: Session, today: date) -> tuple[date, date, list[dict]]:
    end = today
    start = end - timedelta(days=6)
    habits = db.query(Habit).all()
    return start, end, _habit_week_stats(db, habits, end)


@router.get("/weekly-insight", response_model=WeeklyInsight)
async def weekly_insight(
    db: Session = Depends(get_db), today: date | None = None
) -> WeeklyInsight:
    # Offload sync SQLAlchemy work to a thread so the event loop stays free
    # for the awaited Claude HTTP call below.
    today_value = today or date.today()
    start, end, stats = await asyncio.to_thread(_collect_weekly_stats, db, today_value)
    bullets, source = await build_weekly_insight(start, end, stats)
    return WeeklyInsight(bullets=bullets, source=source, week_start=start, week_end=end)
