"""Authentication routes."""

from flask import Blueprint, flash, request, session

from aquasense.db_helper import execute_query, fetch_one
from flask import render_template
from aquasense.utils.decorators import login_required

auth_bp = Blueprint("auth", __name__)

try:
    import bcrypt
except ImportError:
    bcrypt = None
    from werkzeug.security import check_password_hash, generate_password_hash


def _hash_password(password):
    """Hash a password using bcrypt when available; inputs: plaintext; output: hash string."""
    if bcrypt:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return generate_password_hash(password)


def _check_password(password, password_hash):
    """Verify a password; inputs: plaintext and stored hash; output: boolean."""
    if bcrypt:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    return check_password_hash(password_hash, password)


@auth_bp.post("/register")
def register():
    """Register a new user; inputs: form/json fields; output: redirect dict."""
    data = request.get_json(silent=True) or request.form
    try:
        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        city = data.get("city", "").strip()
        tariff_rate = float(data.get("tariff_rate", 0.05))
        threshold = float(data.get("threshold", 200.0))
        if not name or not email or not password or tariff_rate < 0 or threshold <= 0:
            return {"error": "Name, email, password, positive threshold, and valid tariff rate are required."}, 400
        execute_query(
            "INSERT INTO users (name, email, password_hash, city, tariff_rate, threshold) VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, _hash_password(password), city, tariff_rate, threshold),
        )
        flash("Registration successful. Please log in.", "success")
        return {"message": "Registration successful.", "redirect": "/login"}
    except Exception as exc:
        return {"error": f"Registration failed: {exc}"}, 400


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate a user; inputs: email and password; output: redirect dict."""
    if request.method == "GET":
        return render_template("auth/login.html")
    
    data = request.get_json(silent=True) or request.form
    data = request.form
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    if not email or not password:
        return {"error": "Email and password are required."}, 400
    user = fetch_one("SELECT * FROM users WHERE email = ?", (email,))
    if not user or not _check_password(password, user["password_hash"]):
        return {"error": "Invalid email or password."}, 401
    session["user_id"] = user["id"]
    session["role"] = user["role"]
    flash("Login successful.", "success")
    return {"message": "Login successful.", "redirect": "/dashboard"}


@auth_bp.get("/logout")
def logout():
    """Clear the current session; inputs: session; output: redirect dict."""
    session.clear()
    flash("Logged out successfully.", "success")
    return {"message": "Logged out successfully.", "redirect": "/login"}
