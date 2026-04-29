from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utc_now() -> datetime:
    return datetime.now(UTC)


class Habit(Base):
    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    color: Mapped[str] = mapped_column(String(16), nullable=False, default="#22c55e")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now, nullable=False)

    completions: Mapped[list["Completion"]] = relationship(
        back_populates="habit",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Completion(Base):
    """Boolean per habit per date: a row exists for every day the habit was checked off.

    Absence of a row means the habit was not completed that day.
    """

    __tablename__ = "completions"
    __table_args__ = (UniqueConstraint("habit_id", "date", name="uq_completion_habit_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    habit_id: Mapped[int] = mapped_column(
        ForeignKey("habits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    habit: Mapped[Habit] = relationship(back_populates="completions")
