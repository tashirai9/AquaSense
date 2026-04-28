"""Admin-only routes."""

import csv
import io
from datetime import date

from flask import Blueprint, send_file

from aquasense.db_helper import fetch_all, fetch_one
from aquasense.utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/admin")
@admin_required
def admin_dashboard():
    """Return platform metrics; inputs: admin session; output: stats dict."""
    top_users = fetch_all(
        "SELECT u.name, u.email, AVG(r.amount_litres) AS avg_usage FROM users u "
        "JOIN usage_records r ON u.id = r.user_id GROUP BY u.id ORDER BY avg_usage DESC LIMIT 5"
    )
    return {
        "total_registered_users": fetch_one("SELECT COUNT(*) AS count FROM users")["count"],
        "platform_average_daily_usage": fetch_one("SELECT COALESCE(AVG(amount_litres), 0) AS avg_usage FROM usage_records")["avg_usage"],
        "top_5_highest_consuming_users": [dict(row) for row in top_users],
        "total_alerts_triggered_today": fetch_one("SELECT COUNT(*) AS count FROM alerts WHERE date = ?", (date.today().isoformat(),))["count"],
        "total_anomalies_detected": fetch_one("SELECT COUNT(*) AS count FROM usage_records WHERE is_anomaly = 1")["count"],
    }


@admin_bp.get("/admin/export")
@admin_required
def export_usage():
    """Export usage records as CSV; inputs: admin session; output: downloadable CSV response."""
    rows = fetch_all("SELECT * FROM usage_records ORDER BY date DESC")
    text = io.StringIO()
    writer = csv.writer(text)
    writer.writerow(["id", "user_id", "date", "amount_litres", "season", "time_of_day", "is_anomaly", "created_at"])
    for row in rows:
        writer.writerow([row[key] for key in row.keys()])
    buffer = io.BytesIO(text.getvalue().encode("utf-8"))
    return send_file(buffer, mimetype="text/csv", as_attachment=True, download_name="aquasense_usage_records.csv")
