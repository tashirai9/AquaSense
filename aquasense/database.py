"""Database schema creation for AquaSense."""

import os
import sqlite3

from aquasense.config import DATABASE_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user' CHECK(role IN ('user', 'admin')),
    city TEXT,
    tariff_rate REAL DEFAULT 0.05,
    threshold REAL DEFAULT 200.0,
    streak INTEGER DEFAULT 0,
    conservation_score REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usage_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    amount_litres REAL NOT NULL,
    season TEXT,
    time_of_day TEXT,
    is_anomaly INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    date TEXT,
    message TEXT,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS badges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    badge_name TEXT,
    badge_icon TEXT,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, badge_name)
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    predicted_date TEXT,
    predicted_litres REAL,
    model_used TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db():
    """Create all SQLite tables; inputs: none; output: none."""
    try:
        db_path = DATABASE_PATH if os.path.isabs(DATABASE_PATH) else os.path.join(os.path.dirname(__file__), DATABASE_PATH)
        with sqlite3.connect(db_path) as conn:
            conn.executescript(SCHEMA)
            conn.commit()
    except sqlite3.Error as exc:
        raise RuntimeError(f"Database initialization failed: {exc}") from exc


if __name__ == "__main__":
    init_db()
    print("AquaSense database initialized.")
