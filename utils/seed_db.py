"""
Seed the database with the default administrator account.
Run this once after cloning the project: python utils/seed_db.py

This creates the shared admin account so every teammate starts with the same
credentials, without committing the binary SQLite database file to git.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.database import init_db
from modules.authentication.auth import create_admin_account


def main():
    # Ensure tables exist
    init_db()
    print("Database tables verified.")

    # Create the shared admin account if it doesn't exist yet
    success, msg, user_id = create_admin_account(
        full_name="Rudraksh",
        email="1nt25mc103691.akash@nmit.ac.in",
        password="Rudraksh@nmit2026",
        confirm_password="Rudraksh@nmit2026",
        setup_code="nmit2026",
    )
    if success:
        print(f"Admin account created: Rudraksh (ID: {user_id})")
    elif "already exists" in msg:
        print("Admin account already exists.")
    else:
        print(f"Seed warning: {msg}")


if __name__ == "__main__":
    main()
