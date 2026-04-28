"""Badge model for AquaSense."""

from aquasense.db_helper import execute_query, fetch_all


class Badge:
    """Represents a gamification badge."""

    def __init__(self, user_id, badge_name, badge_icon):
        """Create a badge; inputs: user id, name, icon; output: instance."""
        self.user_id = user_id
        self.badge_name = badge_name
        self.badge_icon = badge_icon

    def save(self):
        """Persist this badge if not already earned; inputs: none; output: inserted id or 0."""
        return execute_query(
            "INSERT OR IGNORE INTO badges (user_id, badge_name, badge_icon) VALUES (?, ?, ?)",
            (self.user_id, self.badge_name, self.badge_icon),
        )

    @staticmethod
    def get_by_user(user_id):
        """Fetch badges for one user; inputs: user id; output: list of dicts."""
        rows = fetch_all("SELECT * FROM badges WHERE user_id = ? ORDER BY earned_at DESC", (user_id,))
        return [dict(row) for row in rows]
