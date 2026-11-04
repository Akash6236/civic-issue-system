"""
Authentication Module
AI-Powered Civic Issue Reporting and Management System

Handles citizen registration, login authentication, password hashing with bcrypt,
and Streamlit session state management.
"""

import re
import sqlite3
from typing import Any, Dict, Optional, Tuple

import bcrypt
import streamlit as st

from modules.database import get_connection

# Session State Keys
SESSION_USER_KEY = "current_user"
SESSION_AUTH_KEY = "is_authenticated"

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
PHONE_REGEX = r"^\+?[0-9\s\-()]{7,15}$"


def hash_password(plain_password: str) -> str:
    """
    Hashes a plaintext password using bcrypt with a generated salt.
    Never stores or returns plaintext passwords.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a stored bcrypt hash.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def validate_email(email: str) -> bool:
    """
    Validates email format using a standard regular expression.
    """
    if not email:
        return False
    return bool(re.match(EMAIL_REGEX, email.strip()))


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validates that password meets minimum security criteria:
    - At least 8 characters long
    - Contains at least one letter
    - Contains at least one digit
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    return True, ""


def validate_phone(phone: Optional[str]) -> Tuple[bool, str]:
    """
    Validates optional phone number format.
    Allows empty string or None.
    """
    if not phone or not phone.strip():
        return True, ""
    cleaned = phone.strip()
    if not re.match(PHONE_REGEX, cleaned):
        return False, "Phone number format is invalid (must be 7-15 digits, e.g., 9876543210)."
    return True, ""


def register_citizen(
    full_name: str,
    email: str,
    phone: Optional[str],
    password: str,
    confirm_password: str,
) -> Tuple[bool, str, Optional[int]]:
    """
    Registers a new citizen user.

    Security & Validation:
    - Verifies all required fields are present.
    - Validates email format and password strength.
    - Confirms password matches confirmation.
    - Checks for duplicate emails (case-insensitive).
    - Enforces role='citizen' (public admin registration is strictly prohibited).
    - Stores only the bcrypt password hash.
    - Uses parameterized SQL transactions.

    Returns:
        (success: bool, message: str, user_id: Optional[int])
    """
    # 1. Input sanitization
    full_name_clean = full_name.strip() if full_name else ""
    email_clean = email.strip() if email else ""
    phone_clean = phone.strip() if phone and phone.strip() else None

    # 2. Required field validation
    if not full_name_clean:
        return False, "Full name is required.", None
    if not email_clean:
        return False, "Email address is required.", None
    if not password:
        return False, "Password is required.", None
    if not confirm_password:
        return False, "Password confirmation is required.", None

    # 3. Format validation
    if not validate_email(email_clean):
        return False, "Please provide a valid email address.", None

    phone_valid, phone_msg = validate_phone(phone_clean)
    if not phone_valid:
        return False, phone_msg, None

    # 4. Password validation
    if password != confirm_password:
        return False, "Passwords do not match.", None

    is_strong, pwd_msg = validate_password_strength(password)
    if not is_strong:
        return False, pwd_msg, None

    # 5. Database operations
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Prevent duplicate email registrations (case-insensitive)
            cursor.execute(
                "SELECT id FROM users WHERE email = ? COLLATE NOCASE;",
                (email_clean,),
            )
            if cursor.fetchone():
                return False, "An account with this email address already exists.", None

            # Generate bcrypt hash
            pwd_hash = hash_password(password)

            # Insert citizen record (role is strictly 'citizen')
            cursor.execute(
                """
                INSERT INTO users (full_name, email, phone, password_hash, role, is_active)
                VALUES (?, ?, ?, ?, 'citizen', 1);
                """,
                (full_name_clean, email_clean, phone_clean, pwd_hash),
            )
            user_id = cursor.lastrowid
            conn.commit()

            return True, "Registration successful! You can now log in.", user_id

    except sqlite3.IntegrityError:
        return False, "An account with this email address already exists.", None
    except sqlite3.Error as err:
        return False, f"Database error during registration: {err}", None


def authenticate_user(
    email: str,
    password: str,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Authenticates a user (citizen or admin) by email and password.

    Validation:
    - Matches email case-insensitively using parameterized query.
    - Checks account active status (is_active == 1).
    - Verifies password against bcrypt hash.
    - Strips password_hash before returning user data.

    Returns:
        (success: bool, message: str, user_dict: Optional[Dict[str, Any]])
    """
    email_clean = email.strip() if email else ""
    if not email_clean or not password:
        return False, "Email and password are required.", None

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, full_name, email, phone, password_hash, role, is_active, created_at
                FROM users
                WHERE email = ? COLLATE NOCASE;
                """,
                (email_clean,),
            )
            user_row = cursor.fetchone()

            if not user_row:
                # Generic message to avoid email enumeration
                return False, "Invalid email or password.", None

            # Check if account is active
            if not user_row["is_active"]:
                return False, "This account is disabled. Please contact the administrator.", None

            # Verify password hash
            if not verify_password(password, user_row["password_hash"]):
                return False, "Invalid email or password.", None

            # Build safe user dictionary without password hash
            user_data = {
                "id": user_row["id"],
                "full_name": user_row["full_name"],
                "email": user_row["email"],
                "phone": user_row["phone"],
                "role": user_row["role"],
                "created_at": user_row["created_at"],
            }

            return True, "Login successful.", user_data

    except sqlite3.Error as err:
        return False, f"Database error during authentication: {err}", None


# --- Streamlit Session State Management ---

def login_user(user_data: Dict[str, Any]) -> None:
    """
    Stores authenticated user data into Streamlit's session state.
    Explicitly ensures sensitive fields like password hashes are excluded.
    """
    safe_profile = {
        key: value for key, value in user_data.items() if key != "password_hash"
    }
    st.session_state[SESSION_USER_KEY] = safe_profile
    st.session_state[SESSION_AUTH_KEY] = True


def logout_user() -> None:
    """
    Logs out the current user by clearing session state.
    """
    st.session_state[SESSION_USER_KEY] = None
    st.session_state[SESSION_AUTH_KEY] = False


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Returns the currently logged-in user dictionary, or None if not logged in.
    """
    return st.session_state.get(SESSION_USER_KEY)


def is_authenticated() -> bool:
    """
    Returns True if a user is currently authenticated in session state.
    """
    return bool(st.session_state.get(SESSION_AUTH_KEY) and st.session_state.get(SESSION_USER_KEY))


def is_admin() -> bool:
    """
    Returns True if the current user is authenticated and has the 'admin' role.
    """
    user = get_current_user()
    return bool(is_authenticated() and user and user.get("role") == "admin")


def is_citizen() -> bool:
    """
    Returns True if the current user is authenticated and has the 'citizen' role.
    """
    user = get_current_user()
    return bool(is_authenticated() and user and user.get("role") == "citizen")

