"""Populate the local SQLite DB with sample habits + 120 days of completions.

Run with: `uv run python -m app.seed` from the `backend/` directory.

Designed to be idempotent: deletes existing rows before inserting.
"""

from __future__ import annotations

import random
from datetime import date, timedelta

from .database import Base, SessionLocal, engine
from .models import Completion, Habit

SEED_HABITS = [
    ("Exercise", "#22c55e", 0.55),
    ("Read", "#3b82f6", 0.70),
    ("Meditate", "#a855f7", 0.45),
    ("No sugar", "#ef4444", 0.40),
    ("8h sleep", "#0ea5e9", 0.65),
]

DAYS = 120


def main() -> None:
    Base.metadata.create_all(bind=engine)
    rng = random.Random(42)

    with SessionLocal() as db:
        db.query(Completion).delete()
        db.query(Habit).delete()
        db.commit()

        habits: list[Habit] = []
        for name, color, _ in SEED_HABITS:
            habit = Habit(name=name, color=color)
            db.add(habit)
            habits.append(habit)
        db.commit()
        for h in habits:
            db.refresh(h)

        today = date.today()
        for habit, (_, _, base_rate) in zip(habits, SEED_HABITS, strict=True):
            for i in range(DAYS):
                day = today - timedelta(days=DAYS - 1 - i)
                # Add a weekday/weekend modulation so the day-of-week chart isn't flat.
                weekend_boost = 0.10 if day.weekday() >= 5 else 0.0
                # And a streaky pattern so the heatmap shows visible runs.
                streak_boost = 0.15 if (i // 5) % 2 == 0 else -0.05
                p = max(0.05, min(0.95, base_rate + weekend_boost + streak_boost))
                if rng.random() < p:
                    db.add(Completion(habit_id=habit.id, date=day, completed=True))
        db.commit()
        print(f"Seeded {len(habits)} habits and ~{DAYS} days of completions.")


if __name__ == "__main__":
    main()
