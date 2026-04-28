"""Dashboard route."""

from datetime import date, timedelta

from flask import Blueprint, session
from flask import render_template

from aquasense.db_helper import fetch_all, fetch_one
from aquasense.ml.anomaly import AnomalyDetector
from aquasense.utils.decorators import login_required
from aquasense.utils.weather import get_weather
from aquasense.blueprints.gamification import calculate_conservation_score, calculate_streak

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    """Build dashboard data; inputs: logged-in session; output: rendered dashboard page."""
    user_id = session["user_id"]
    today = date.today()
    user = fetch_one("SELECT id, name, email, role, city, threshold, streak, conservation_score FROM users WHERE id = ?", (user_id,))
    today_usage = fetch_one("SELECT COALESCE(SUM(amount_litres), 0) AS total FROM usage_records WHERE user_id = ? AND date = ?", (user_id, today.isoformat()))["total"]
    weekly_total = fetch_one("SELECT COALESCE(SUM(amount_litres), 0) AS total FROM usage_records WHERE user_id = ? AND date >= ?", (user_id, (today - timedelta(days=6)).isoformat()))["total"]
    monthly_total = fetch_one("SELECT COALESCE(SUM(amount_litres), 0) AS total FROM usage_records WHERE user_id = ? AND date >= ?", (user_id, today.replace(day=1).isoformat()))["total"]
    threshold = float(user["threshold"])
    threshold_status = "exceeded" if today_usage > threshold else "approaching" if today_usage >= threshold * 0.8 else "under"
    alerts = [dict(row) for row in fetch_all("SELECT * FROM alerts WHERE user_id = ? ORDER BY triggered_at DESC LIMIT 10", (user_id,))]
    records = [dict(row) for row in fetch_all("SELECT * FROM usage_records WHERE user_id = ? ORDER BY date DESC LIMIT 30", (user_id,))]
    badges = [dict(row) for row in fetch_all("SELECT * FROM badges WHERE user_id = ? ORDER BY earned_at DESC LIMIT 4", (user_id,))]
    weekly_rows = fetch_all(
        "SELECT date, COALESCE(SUM(amount_litres), 0) AS total FROM usage_records WHERE user_id = ? AND date >= ? GROUP BY date",
        (user_id, (today - timedelta(days=6)).isoformat()),
    )
    weekly_usage = {row["date"]: float(row["total"]) for row in weekly_rows}
    weekly_dates = [(today - timedelta(days=offset)) for offset in range(6, -1, -1)]
    weekly_labels = [day.strftime("%a") for day in weekly_dates]
    weekly_data = [weekly_usage.get(day.isoformat(), 0) for day in weekly_dates]
    detector = AnomalyDetector()
    streak = calculate_streak(user_id)
    conservation_score = calculate_conservation_score(user_id)
    user_data = {key: user[key] for key in user.keys()}
    user_data["streak"] = streak
    user_data["conservation_score"] = conservation_score
    stats = {
        "today_usage": today_usage,
        "week_usage": weekly_total,
        "month_usage": monthly_total,
        "threshold": threshold,
        "threshold_remaining": max(round(threshold - today_usage, 2), 0),
        "weekly_labels": weekly_labels,
        "weekly_data": weekly_data,
    }

    return render_template(
        "dashboard.html",
        user=user_data,
        stats=stats,
        today_usage=today_usage,
        weekly_total=weekly_total,
        monthly_total=monthly_total,
        threshold_status=threshold_status,
        alerts=alerts,
        badges=badges,
        weather=get_weather(user["city"]),
        anomalies=detector.detect_zscore(records),
        streak=streak,
        conservation_score=conservation_score,
    )
