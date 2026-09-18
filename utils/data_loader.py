"""
Data Loader Utility
───────────────────
Provides utility functions to load external test datasets (JSON, CSV)
and resolve environment-level overrides for data-driven testing.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from config.settings import get_settings


def load_json(file_name: str) -> dict:
    """Loads and parses a JSON file located in the test_data directory."""
    settings = get_settings()
    file_path = settings.TEST_DATA_DIR / file_name
    if not file_path.exists():
        raise FileNotFoundError(f"Test data file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_credential_wordlists() -> Tuple[List[str], List[str]]:
    """
    Retrieves username and password probe wordlists.
    Prioritizes comma-separated environment overrides if present;
    otherwise loads from test_data/credentials_wordlist.json.
    """
    import os
    env_users = os.getenv("WORDLIST_USERS", "").strip()
    env_passes = os.getenv("WORDLIST_PASSES", "").strip()

    if env_users and env_passes:
        users = [u.strip() for u in env_users.split(",") if u.strip()]
        passes = [p.strip() for p in env_passes.split(",") if p.strip()]
        return users, passes

    data = load_json("credentials_wordlist.json")
    users = [u.strip() for u in env_users.split(",") if u.strip()] if env_users else data.get("users", [])
    passes = [p.strip() for p in env_passes.split(",") if u.strip()] if env_passes else data.get("passwords", [])

    return users, passes
