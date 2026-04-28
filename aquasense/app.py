"""AquaSense Flask application factory and background alert monitor."""

from datetime import date
import threading
import time
import os
import anthropic

from flask import Flask
from flask import render_template 

from aquasense.blueprints.admin import admin_bp
from aquasense.blueprints.auth import auth_bp
from aquasense.blueprints.chatbot import chatbot_bp
from aquasense.blueprints.cost import cost_bp
from aquasense.blueprints.dashboard import dashboard_bp
from aquasense.blueprints.gamification import gamification_bp
from aquasense.blueprints.predictions import predictions_bp
from aquasense.blueprints.report import report_bp
from aquasense.blueprints.usage import usage_bp
from aquasense.config import ALERT_CHECK_INTERVAL, SECRET_KEY
from aquasense.database import init_db
from aquasense.db_helper import close_db, execute_query, fetch_all, fetch_one


def alert_monitor(app):
    """Check threshold alerts every interval; inputs: Flask app; output: runs until process exits."""
    with app.app_context():
        while True:
            try:
                today = date.today().isoformat()
                users = fetch_all("SELECT id, threshold FROM users")
                for user in users:
                    usage = fetch_one(
                        "SELECT COALESCE(SUM(amount_litres), 0) AS total FROM usage_records WHERE user_id = ? AND date = ?",
                        (user["id"], today),
                    )
                    already_alerted = fetch_one(
                        "SELECT id FROM alerts WHERE user_id = ? AND date = ? AND message LIKE ?",
                        (user["id"], today, "%exceeded threshold%"),
                    )
                    if usage and float(usage["total"]) > float(user["threshold"]) and not already_alerted:
                        execute_query(
                            "INSERT INTO alerts (user_id, date, message) VALUES (?, ?, ?)",
                            (user["id"], today, f"Today's usage exceeded threshold: {round(usage['total'], 2)}L."),
                        )
            except Exception as exc:
                print(f"AquaSense alert monitor error: {exc}")
            time.sleep(ALERT_CHECK_INTERVAL)


def create_app():
    """Create and configure the Flask app; inputs: none; output: Flask app."""
    app = Flask(__name__)
    app.config.from_object('aquasense.config')
    init_db()

    @app.route("/")
    def home():
      return render_template("dashboard.html")

    import anthropic
    import os
    os.environ['ANTHROPIC_API_KEY'] = app.config.get('ANTHROPIC_API_KEY', 'test_key')

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(usage_bp)
    app.register_blueprint(predictions_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(cost_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(gamification_bp)
    app.teardown_appcontext(close_db)

    monitor_thread = threading.Thread(target=alert_monitor, args=(app,), daemon=True)
    monitor_thread.start()
    print("AquaSense startup complete: all blueprints registered and background alert thread is running.")
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
