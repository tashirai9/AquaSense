"""Monthly PDF report route."""

from datetime import date
import io

from flask import Blueprint, send_file, session
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from aquasense.db_helper import fetch_all, fetch_one
from aquasense.ml.predictor import DecisionTreePredictor, LinearRegressionPredictor, RandomForestPredictor
from aquasense.utils.decorators import login_required
from aquasense.utils.tips import get_tips

report_bp = Blueprint("report", __name__)


@report_bp.get("/report")
@login_required
def report():
    """Generate a monthly PDF report; inputs: current user; output: send_file PDF response."""
    user_id = session["user_id"]
    today = date.today()
    first_day = today.replace(day=1).isoformat()
    user = fetch_one("SELECT name, tariff_rate, threshold FROM users WHERE id = ?", (user_id,))
    summary = fetch_one("SELECT COALESCE(SUM(amount_litres), 0) AS total, COALESCE(AVG(amount_litres), 0) AS avg_usage FROM usage_records WHERE user_id = ? AND date >= ?", (user_id, first_day))
    anomalies = fetch_one("SELECT COUNT(*) AS count FROM usage_records WHERE user_id = ? AND is_anomaly = 1 AND date >= ?", (user_id, first_day))["count"]
    badges = fetch_all("SELECT badge_name, badge_icon FROM badges WHERE user_id = ? AND earned_at >= datetime(?)", (user_id, first_day))
    today_usage = fetch_one("SELECT COALESCE(SUM(amount_litres), 0) AS total FROM usage_records WHERE user_id = ? AND date = ?", (user_id, today.isoformat()))["total"]
    records = [dict(row) for row in fetch_all("SELECT * FROM usage_records WHERE user_id = ? ORDER BY date", (user_id,))]

    best_accuracy = "Not enough data"
    if len(records) >= 7:
        results = [model.predict(records) for model in (LinearRegressionPredictor(), RandomForestPredictor(), DecisionTreePredictor())]
        good = [result for result in results if "error" not in result]
        if good:
            best = max(good, key=lambda item: item["r2_score"])
            best_accuracy = f"{best['model']} R2={best['r2_score']} RMSE={best['rmse']}"

    monthly_cost = float(summary["avg_usage"]) * 30 * float(user["tariff_rate"])
    tips = get_tips(today_usage, None)[:3]
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    y = 760
    lines = [
        "AquaSense Monthly Report",
        f"User: {user['name']} | Month: {today.strftime('%B %Y')}",
        f"Total usage: {round(summary['total'], 2)} L",
        f"Daily average: {round(summary['avg_usage'], 2)} L",
        f"Anomalies detected: {anomalies}",
        f"Prediction accuracy: {best_accuracy}",
        f"Badges earned this month: {', '.join([row['badge_name'] for row in badges]) or 'None'}",
        f"Estimated monthly water cost: Rs {round(monthly_cost, 2)}",
        "Top water saving tips:",
    ]
    for tip in tips:
        lines.append(f"- {tip['tip']}")
    for line in lines:
        pdf.drawString(50, y, line)
        y -= 24
    pdf.save()
    buffer.seek(0)
    return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name="aquasense_monthly_report.pdf")
