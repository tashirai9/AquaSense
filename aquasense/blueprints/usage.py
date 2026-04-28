"""Usage logging and history routes."""

from datetime import date, datetime, timedelta

from flask import Blueprint, flash, request, session

from aquasense.db_helper import execute_query, fetch_all, fetch_one
from aquasense.ml.anomaly import AnomalyDetector
from aquasense.models.alert import Alert
from aquasense.models.usage import UsageRecord
from aquasense.utils.decorators import login_required
from aquasense.blueprints.gamification import calculate_conservation_score, calculate_streak, check_and_award_badges

usage_bp = Blueprint("usage", __name__)


def _valid_date(value):
    """Validate ISO date; inputs: date string; output: same string or ValueError."""
    datetime.strptime(value, "%Y-%m-%d")
    return value


@usage_bp.post("/log")
@login_required
def log_usage():
    """Log water usage and trigger checks; inputs: form/json record fields; output: redirect dict."""
    data = request.get_json(silent=True) or request.form
    try:
        user_id = session["user_id"]
        usage_date = _valid_date(data.get("date", date.today().isoformat()))
        amount = float(data.get("amount_litres"))
        season = data.get("season", "").strip().lower()
        time_of_day = data.get("time_of_day", "").strip()
        if amount <= 0 or amount > 100000:
            return {"error": "amount_litres must be between 0 and 100000."}, 400

        record_id = UsageRecord(user_id, usage_date, amount, season, time_of_day).save()
        records = [dict(row) for row in fetch_all("SELECT * FROM usage_records WHERE user_id = ?", (user_id,))]
        flagged = AnomalyDetector().detect_zscore(records)
        if any(item["date"] == usage_date and item["amount_litres"] == amount for item in flagged):
            execute_query("UPDATE usage_records SET is_anomaly = 1 WHERE id = ?", (record_id,))

        user = fetch_one("SELECT threshold FROM users WHERE id = ?", (user_id,))
        if amount > float(user["threshold"]):
            Alert(user_id, f"Usage exceeded threshold: {amount}L logged against {user['threshold']}L.", usage_date).save()

        badges = check_and_award_badges(user_id)
        streak = calculate_streak(user_id)
        score = calculate_conservation_score(user_id)
        flash("Usage logged successfully.", "success")
        return {"message": "Usage logged successfully.", "record_id": record_id, "badges_awarded": badges, "streak": streak, "conservation_score": score, "redirect": "/dashboard"}
    except Exception as exc:
        return {"error": f"Usage logging failed: {exc}"}, 400


@usage_bp.get("/history")
@login_required
def history():
    """Fetch usage history with optional period filter; inputs: query filter; output: records dict."""
    period = request.args.get("filter")
    params = [session["user_id"]]
    where = "WHERE user_id = ?"
    if period in {"week", "month", "year"}:
        days = {"week": 7, "month": 31, "year": 365}[period]
        where += " AND date >= ?"
        params.append((date.today() - timedelta(days=days)).isoformat())
    rows = fetch_all(f"SELECT * FROM usage_records {where} ORDER BY date DESC", tuple(params))
    return {"records": [dict(row) for row in rows]}
