"""
Admin Account Reset Utility
AI-Powered Civic Issue Reporting and Management System

Safely resets an existing administrator account's email and/or password.
Preserves all citizen accounts, complaints, images, complaint history,
and audit logs. Does NOT create duplicate accounts — updates the
existing admin record in place.

Usage:
    Interactive mode:
        python utils/reset_admin.py

    Non-interactive CLI mode:
        python utils/reset_admin.py --email "admin@city.gov" --password "NewPass123"
"""

import argparse
import getpass
import sqlite3
import sys
from pathlib import Path
from typing import Optional, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.authentication.auth import hash_password, validate_email, validate_password_strength
from modules.database import get_connection, init_db


def reset_admin(
    email: str,
    password: str,
    confirm_password: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Resets an existing administrator account's email and/or password.

    Finds an existing admin account (role='admin') and updates its
    email and password_hash in place. If no admin account exists,
    creates one. Never creates duplicates.

    All citizen accounts, complaints, images, complaint history,
    and audit logs are preserved untouched.

    Args:
        email: New admin email address.
        password: New admin password.
        confirm_password: Password confirmation (required if provided).

    Returns:
        (success: bool, message: str)
    """
    # 1. Input sanitization
    email_clean = email.strip() if email else ""
    password_clean = password.strip() if password else ""

    # 2. Required field validation
    if not email_clean:
        return False, "Email address is required."
    if not password_clean:
        return False, "Password is required."

    # 3. Format validation
    if not validate_email(email_clean):
        return False, "Invalid email address format."

    if confirm_password is not None and password_clean != confirm_password:
        return False, "Passwords do not match."

    is_strong, pwd_err = validate_password_strength(password_clean)
    if not is_strong:
        return False, pwd_err

    # 4. Ensure database is verified (runs safe migrations)
    init_db()

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Check if the requested email is already taken by a NON-admin account.
            # Admin email changes must not collide with existing citizen emails.
            cursor.execute(
                """
                SELECT id, role FROM users WHERE email = ? COLLATE NOCASE;
                """,
                (email_clean,),
            )
            existing_email_row = cursor.fetchone()
            if existing_email_row and existing_email_row["role"] != "admin":
                return (
                    False,
                    f"Email '{email_clean}' is already used by a citizen account.",
                )

            # Find an existing admin account to update in place.
            cursor.execute(
                """
                SELECT id, email FROM users WHERE role = 'admin'
                ORDER BY id ASC LIMIT 1;
                """,
            )
            admin_row = cursor.fetchone()

            # Generate bcrypt hash using the same implementation as auth.py
            pwd_hash = hash_password(password_clean)

            if admin_row:
                # UPDATE the existing admin account in place (no duplicate).
                cursor.execute(
                    """
                    UPDATE users
                    SET email = ?,
                        password_hash = ?,
                        is_active = 1,
                        full_name = COALESCE(NULLIF(full_name, ''), 'Administrator')
                    WHERE id = ? AND role = 'admin';
                    """,
                    (email_clean, pwd_hash, admin_row["id"]),
                )
                conn.commit()
                return (
                    True,
                    f"Admin account updated successfully (email: {email_clean}).",
                )
            else:
                # No admin account exists — create one (should not happen normally).
                cursor.execute(
                    """
                    INSERT INTO users (full_name, email, phone, password_hash, role, is_active)
                    VALUES (?, ?, NULL, ?, 'admin', 1);
                    """,
                    ("Administrator", email_clean, pwd_hash),
                )
                conn.commit()
                return (
                    True,
                    f"No existing admin found. Created new admin account (email: {email_clean}).",
                )

    except sqlite3.IntegrityError:
        return False, f"An account with email '{email_clean}' already exists."
    except sqlite3.Error as err:
        return False, f"Database error while resetting admin: {err}"


def interactive_cli():
    """Runs interactive terminal prompts for resetting the admin account."""
    print("=" * 60)
    print("AI-Powered Civic Issue System: Reset Admin Account")
    print("=" * 60)
    print("This utility resets an existing administrator account in place.")
    print("All citizen accounts, complaints, and audit logs are preserved.")
    print("Passwords are encrypted with bcrypt and never stored in plaintext.\n")

    email = input("Admin Email: ").strip()

    password = getpass.getpass("New Password (min 8 chars, letters & numbers): ")
    confirm_password = getpass.getpass("Confirm New Password: ")

    success, message = reset_admin(
        email=email,
        password=password,
        confirm_password=confirm_password,
    )

    if success:
        print(f"\n[SUCCESS] {message}")
    else:
        print(f"\n[ERROR] {message}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Securely reset an administrator account (email + password)."
    )
    parser.add_argument("--email", help="Admin Email Address")
    parser.add_argument("--password", help="Admin Password")

    args = parser.parse_args()

    # If any CLI arg is provided, run in non-interactive mode
    if args.email or args.password:
        if not (args.email and args.password):
            print(
                "[ERROR] When using CLI arguments, --email and --password are both required."
            )
            sys.exit(1)
        success, message = reset_admin(
            email=args.email,
            password=args.password,
        )
        if success:
            print(f"[SUCCESS] {message}")
        else:
            print(f"[ERROR] {message}")
            sys.exit(1)
    else:
        interactive_cli()


if __name__ == "__main__":
    main()
