"""Water usage prediction models."""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.tree import DecisionTreeRegressor


SEASONS = {"spring": 0, "summer": 1, "autumn": 2, "fall": 2, "winter": 3}


class Predictor(ABC):
    """Abstract predictor contract."""

    @abstractmethod
    def predict(self, data):
        """Train and predict usage; inputs: historical records; output: metrics and predictions."""


class BaseSklearnPredictor(Predictor):
    """Shared feature engineering and training for sklearn regressors."""

    model_cls = None
    model_kwargs = {}
    model_name = "Base Model"

    def get_model_name(self):
        """Return display model name; inputs: none; output: string."""
        return self.model_name

    def _features(self, records):
        """Convert records to ML features; inputs: records; output: X, y, sorted records."""
        sorted_records = sorted(records, key=lambda item: item["date"])
        x_values, y_values, prev_usage = [], [], 0.0
        for record in sorted_records:
            dt = datetime.strptime(record["date"], "%Y-%m-%d")
            season = (record.get("season") or "").lower()
            x_values.append([dt.weekday(), dt.month, SEASONS.get(season, 0), prev_usage])
            amount = float(record["amount_litres"])
            y_values.append(amount)
            prev_usage = amount
        return np.array(x_values), np.array(y_values), sorted_records

    def predict(self, data):
        """Train the model and predict next 7 days; inputs: historical records; output: dict."""
        if len(data) < 7:
            return {"error": "At least 7 historical usage records are required for predictions."}
        try:
            x_values, y_values, sorted_records = self._features(data)
            model = self.model_cls(**self.model_kwargs)
            model.fit(x_values, y_values)
            fitted = model.predict(x_values)
            r2 = float(r2_score(y_values, fitted))
            try:
                rmse = float(mean_squared_error(y_values, fitted, squared=False))
            except TypeError:
                rmse = float(mean_squared_error(y_values, fitted) ** 0.5)

            last_date = datetime.strptime(sorted_records[-1]["date"], "%Y-%m-%d")
            prev_usage = float(sorted_records[-1]["amount_litres"])
            season_code = SEASONS.get((sorted_records[-1].get("season") or "").lower(), 0)
            predictions = []
            for day in range(1, 8):
                target_date = last_date + timedelta(days=day)
                feature = np.array([[target_date.weekday(), target_date.month, season_code, prev_usage]])
                predicted = max(0.0, float(model.predict(feature)[0]))
                predictions.append({"date": target_date.date().isoformat(), "predicted_litres": round(predicted, 2)})
                prev_usage = predicted
            return {"model": self.get_model_name(), "r2_score": round(r2, 4), "rmse": round(rmse, 4), "predictions": predictions}
        except Exception as exc:
            return {"model": self.get_model_name(), "error": f"Prediction failed: {exc}"}


class LinearRegressionPredictor(BaseSklearnPredictor):
    """Linear regression predictor."""

    model_cls = LinearRegression
    model_name = "Linear Regression"


class RandomForestPredictor(BaseSklearnPredictor):
    """Random forest predictor."""

    model_cls = RandomForestRegressor
    model_kwargs = {"n_estimators": 100, "random_state": 42}
    model_name = "Random Forest"


class DecisionTreePredictor(BaseSklearnPredictor):
    """Decision tree predictor."""

    model_cls = DecisionTreeRegressor
    model_kwargs = {"random_state": 42}
    model_name = "Decision Tree"
