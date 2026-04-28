"""Reusable SQLite helpers used by every AquaSense module."""

import os
import sqlite3
from flask import g

from aquasense.config import DATABASE_PATH


def _database_file():
    """Return the absolute database path; inputs: none; output: file path string."""
    return DATABASE_PATH if os.path.isabs(DATABASE_PATH) else os.path.join(os.path.dirname(__file__), DATABASE_PATH)


def get_db():
    """Open or reuse a SQLite connection for the current Flask context; inputs: none; output: connection."""
    if "db" not in g:
        g.db = sqlite3.connect(_database_file())
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    """Close the request-scoped SQLite connection; inputs: optional error; output: none."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def execute_query(query, params=(), commit=True):
    """Run an INSERT/UPDATE/DELETE query; inputs: SQL and params; output: last inserted row id."""
    try:
        db = get_db()
        cursor = db.execute(query, params)
        if commit:
            db.commit()
        return cursor.lastrowid
    except sqlite3.Error as exc:
        get_db().rollback()
        raise RuntimeError(f"Database write failed: {exc}") from exc


def fetch_one(query, params=()):
    """Fetch a single row; inputs: SQL and params; output: sqlite Row or None."""
    try:
        return get_db().execute(query, params).fetchone()
    except sqlite3.Error as exc:
        raise RuntimeError(f"Database read failed: {exc}") from exc


def fetch_all(query, params=()):
    """Fetch all matching rows; inputs: SQL and params; output: list of sqlite Rows."""
    try:
        return get_db().execute(query, params).fetchall()
    except sqlite3.Error as exc:
        raise RuntimeError(f"Database read failed: {exc}") from exc
