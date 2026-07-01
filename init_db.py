"""
init_db.py
──────────
Run this script once to bootstrap the SQLite authentication database.

Usage:
    python init_db.py

What it does:
  1. Creates (or opens) users.db in the project root.
  2. Creates the `users` table if it does not already exist.
  3. Inserts a default admin user for first-run testing.
     If the admin user already exists the insert is silently skipped
     (INSERT OR IGNORE), so it is safe to re-run this script at any time.
"""

import sqlite3
import os

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

# ── Default seed user (for local testing only — change before any deployment) ─
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "password123"   # Plain text for now; Phase 2 will hash this.

# ── Bootstrap ─────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create the users table (no-op if it already exists)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    UNIQUE NOT NULL,
            password TEXT    NOT NULL
        )
    """)

    # Insert default admin — silently skip if username already taken
    cursor.execute(
        "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
        (DEFAULT_USERNAME, DEFAULT_PASSWORD),
    )

    conn.commit()
    conn.close()

    print("[init_db] Database ready at: " + DB_PATH)
    print("[init_db] Default user      : " + DEFAULT_USERNAME)
    print("[init_db] NOTE: Store hashed passwords before going to production.")


if __name__ == "__main__":
    init_db()
