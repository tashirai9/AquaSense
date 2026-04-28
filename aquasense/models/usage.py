"""Usage record model for AquaSense."""

from aquasense.db_helper import execute_query, fetch_all


class UsageRecord:
    """Represents one water usage entry."""

    def __init__(self, user_id, date, amount_litres, season=None, time_of_day=None, is_anomaly=0):
        """Create a usage record; inputs: record fields; output: instance."""
        self.user_id = user_id
        self.date = date
        self.amount_litres = amount_litres
        self.season = season
        self.time_of_day = time_of_day
        self.is_anomaly = is_anomaly

    def save(self):
        """Persist this record; inputs: none; output: inserted record id."""
        return execute_query(
            "INSERT INTO usage_records (user_id, date, amount_litres, season, time_of_day, is_anomaly) VALUES (?, ?, ?, ?, ?, ?)",
            (self.user_id, self.date, self.amount_litres, self.season, self.time_of_day, self.is_anomaly),
        )

    def to_dict(self):
        """Serialize the record; inputs: none; output: dict."""
        return self.__dict__.copy()

    @staticmethod
    def get_by_user(user_id):
        """Fetch records for one user; inputs: user id; output: list of dicts."""
        rows = fetch_all("SELECT * FROM usage_records WHERE user_id = ? ORDER BY date DESC", (user_id,))
        return [dict(row) for row in rows]
