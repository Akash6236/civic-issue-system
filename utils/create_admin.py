"""
Local Admin Creation Utility
AI-Powered Civic Issue Reporting and Management System

This script provides a secure, local-only administrative command to create
the initial administrator account. It is NOT exposed through the public web interface.

Usage:
    Interactive mode:
        python utils/create_admin.py

    Non-interactive CLI mode:
        python utils/create_admin.py --name "Admin User" --email "admin@city.gov" --password "AdminPass123" --phone "9876543210"
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

from modules.database import get_connection, init_db
from modules.authentication.auth import (
    hash_password,
    validate_email,
    validate_password_strength,
    validate_phone,
)


def create_admin(
    full_name: str,
    email: str,
    password: str,
    confirm_password: Optional[str] = None,
    phone: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Creates an administrative user account.
    Validates credentials and securely hashes password using bcrypt.
    """
    name_clean = full_name.strip() if full_name else ""
    email_clean = email.strip() if email else ""
    phone_clean = phone.strip() if phone and phone.strip() else None

    # Required field validation
    if not name_clean:
        return False, "Full name is required."
    if not email_clean:
        return False, "Email address is required."
    if not password:
        return False, "Password is required."

    # Format checks
    if not validate_email(email_clean):
        return False, "Invalid email address format."

    if confirm_password is not None and password != confirm_password:
        return False, "Passwords do not match."

    is_strong, pwd_err = validate_password_strength(password)
    if not is_strong:
        return False, pwd_err

    phone_valid, phone_err = validate_phone(phone_clean)
    if not phone_valid:
        return False, phone_err

    # Ensure database is verified
    init_db()

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Check if email is already taken
            cursor.execute(
                "SELECT id, role FROM users WHERE email = ? COLLATE NOCASE;",
                (email_clean,),
            )
            existing = cursor.fetchone()
            if existing:
                return (
                    False,
                    f"User with email '{email_clean}' already exists (Role: {existing['role']}).",
                )

            # Hash password with bcrypt
            pwd_hash = hash_password(password)

            # Insert admin record
            cursor.execute(
                """
                INSERT INTO users (full_name, email, phone, password_hash, role, is_active)
                VALUES (?, ?, ?, ?, 'admin', 1);
                """,
                (name_clean, email_clean, phone_clean, pwd_hash),
            )
            conn.commit()

            return True, f"Admin account '{email_clean}' successfully created!"

    except sqlite3.IntegrityError:
        return False, f"An account with email '{email_clean}' already exists."
    except sqlite3.Error as err:
        return False, f"Database error while creating admin: {err}"


def interactive_cli():
    """Runs interactive terminal prompts for creating an admin account."""
    print("=" * 60)
    print("AI-Powered Civic Issue System: Create Admin Account")
    print("=" * 60)
    print("This utility runs locally to securely set up an administrative account.")
    print("Passwords are encrypted with bcrypt and never stored in plaintext.\n")

    full_name = input("Admin Full Name: ").strip()
    email = input("Admin Email: ").strip()
    phone = input("Admin Phone (optional, press Enter to skip): ").strip()

    password = getpass.getpass("Password (min 8 chars, letters & numbers): ")
    confirm_password = getpass.getpass("Confirm Password: ")

    success, message = create_admin(
        full_name=full_name,
        email=email,
        password=password,
        confirm_password=confirm_password,
        phone=phone or None,
    )

    if success:
        print(f"\n[SUCCESS] {message}")
    else:
        print(f"\n[ERROR] {message}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Securely create an administrator account for Civic Issue System."
    )
    parser.add_argument("--name", help="Admin Full Name")
    parser.add_argument("--email", help="Admin Email Address")
    parser.add_argument("--password", help="Admin Password")
    parser.add_argument("--phone", help="Admin Phone Number (Optional)")

    args = parser.parse_args()

    # If any CLI arg is provided, run in non-interactive mode
    if args.email or args.name or args.password:
        if not (args.name and args.email and args.password):
            print("[ERROR] When using CLI arguments, --name, --email, and --password are all required.")
            sys.exit(1)
        success, message = create_admin(
            full_name=args.name,
            email=args.email,
            password=args.password,
            phone=args.phone,
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

