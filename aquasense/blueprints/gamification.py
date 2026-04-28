"""Gamification helpers and badge awarding."""

from datetime import date, timedelta

from flask import Blueprint, session

from aquasense.db_helper import execute_query, fetch_all, fetch_one
from aquasense.models.badge import Badge
from aquasense.utils.decorators import login_required

gamification_bp = Blueprint("gamification", __name__)


def _award_once(user_id, name, icon):
    """Award a badge if missing; inputs: user id, name, icon; output: inserted id or 0."""
    return Badge(user_id, name, icon).save()


def calculate_streak(user_id):
    """Count consecutive days under threshold from today backwards; inputs: user id; output: streak integer."""
    user = fetch_one("SELECT threshold FROM users WHERE id = ?", (user_id,))
    if not user:
        return 0
    threshold = float(user["threshold"])
    streak = 0
    current = date.today()
    while True:
        row = fetch_one(
            "SELECT COALESCE(SUM(amount_litres), 0) AS total FROM usage_records WHERE user_id = ? AND date = ?",
            (user_id, current.isoformat()),
        )
        if not row or row["total"] <= 0 or float(row["total"]) > threshold:
            break
        streak += 1
        current -= timedelta(days=1)
    execute_query("UPDATE users SET streak = ? WHERE id = ?", (streak, user_id))
    return streak


def calculate_conservation_score(user_id):
    """Calculate percent of logged days under threshold; inputs: user id; output: score."""
    user = fetch_one("SELECT threshold FROM users WHERE id = ?", (user_id,))
    if not user:
        return 0.0
    row = fetch_one(
        "SELECT COUNT(*) AS total, SUM(CASE WHEN daily_total <= ? THEN 1 ELSE 0 END) AS under_days "
        "FROM (SELECT date, SUM(amount_litres) AS daily_total FROM usage_records WHERE user_id = ? GROUP BY date)",
        (float(user["threshold"]), user_id),
    )
    total = row["total"] or 0
    score = round(((row["under_days"] or 0) / total) * 100, 2) if total else 0.0
    execute_query("UPDATE users SET conservation_score = ? WHERE id = ?", (score, user_id))
    return score


def check_and_award_badges(user_id):
    """Evaluate and award conservation badges; inputs: user id; output: list of earned badge dicts."""
    earned = []
    count = fetch_one("SELECT COUNT(*) AS count FROM usage_records WHERE user_id = ?", (user_id,))["count"]
    if count == 1 and _award_once(user_id, "First Log", "💧"):
        earned.append({"badge_name": "First Log", "badge_icon": "💧"})

    streak = calculate_streak(user_id)
    if streak >= 3 and _award_once(user_id, "3 Day Streak", "🌱"):
        earned.append({"badge_name": "3 Day Streak", "badge_icon": "🌱"})
    if streak >= 7 and _award_once(user_id, "Week Warrior", "⚡"):
        earned.append({"badge_name": "Week Warrior", "badge_icon": "⚡"})

    avg_row = fetch_one("SELECT AVG(amount_litres) AS avg_usage FROM usage_records WHERE user_id = ?", (user_id,))
    platform = fetch_one("SELECT AVG(amount_litres) AS avg_usage FROM usage_records")["avg_usage"] or 150.0
    if avg_row["avg_usage"] and float(avg_row["avg_usage"]) <= float(platform) * 0.8:
        if _award_once(user_id, "Eco Champion", "🌍"):
            earned.append({"badge_name": "Eco Champion", "badge_icon": "🌍"})

    first_day = date.today().replace(day=1).isoformat()
    user = fetch_one("SELECT threshold FROM users WHERE id = ?", (user_id,))
    month_rows = fetch_all(
        "SELECT date, SUM(amount_litres) AS total FROM usage_records WHERE user_id = ? AND date >= ? GROUP BY date",
        (user_id, first_day),
    )
    if month_rows and all(float(row["total"]) <= float(user["threshold"]) for row in month_rows):
        if _award_once(user_id, "Saver of the Month", "🏆"):
            earned.append({"badge_name": "Saver of the Month", "badge_icon": "🏆"})

    calculate_conservation_score(user_id)
    return earned


@gamification_bp.get("/badges")
@login_required
def badges():
    """Return current user's badges; inputs: session user; output: dict."""
    rows = fetch_all("SELECT * FROM badges WHERE user_id = ? ORDER BY earned_at DESC", (session["user_id"],))
    return {"badges": [dict(row) for row in rows]}
