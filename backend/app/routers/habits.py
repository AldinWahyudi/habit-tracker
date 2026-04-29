from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Completion, Habit
from ..schemas import CompletionToggle, HabitCreate, HabitOut

router = APIRouter(prefix="/api/habits", tags=["habits"])


@router.get("", response_model=list[HabitOut])
def list_habits(db: Session = Depends(get_db)) -> list[Habit]:
    return db.query(Habit).order_by(Habit.created_at.asc()).all()


@router.post("", response_model=HabitOut, status_code=status.HTTP_201_CREATED)
def create_habit(payload: HabitCreate, db: Session = Depends(get_db)) -> Habit:
    habit = Habit(name=payload.name.strip(), color=payload.color)
    db.add(habit)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Habit name already exists") from exc
    db.refresh(habit)
    return habit


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit(habit_id: int, db: Session = Depends(get_db)) -> None:
    habit = db.get(Habit, habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    db.delete(habit)
    db.commit()


@router.put("/{habit_id}/completions/{day}", response_model=CompletionToggle)
def toggle_completion(
    habit_id: int,
    day: date,
    payload: CompletionToggle,
    db: Session = Depends(get_db),
) -> CompletionToggle:
    habit = db.get(Habit, habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")

    existing = (
        db.query(Completion)
        .filter(Completion.habit_id == habit_id, Completion.date == day)
        .one_or_none()
    )
    if payload.completed:
        if existing is None:
            db.add(Completion(habit_id=habit_id, date=day, completed=True))
        else:
            existing.completed = True
    else:
        if existing is not None:
            db.delete(existing)
    db.commit()
    return payload
