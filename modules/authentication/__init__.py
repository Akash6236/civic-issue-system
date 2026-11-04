"""
Authentication Package
AI-Powered Civic Issue Reporting and Management System
"""

from modules.authentication.auth import (
    authenticate_user,
    get_current_user,
    hash_password,
    is_admin,
    is_authenticated,
    is_citizen,
    login_user,
    logout_user,
    register_citizen,
    validate_email,
    validate_password_strength,
    verify_password,
)

__all__ = [
    "hash_password",
    "verify_password",
    "validate_email",
    "validate_password_strength",
    "register_citizen",
    "authenticate_user",
    "login_user",
    "logout_user",
    "get_current_user",
    "is_authenticated",
    "is_admin",
    "is_citizen",
]

