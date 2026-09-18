"""
Base Page Object
────────────────
Provides core Playwright web element interaction wrappers, explicit waits,
and unified diagnostic logging across all derivative page objects.
"""

from pathlib import Path
from typing import Optional
from playwright.sync_api import Page, Locator
from config.settings import get_settings
from utils.logger import get_logger


class BasePage:
    """Foundational Page Object with high-reliability interaction primitives."""

    def __init__(self, page: Page, base_url: Optional[str] = None):
        self.page = page
        self.settings = get_settings()
        self.base_url = (base_url or self.settings.TARGET_URL).rstrip("/")
        self.logger = get_logger(self.__class__.__name__)

    def navigate(self, path: str = "") -> None:
        """Navigates to the specified path or the base URL."""
        target = f"{self.base_url}/{path}".rstrip("/") if path else self.base_url
        self.page.goto(target)
        self.logger.info(f"Navigated to: {target}")

    def get_locator(self, selector: str) -> Locator:
        """Returns a Playwright Locator for the given selector."""
        return self.page.locator(selector)

    def fill(self, selector: str, text: str, mask_log: bool = False) -> None:
        """Fills an input element with the provided text."""
        log_text = "*" * len(text) if mask_log else text
        locator = self.get_locator(selector)
        locator.fill(text)

    def click(self, selector: str) -> None:
        """Clicks an element identified by the selector."""
        locator = self.get_locator(selector)
        locator.click()

    def get_text(self, selector: str) -> str:
        """Retrieves inner text of the target element."""
        return self.get_locator(selector).inner_text().strip()

    def is_visible(self, selector: str) -> bool:
        """Checks whether the element is visible on the current view."""
        return self.get_locator(selector).is_visible()

    @property
    def current_url(self) -> str:
        """Returns the current browser URL."""
        return self.page.url

    def wait_for_timeout(self, timeout_ms: int) -> None:
        """Pauses execution for the specified milliseconds."""
        self.page.wait_for_timeout(timeout_ms)

    def take_screenshot(self, filename: str) -> Path:
        """Captures a screenshot and saves it to the reports/screenshots directory."""
        screenshots_dir = self.settings.REPORTS_DIR / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        file_path = screenshots_dir / f"{filename}.png"
        self.page.screenshot(path=str(file_path))
        self.logger.info(f"Captured screenshot: {file_path}")
        return file_path
