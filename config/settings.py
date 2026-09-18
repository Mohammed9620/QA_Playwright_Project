"""
Configuration Settings Module
─────────────────────────────
Centralized runtime settings management driven by environment variables (.env).
Provides strongly typed defaults and path resolution for enterprise testing.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

# Ensure root .env is loaded
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """Immutable framework configuration holding global test and runtime parameters."""

    # Project Paths
    PROJECT_ROOT: Path = _PROJECT_ROOT
    REPORTS_DIR: Path = _PROJECT_ROOT / "reports"
    LOGS_DIR: Path = _PROJECT_ROOT / "logs"
    TEST_DATA_DIR: Path = _PROJECT_ROOT / "test_data"

    # Target Under Test & Authentication
    TARGET_URL: str = os.getenv("TARGET_URL", "https://www.saucedemo.com")
    TEST_USER: str = os.getenv("TEST_USER", "standard_user")
    TEST_PASS: str = os.getenv("TEST_PASS", "secret_sauce")

    # UI Locators (Configurable for cross-environment selector adaptation)
    USER_LOCATOR: str = os.getenv("USER_LOCATOR", "#user-name")
    PASS_LOCATOR: str = os.getenv("PASS_LOCATOR", "#password")
    LOGIN_LOCATOR: str = os.getenv("LOGIN_LOCATOR", "#login-button")

    # Playwright Execution Controls
    BROWSER: str = os.getenv("BROWSER", "chromium").lower()
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")
    DEFAULT_TIMEOUT_MS: int = int(os.getenv("TIMEOUT", "10000"))

    # API Testing Parameters
    API_EXPECTED_STATUS: int = int(os.getenv("API_EXPECTED_STATUS", "200"))
    API_SLA_MS: int = int(os.getenv("API_SLA_MS", "3000"))

    # Security Probes & Wordlists
    WORDLIST_USERS_ENV: str = os.getenv("WORDLIST_USERS", "")
    WORDLIST_PASSES_ENV: str = os.getenv("WORDLIST_PASSES", "")

    def ensure_directories(self) -> None:
        """Ensures all required output directories exist."""
        self.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

    def validate_target(self) -> None:
        """Validates that mandatory target configurations are provided."""
        if not self.TARGET_URL:
            raise EnvironmentError(
                "[ERROR] TARGET_URL is not defined in the environment or .env file."
            )


# Global singleton access
_settings_instance = None


def get_settings() -> Settings:
    """Returns the cached global Settings instance, ensuring directories are initialized."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
        _settings_instance.ensure_directories()
    return _settings_instance
