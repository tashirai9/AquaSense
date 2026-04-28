"""Prediction routes."""

from flask import Blueprint, session

from aquasense.db_helper import execute_query, fetch_all
from aquasense.ml.predictor import DecisionTreePredictor, LinearRegressionPredictor, RandomForestPredictor
from aquasense.utils.decorators import login_required

predictions_bp = Blueprint("predictions", __name__)


@predictions_bp.get("/predictions")
@login_required
def predictions():
    """Run all usage predictors; inputs: current user records; output: model results dict."""
    user_id = session["user_id"]
    records = [dict(row) for row in fetch_all("SELECT * FROM usage_records WHERE user_id = ? ORDER BY date", (user_id,))]
    if len(records) < 7:
        return {"error": "At least 7 historical usage records are required for predictions."}, 400
    models = [LinearRegressionPredictor(), RandomForestPredictor(), DecisionTreePredictor()]
    results = [model.predict(records) for model in models]
    successful = [result for result in results if "error" not in result]
    if not successful:
        return {"error": "All prediction models failed.", "results": results}, 500
    best = max(successful, key=lambda result: result["r2_score"])
    for result in successful:
        for item in result["predictions"]:
            execute_query(
                "INSERT INTO predictions (user_id, predicted_date, predicted_litres, model_used) VALUES (?, ?, ?, ?)",
                (user_id, item["date"], item["predicted_litres"], result["model"]),
            )
        result["is_best"] = result["model"] == best["model"]
    return {"results": results, "best_model": best["model"]}
