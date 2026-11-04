"""
Database Connection and Utility Module
AI-Powered Civic Issue Reporting and Management System
"""

import sqlite3
from pathlib import Path
from typing import Optional

# Determine project root directory reliably regardless of working directory
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "civic_streamlit.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"

REQUIRED_TABLES = [
    "users",
    "complaints",
    "complaint_history",
    "resolution",
    "duplicate_matches",
    "admin_actions",
]


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Creates and returns a connection to the SQLite database.

    Features:
    - Uses reliable project-relative path.
    - Enforces foreign key constraints (PRAGMA foreign_keys = ON).
    - Configures sqlite3.Row as row_factory for name-based column access.
    - Handles and surfaces database connection errors.
    """
    target_path = db_path or DB_PATH
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(target_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as err:
        raise RuntimeError(f"Database connection error to '{target_path}': {err}") from err


def init_db(db_path: Optional[Path] = None, schema_file: Optional[Path] = None) -> bool:
    """
    Initializes or verifies the database schema without deleting existing records.

    - Uses CREATE TABLE IF NOT EXISTS from schema.sql.
    - Verifies that all 6 required tables are present.
    - Checks foreign key integrity using PRAGMA foreign_key_check.
    - Runs safe migrations for new columns.
    """
    target_db = db_path or DB_PATH
    target_schema = schema_file or SCHEMA_PATH

    try:
        with get_connection(target_db) as conn:
            cursor = conn.cursor()

            # Execute schema safely if file exists
            if target_schema.exists():
                schema_sql = target_schema.read_text(encoding="utf-8")
                cursor.executescript(schema_sql)
                conn.commit()

            # Run safe migrations
            _run_migrations(cursor)
            conn.commit()

            # Verify presence of all expected tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
            )
            existing_tables = {row["name"] for row in cursor.fetchall()}
            missing = [table for table in REQUIRED_TABLES if table not in existing_tables]

            if missing:
                raise RuntimeError(f"Database verification failed. Missing tables: {missing}")

            # Check referential integrity
            cursor.execute("PRAGMA foreign_key_check;")
            violations = cursor.fetchall()
            if violations:
                raise RuntimeError(f"Foreign key integrity check failed: {violations}")

            return True
    except sqlite3.Error as err:
        raise RuntimeError(f"Database initialization error: {err}") from err


def _run_migrations(cursor: sqlite3.Cursor) -> None:
    """
    Runs safe, idempotent database migrations.

    Adds new columns only if they don't already exist, preserving all existing data.
    """
    # Check if is_withdrawn column exists in complaints table
    cursor.execute("PRAGMA table_info(complaints);")
    complaint_columns = {row["name"] for row in cursor.fetchall()}

    if "is_withdrawn" not in complaint_columns:
        cursor.execute(
            "ALTER TABLE complaints ADD COLUMN is_withdrawn INTEGER NOT NULL DEFAULT 0;"
        )

    if "withdrawal_reason" not in complaint_columns:
        cursor.execute(
            "ALTER TABLE complaints ADD COLUMN withdrawal_reason TEXT;"
        )

    if "is_archived" not in complaint_columns:
        cursor.execute(
            "ALTER TABLE complaints ADD COLUMN is_archived INTEGER NOT NULL DEFAULT 0;"
        )

    if "archive_reason" not in complaint_columns:
        cursor.execute(
            "ALTER TABLE complaints ADD COLUMN archive_reason TEXT;"
        )

    # Create performance indexes
    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_complaints_user_id ON complaints(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);",
        "CREATE INDEX IF NOT EXISTS idx_complaints_category ON complaints(category);",
        "CREATE INDEX IF NOT EXISTS idx_complaints_created_at ON complaints(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_complaints_is_archived ON complaints(is_archived);",
        "CREATE INDEX IF NOT EXISTS idx_complaints_is_withdrawn ON complaints(is_withdrawn);",
        "CREATE INDEX IF NOT EXISTS idx_complaint_history_complaint_id ON complaint_history(complaint_id);",
        "CREATE INDEX IF NOT EXISTS idx_admin_actions_admin_id ON admin_actions(admin_id);",
        "CREATE INDEX IF NOT EXISTS idx_admin_actions_complaint_id ON admin_actions(complaint_id);",
        "CREATE INDEX IF NOT EXISTS idx_duplicate_matches_status ON duplicate_matches(status);",
        "CREATE INDEX IF NOT EXISTS idx_duplicate_matches_orig ON duplicate_matches(original_complaint_id);",
        "CREATE INDEX IF NOT EXISTS idx_duplicate_matches_dup ON duplicate_matches(duplicate_complaint_id);",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",
    ]
    for stmt in index_statements:
        cursor.execute(stmt)


if __name__ == "__main__":
    try:
        if init_db():
            print(f"Database successfully connected and verified at: {DB_PATH}")
    except Exception as error:
        print(f"Database verification failed: {error}")

