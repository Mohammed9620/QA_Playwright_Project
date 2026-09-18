"""
Database Initialization Module
──────────────────────────────
Initializes the SQLite schema for user role management and OTP authentication.
Credentials and configuration are pulled securely from environment variables.

Usage:
    python init_db.py
"""

import os
import sqlite3
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

DB_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(__file__), "users.db")
)

# Admin seed configuration sourced securely from environment variables
DEFAULT_EMAIL = os.environ.get("ADMIN_DEFAULT_EMAIL", "admin@test.com")
DEFAULT_USERNAME = os.environ.get("ADMIN_DEFAULT_USERNAME", "admin")
DEFAULT_PASSWORD = os.environ.get("ADMIN_DEFAULT_PASSWORD", "AdminPassword123!Secure")
DEFAULT_ROLE = os.environ.get("ADMIN_DEFAULT_ROLE", "admin")


def init_db() -> None:
    """Creates the necessary database tables and seeds the initial administrator account."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Drop existing tables to refresh schema cleanly
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS otp_store")

    # Create users table
    cursor.execute("""
        CREATE TABLE users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            email    TEXT    UNIQUE NOT NULL,
            username TEXT    UNIQUE NOT NULL,
            password TEXT    NOT NULL,
            role     TEXT    NOT NULL
        )
    """)

    # Create otp_store table
    cursor.execute("""
        CREATE TABLE otp_store (
            email      TEXT PRIMARY KEY,
            otp_code   TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Insert initial administrator user
    cursor.execute(
        "INSERT INTO users (email, username, password, role) VALUES (?, ?, ?, ?)",
        (DEFAULT_EMAIL, DEFAULT_USERNAME, DEFAULT_PASSWORD, DEFAULT_ROLE),
    )

    conn.commit()
    conn.close()

    print(f"[INFO] Database initialized at: {DB_PATH}")
    print(f"[INFO] Default administrator account seeded: '{DEFAULT_USERNAME}' <{DEFAULT_EMAIL}>")


if __name__ == "__main__":
    init_db()
