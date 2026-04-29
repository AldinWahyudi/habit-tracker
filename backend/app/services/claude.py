"""Claude-powered weekly insight, with a deterministic local fallback."""

from __future__ import annotations

import re
from datetime import date, timedelta

import httpx

from ..config import settings

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
_BULLET_PREFIX_RE = re.compile(r"^\s*(?:[-*\u2022]|\d+[.)])\s*")


def _heuristic_insight(
    week_start: date,
    week_end: date,
    habit_stats: list[dict],
) -> list[str]:
    """Generate three bullets without an LLM.

    `habit_stats` items shape:
      {
        "name": str,
        "this_week": int,         # completions in [week_start, week_end]
        "prev_week": int,         # completions in the prior 7 days
        "this_week_rate": float,  # this_week / 7
        "best_day": str | None,   # weekday name with highest completion rate this week
        "worst_day": str | None,
      }
    """
    if not habit_stats:
        return [
            "No habits tracked yet — add a few to start seeing insights.",
            "Try starting with 2-3 habits so correlations and trends become meaningful.",
            "Aim for daily check-ins; even short streaks reveal day-of-week patterns.",
        ]

    bullets: list[str] = []

    best = max(habit_stats, key=lambda h: h["this_week_rate"])
    bullets.append(
        f"Strongest habit this week: \u201c{best['name']}\u201d "
        f"at {round(best['this_week_rate'] * 100)}% "
        f"({best['this_week']}/7 days)."
    )

    diffs = [(h, h["this_week"] - h["prev_week"]) for h in habit_stats]
    diffs.sort(key=lambda t: t[1])
    biggest_drop_habit, drop = diffs[0]
    biggest_gain_habit, gain = diffs[-1]
    if drop <= -2 and abs(drop) >= gain:
        bullets.append(
            f"Anomaly: \u201c{biggest_drop_habit['name']}\u201d dropped "
            f"{abs(drop)} days vs the prior week — worth investigating what changed."
        )
    elif gain >= 2:
        bullets.append(
            f"Notable improvement: \u201c{biggest_gain_habit['name']}\u201d is up "
            f"{gain} day(s) over the prior week."
        )
    else:
        bullets.append(
            "Week-over-week completion is stable across your habits — no large swings detected."
        )

    weakest = min(habit_stats, key=lambda h: h["this_week_rate"])
    if weakest["this_week_rate"] < 0.5 and weakest["worst_day"]:
        bullets.append(
            f"Suggestion: \u201c{weakest['name']}\u201d slipped most on {weakest['worst_day']}. "
            "Consider scheduling it earlier in the day or pairing it with an existing routine."
        )
    else:
        bullets.append(
            "Suggestion: pick one habit to deliberately push to a 7/7 streak next week to "
            "build momentum."
        )

    return bullets


async def _call_claude(prompt: str) -> list[str] | None:
    """Call the Anthropic Messages API. Returns None on any failure so callers can fall back."""
    if not settings.anthropic_api_key:
        return None
    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": settings.anthropic_model,
        "max_tokens": 400,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(ANTHROPIC_URL, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError):
        return None

    blocks = data.get("content") or []
    text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
    if not text:
        return None

    bullets: list[str] = []
    for line in text.splitlines():
        cleaned = _BULLET_PREFIX_RE.sub("", line.strip()).strip()
        if cleaned:
            bullets.append(cleaned)
        if len(bullets) == 3:
            break
    return bullets or None


def _format_prompt(week_start: date, week_end: date, habit_stats: list[dict]) -> str:
    lines = [
        "You are an analytics assistant for a personal habit tracker.",
        f"Analyze the past 7 days ({week_start.isoformat()} to {week_end.isoformat()}).",
        "Return EXACTLY 3 short bullet points, plain text, no markdown headers.",
        "Bullet 1: pattern. Bullet 2: anomaly. Bullet 3: suggestion.",
        "",
        "Per-habit stats:",
    ]
    for h in habit_stats:
        lines.append(
            f"- {h['name']}: this_week={h['this_week']}/7, prev_week={h['prev_week']}/7, "
            f"best_day={h['best_day']}, worst_day={h['worst_day']}"
        )
    return "\n".join(lines)


async def weekly_insight(
    week_start: date,
    week_end: date,
    habit_stats: list[dict],
) -> tuple[list[str], str]:
    """Return (bullets, source) where source is 'claude' or 'heuristic'."""
    if settings.anthropic_api_key:
        prompt = _format_prompt(week_start, week_end, habit_stats)
        bullets = await _call_claude(prompt)
        if bullets:
            return bullets[:3], "claude"
    return _heuristic_insight(week_start, week_end, habit_stats), "heuristic"


# Re-export `timedelta` so tests/callers can import from a single module.
__all__ = ["weekly_insight", "timedelta"]
