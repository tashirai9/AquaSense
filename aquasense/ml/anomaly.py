"""Anomaly detection for AquaSense usage records."""

import numpy as np
from sklearn.ensemble import IsolationForest


class AnomalyDetector:
    """Detect unusually high water usage days."""

    def detect_zscore(self, records):
        """Flag records above mean + 2 stddev; inputs: records; output: list of flagged dicts."""
        if not records:
            return []
        amounts = np.array([float(record["amount_litres"]) for record in records])
        mean = amounts.mean()
        std = amounts.std()
        limit = mean + (2 * std)
        return [
            {"date": record["date"], "amount_litres": float(record["amount_litres"])}
            for record in records
            if float(record["amount_litres"]) > limit
        ]

    def detect_isolation_forest(self, records):
        """Use IsolationForest to flag anomalous usage; inputs: records; output: list of flagged dicts."""
        if len(records) < 5:
            return []
        try:
            values = np.array([[float(record["amount_litres"])] for record in records])
            model = IsolationForest(contamination="auto", random_state=42)
            labels = model.fit_predict(values)
            return [
                {"date": record["date"], "amount_litres": float(record["amount_litres"])}
                for record, label in zip(records, labels)
                if label == -1
            ]
        except Exception:
            return []
