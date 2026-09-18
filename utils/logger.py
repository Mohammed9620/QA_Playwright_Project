"""
Structured Logging Utility
──────────────────────────
Provides standardized logging across test suites, page objects, and HTTP clients.
Writes simultaneously to console (stdout) and persistent rotating log files,
while preserving milestone tags ([INFO], [PASS], [WARN], [FAIL], [ERROR])
required for real-time SSE stream parsing and dashboard visualization.
"""

import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config.settings import get_settings


class TestLogger:
    """Enterprise wrapper around Python's standard logging library."""

    def __init__(self, name: str = "QA_Engine"):
        self.settings = get_settings()
        self.settings.ensure_directories()
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.INFO)

        # Prevent duplicate handlers if re-instantiated
        if not self._logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self) -> None:
        # Formatter for console: preserves the exact prefix for real-time SSE parsing
        console_formatter = logging.Formatter("%(message)s")
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)

        # Formatter for persistent file: includes full ISO timestamp and level
        log_file_path = self.settings.LOGS_DIR / "automation.log"
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        self._logger.addHandler(file_handler)

    def info(self, msg: str) -> None:
        """Logs general milestone or execution state."""
        self._logger.info(f"[INFO] {msg}")

    def pass_step(self, msg: str) -> None:
        """Logs a successful milestone or passing assertion."""
        self._logger.info(f"[PASS] {msg}")

    def warn(self, msg: str) -> None:
        """Logs a warning or security anomaly."""
        self._logger.warning(f"[WARN] {msg}")

    def fail(self, msg: str) -> None:
        """Logs an assertion failure or test defect."""
        self._logger.error(f"[FAIL] {msg}")

    def error(self, msg: str) -> None:
        """Logs an unhandled system or network error."""
        self._logger.error(f"[ERROR] {msg}")

    def debug(self, msg: str) -> None:
        """Logs debug details to log file."""
        self._logger.debug(msg)


# Module-level singleton helper
def get_logger(name: str = "QA_Engine") -> TestLogger:
    """Factory function to retrieve a configured TestLogger instance."""
    return TestLogger(name)
