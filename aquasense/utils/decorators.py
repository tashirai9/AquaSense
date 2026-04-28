"""Route protection decorators."""

from functools import wraps
from flask import redirect, session


def login_required(view):
    """Require an active user session; inputs: route function; output: wrapped function."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect("/login")
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    """Require an admin session; inputs: route function; output: wrapped function."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect("/login")
        if session.get("role") != "admin":
            return redirect("/dashboard")
        return view(*args, **kwargs)
    return wrapped
