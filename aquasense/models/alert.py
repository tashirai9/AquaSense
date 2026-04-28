"""Alert model for AquaSense."""

from datetime import date as date_cls

from aquasense.db_helper import execute_query, fetch_all


class Alert:
    """Represents a threshold or anomaly alert."""

    def __init__(self, user_id, message, date=None):
        """Create an alert; inputs: user id, message, optional date; output: instance."""
        self.user_id = user_id
        self.message = message
        self.date = date or date_cls.today().isoformat()

    def save(self):
        """Persist this alert; inputs: none; output: inserted alert id."""
        return execute_query("INSERT INTO alerts (user_id, date, message) VALUES (?, ?, ?)", (self.user_id, self.date, self.message))

    @staticmethod
    def get_by_user(user_id):
        """Fetch alerts for one user; inputs: user id; output: list of dicts."""
        rows = fetch_all("SELECT * FROM alerts WHERE user_id = ? ORDER BY triggered_at DESC", (user_id,))
        return [dict(row) for row in rows]
