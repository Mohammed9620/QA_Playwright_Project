"""
Auth Security Page Object
─────────────────────────
Encapsulates session, cookie, and authorization state inspection
to detect security regressions, token leakages, and broken access controls.
"""

from typing import Any, Dict, List, Optional
from playwright.sync_api import Page, BrowserContext
from pages.login_page import LoginPage


class AuthSecurityPage(LoginPage):
    """Specialized Page Object for session integrity and penetration probing."""

    def __init__(
        self,
        page: Page,
        context: BrowserContext,
        base_url: Optional[str] = None
    ):
        super().__init__(page, base_url)
        self.context = context

    def get_cookies(self) -> List[Dict[str, Any]]:
        """Returns all browser cookies within the current browser context."""
        return self.context.cookies()

    def get_session_storage_keys(self) -> List[str]:
        """Returns all keys stored in the active DOM sessionStorage."""
        return self.page.evaluate("() => Object.keys(sessionStorage)")

    def get_local_storage_keys(self) -> List[str]:
        """Returns all keys stored in the active DOM localStorage."""
        return self.page.evaluate("() => Object.keys(localStorage)")

    def logout(self, logout_path: str = "index.html") -> None:
        """Navigates to the designated logout endpoint or reset route."""
        target = f"{self.base_url}/{logout_path.lstrip('/')}"
        self.page.goto(target)
        self.logger.info("Triggered logout / session reset via navigation.")

    def is_protected_page_accessible(self, protected_path: str = "inventory.html") -> bool:
        """Attempts to access a restricted route without re-authenticating."""
        target = f"{self.base_url}/{protected_path.lstrip('/')}"
        self.page.goto(target)
        self.page.wait_for_timeout(1000)
        return f"/{protected_path.lstrip('/')}" in self.current_url
