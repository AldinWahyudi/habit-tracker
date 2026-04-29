from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class HabitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    color: str = Field(default="#22c55e", pattern=r"^#[0-9a-fA-F]{6}$")


class HabitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str
    created_at: datetime


class CompletionToggle(BaseModel):
    completed: bool


class HeatmapCell(BaseModel):
    date: date
    completed: bool
    intensity: int  # 0..4 GitHub-style level


class HeatmapResponse(BaseModel):
    habit_id: int
    habit_name: str
    color: str
    start_date: date
    end_date: date
    cells: list[HeatmapCell]
    completion_rate: float


class DayOfWeekPoint(BaseModel):
    weekday: int  # 0 = Monday
    name: str
    rate: float  # 0..1


class CorrelationPair(BaseModel):
    habit_a_id: int
    habit_a_name: str
    habit_b_id: int
    habit_b_name: str
    correlation: float
    days_compared: int
    explanation: str


class WeeklyInsight(BaseModel):
    bullets: list[str]
    source: str  # "claude" | "heuristic"
    week_start: date
    week_end: date
