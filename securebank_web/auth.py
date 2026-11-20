import hashlib
import secrets
from functools import wraps
from flask import session, redirect, url_for, flash

CURRENCY = "₹"


def hash_password(password: str, salt: str = None):
    """
    Hashes password using PBKDF2-HMAC-SHA256 with 200,000 iterations.
    Matches the exact algorithm used in the Tkinter desktop application.
    """
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 200_000
    ).hex()
    return salt, digest


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Safely verifies the password using constant-time comparison."""
    _, actual_hash = hash_password(password, salt)
    return secrets.compare_digest(actual_hash, expected_hash)


def money(amount) -> str:
    """Formats a float as currency (e.g. ₹1,234.56)."""
    try:
        val = float(amount)
        return f"{CURRENCY}{val:,.2f}"
    except (ValueError, TypeError):
        return f"{CURRENCY}0.00"


def login_required(f):
    """Decorator ensuring that a route can only be accessed by authenticated users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def validate_registration(name: str, username: str, password: str, confirm: str):
    """Validates registration input fields."""
    if not name or not username or not password or not confirm:
        return False, "Please fill in all fields."
    if len(name.strip()) < 2:
        return False, "Full name must be at least 2 characters."
    if len(username.strip()) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must contain at least 6 characters."
    if password != confirm:
        return False, "Password and confirm password do not match."
    return True, ""


def validate_password_change(current_pass: str, new_pass: str, confirm_pass: str):
    """Validates password change fields."""
    if not current_pass or not new_pass or not confirm_pass:
        return False, "Please fill in all password fields."
    if len(new_pass) < 8:
        return False, "New password must contain at least 8 characters."
    if new_pass != confirm_pass:
        return False, "New password and confirm password do not match."
    return True, ""


def validate_amount(amount_str: str):
    """Validates banking transaction amounts."""
    if not amount_str:
        return None, "Please enter an amount."
    try:
        amount = round(float(amount_str.strip()), 2)
        if amount <= 0:
            return None, "Amount must be greater than zero."
        return amount, ""
    except ValueError:
        return None, "Please enter a valid numeric amount."
