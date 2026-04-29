from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Completion


@pytest.fixture()
def client(tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False}, future=True)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        c.session_factory = TestingSession  # type: ignore[attr-defined]
        yield c
    app.dependency_overrides.clear()


def _seed(client: TestClient, name: str, color: str, completed_days: list[date]) -> int:
    resp = client.post("/api/habits", json={"name": name, "color": color})
    assert resp.status_code == 201, resp.text
    habit_id = resp.json()["id"]

    SessionLocal = client.session_factory  # type: ignore[attr-defined]
    with SessionLocal() as db:
        for d in completed_days:
            db.add(Completion(habit_id=habit_id, date=d, completed=True))
        db.commit()
    return habit_id


def test_create_and_list_habit(client):
    resp = client.post("/api/habits", json={"name": "Read", "color": "#3b82f6"})
    assert resp.status_code == 201
    listed = client.get("/api/habits").json()
    assert len(listed) == 1
    assert listed[0]["name"] == "Read"


def test_duplicate_habit_name_rejected(client):
    client.post("/api/habits", json={"name": "Read"})
    resp = client.post("/api/habits", json={"name": "Read"})
    assert resp.status_code == 409


def test_toggle_completion_creates_and_clears_row(client):
    h = client.post("/api/habits", json={"name": "Run"}).json()
    today = date.today().isoformat()
    on = client.put(f"/api/habits/{h['id']}/completions/{today}", json={"completed": True})
    assert on.status_code == 200
    off = client.put(f"/api/habits/{h['id']}/completions/{today}", json={"completed": False})
    assert off.status_code == 200

    SessionLocal = client.session_factory  # type: ignore[attr-defined]
    with SessionLocal() as db:
        rows = db.query(Completion).filter(Completion.habit_id == h["id"]).all()
        assert rows == []


def test_heatmap_returns_365_days(client):
    today = date.today()
    days = [today - timedelta(days=i) for i in (0, 1, 2, 30)]
    habit_id = _seed(client, "Read", "#3b82f6", days)
    resp = client.get(f"/api/analytics/heatmap/{habit_id}")
    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload["cells"]) == 365
    completed = [c for c in payload["cells"] if c["completed"]]
    assert len(completed) == len(days)
    assert payload["completion_rate"] == pytest.approx(len(days) / 365)


def test_day_of_week(client):
    today = date.today()
    # 28 day window, complete every Monday for one habit
    days = [today - timedelta(days=i) for i in range(28) if (today - timedelta(days=i)).weekday() == 0]
    _seed(client, "Read", "#3b82f6", days)
    resp = client.get("/api/analytics/day-of-week")
    assert resp.status_code == 200
    points = resp.json()
    assert len(points) == 7
    by_name = {p["name"]: p["rate"] for p in points}
    assert by_name["Mon"] > 0
    # Other weekdays in the *full 365-day* window should be zero for this habit.
    assert by_name["Tue"] == 0


def test_correlations_returns_top_pairs(client):
    today = date.today()
    days = [today - timedelta(days=i) for i in range(30)]
    _seed(client, "A", "#22c55e", days)
    _seed(client, "B", "#3b82f6", days)
    _seed(client, "C", "#ef4444", [])
    resp = client.get("/api/analytics/correlations")
    assert resp.status_code == 200
    payload = resp.json()
    # Pairs with constant series (C) are skipped — only the A/B pair remains.
    assert len(payload) == 1
    pair = payload[0]
    assert pair["correlation"] == pytest.approx(1.0)
    assert "positive" in pair["explanation"].lower()


def test_weekly_insight_falls_back_to_heuristic(client):
    today = date.today()
    days = [today - timedelta(days=i) for i in range(7)]
    _seed(client, "Read", "#3b82f6", days)
    resp = client.get("/api/analytics/weekly-insight")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["source"] == "heuristic"
    assert len(payload["bullets"]) == 3
