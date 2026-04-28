"""Water cost calculation routes."""

from datetime import date

from flask import Blueprint, request, session

from aquasense.db_helper import fetch_one
from aquasense.utils.decorators import login_required

cost_bp = Blueprint("cost", __name__)


@cost_bp.route("/cost", methods=["GET", "POST"])
@login_required
def cost():
    """Calculate cost projections; inputs: optional tariff/threshold; output: cost dict."""
    data = request.get_json(silent=True) or request.form or request.args
    user = fetch_one("SELECT tariff_rate, threshold FROM users WHERE id = ?", (session["user_id"],))
    try:
        tariff = float(data.get("tariff_rate", user["tariff_rate"]))
        threshold = float(data.get("threshold", data.get("custom_threshold", user["threshold"])))
        if tariff < 0 or threshold <= 0:
            return {"error": "Tariff must be non-negative and threshold must be positive."}, 400
    except Exception:
        return {"error": "Invalid tariff_rate or threshold."}, 400

    today = date.today()
    today_usage = fetch_one("SELECT COALESCE(SUM(amount_litres), 0) AS total FROM usage_records WHERE user_id = ? AND date = ?", (session["user_id"], today.isoformat()))["total"]
    avg_daily = fetch_one("SELECT COALESCE(AVG(daily_total), 0) AS avg_usage FROM (SELECT date, SUM(amount_litres) AS daily_total FROM usage_records WHERE user_id = ? GROUP BY date)", (session["user_id"],))["avg_usage"]
    monthly_bill = avg_daily * 30 * tariff
    threshold_bill = threshold * 30 * tariff
    return {
        "today_cost": round(today_usage * tariff, 2),
        "monthly_estimated_bill": round(monthly_bill, 2),
        "projected_annual_spend": round(monthly_bill * 12, 2),
        "potential_monthly_savings": round(max(0, monthly_bill - threshold_bill), 2),
        "tariff_rate": tariff,
        "threshold": threshold,
    }
