"""User domain classes for AquaSense."""

from abc import ABC, abstractmethod
import csv
import io

from aquasense.db_helper import execute_query, fetch_all, fetch_one


try:
    import bcrypt
except ImportError:
    bcrypt = None
    from werkzeug.security import check_password_hash


class MonitorBase(ABC):
    """Abstract contract for water monitoring users."""

    @abstractmethod
    def log_usage(self, amount_litres, date, season=None, time_of_day=None):
        """Log water usage; inputs: amount, date, optional season/time; output: record id."""

    @abstractmethod
    def get_summary(self):
        """Return usage summary; inputs: none; output: dict."""

    @abstractmethod
    def send_alert(self, message, date=None):
        """Create an alert; inputs: message and optional date; output: alert id."""


class User:
    """Base AquaSense user object."""

    def __init__(self, id, name, email, password_hash, role="user"):
        """Create a user object; inputs: user columns; output: instance."""
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.role = role

    def check_password(self, password):
        """Verify a password; inputs: plaintext password; output: boolean."""
        if bcrypt:
            return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Serialize safe user fields; inputs: none; output: dict without password_hash."""
        return {"id": self.id, "name": self.name, "email": self.email, "role": self.role}


class RegularUser(User, MonitorBase):
    """Regular user with monitoring metrics."""

    def __init__(self, id, name, email, password_hash, role="user", threshold=200.0, streak=0, conservation_score=0.0):
        """Create a regular user; inputs: user and score fields; output: instance."""
        super().__init__(id, name, email, password_hash, role)
        self.threshold = threshold
        self.streak = streak
        self.conservation_score = conservation_score

    def log_usage(self, amount_litres, date, season=None, time_of_day=None):
        """Insert a usage record; inputs: amount, date, season, time; output: record id."""
        return execute_query(
            "INSERT INTO usage_records (user_id, date, amount_litres, season, time_of_day) VALUES (?, ?, ?, ?, ?)",
            (self.id, date, amount_litres, season, time_of_day),
        )

    def get_summary(self):
        """Return totals and averages; inputs: none; output: dict."""
        row = fetch_one(
            "SELECT COUNT(*) AS days, COALESCE(SUM(amount_litres), 0) AS total, COALESCE(AVG(amount_litres), 0) AS avg_usage "
            "FROM usage_records WHERE user_id = ?",
            (self.id,),
        )
        return dict(row) if row else {"days": 0, "total": 0.0, "avg_usage": 0.0}

    def send_alert(self, message, date=None):
        """Insert a user alert; inputs: message and date; output: alert id."""
        return execute_query("INSERT INTO alerts (user_id, date, message) VALUES (?, ?, ?)", (self.id, date, message))

    def to_dict(self):
        """Serialize safe regular user fields; inputs: none; output: dict."""
        data = super().to_dict()
        data.update({"threshold": self.threshold, "streak": self.streak, "conservation_score": self.conservation_score})
        return data


class AdminUser(User, MonitorBase):
    """Administrator user with platform reporting tools."""

    def log_usage(self, amount_litres, date, season=None, time_of_day=None):
        """Insert an admin usage record; inputs: amount, date, season, time; output: record id."""
        return execute_query(
            "INSERT INTO usage_records (user_id, date, amount_litres, season, time_of_day) VALUES (?, ?, ?, ?, ?)",
            (self.id, date, amount_litres, season, time_of_day),
        )

    def get_summary(self):
        """Return admin's own usage summary; inputs: none; output: dict."""
        row = fetch_one(
            "SELECT COUNT(*) AS days, COALESCE(SUM(amount_litres), 0) AS total, COALESCE(AVG(amount_litres), 0) AS avg_usage "
            "FROM usage_records WHERE user_id = ?",
            (self.id,),
        )
        return dict(row) if row else {"days": 0, "total": 0.0, "avg_usage": 0.0}

    def send_alert(self, message, date=None):
        """Insert an admin alert; inputs: message and date; output: alert id."""
        return execute_query("INSERT INTO alerts (user_id, date, message) VALUES (?, ?, ?)", (self.id, date, message))

    def get_all_users(self):
        """Fetch all users; inputs: none; output: list of safe dicts."""
        rows = fetch_all("SELECT id, name, email, role, city, threshold, tariff_rate, streak, conservation_score, created_at FROM users")
        return [dict(row) for row in rows]

    def get_platform_stats(self):
        """Fetch platform metrics; inputs: none; output: dict."""
        return {
            "total_users": fetch_one("SELECT COUNT(*) AS count FROM users")["count"],
            "average_daily_usage": fetch_one("SELECT COALESCE(AVG(amount_litres), 0) AS avg_usage FROM usage_records")["avg_usage"],
            "total_alerts": fetch_one("SELECT COUNT(*) AS count FROM alerts")["count"],
            "total_anomalies": fetch_one("SELECT COUNT(*) AS count FROM usage_records WHERE is_anomaly = 1")["count"],
        }

    def export_csv(self):
        """Export usage records to CSV text; inputs: none; output: CSV string."""
        rows = fetch_all("SELECT * FROM usage_records ORDER BY date DESC")
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "user_id", "date", "amount_litres", "season", "time_of_day", "is_anomaly", "created_at"])
        for row in rows:
            writer.writerow([row[key] for key in row.keys()])
        return output.getvalue()
