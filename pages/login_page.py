"""
Login Page Object
─────────────────
Encapsulates UI interactions, selector mappings, and verification checks
for the application login interface.
"""

from typing import Dict, Optional
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage


class LoginPage(BasePage):
    """Page object modeling the authentication portal."""

    def __init__(self, page: Page, base_url: Optional[str] = None):
        super().__init__(page, base_url)
        self.username_selector = self.settings.USER_LOCATOR
        self.password_selector = self.settings.PASS_LOCATOR
        self.login_button_selector = self.settings.LOGIN_LOCATOR
        self.error_banner_selector = "[data-test='error']"

    @property
    def username_input(self) -> Locator:
        return self.get_locator(self.username_selector)

    @property
    def password_input(self) -> Locator:
        return self.get_locator(self.password_selector)

    @property
    def login_button(self) -> Locator:
        return self.get_locator(self.login_button_selector)

    @property
    def error_banner(self) -> Locator:
        return self.get_locator(self.error_banner_selector)

    def Maps(self) -> Dict[str, Locator]:
        """Provides backwards-compatible locator dictionary."""
        return {
            "username_field": self.username_input,
            "password_field": self.password_input,
            "login_button": self.login_button,
        }

    def navigate_to_login(self) -> None:
        """Navigates to the login page."""
        self.navigate()

    def fill_username(self, username: str) -> None:
        """Fills the username field."""
        self.fill(self.username_selector, username)
        self.logger.info(f"Entered username: {username}")

    def fill_password(self, password: str) -> None:
        """Fills the password field and logs masked output."""
        self.fill(self.password_selector, password, mask_log=True)
        self.logger.info(f"Entered password: {'*' * len(password)}")

    def click_login(self) -> None:
        """Clicks the login submit button."""
        self.click(self.login_button_selector)
        self.logger.info("Clicked the Login button.")

    def login(self, username: str, password: str) -> None:
        """Performs a full credential submission sequence."""
        self.fill_username(username)
        self.fill_password(password)
        self.click_login()

    def attempt_login(self, username: str, password: str) -> None:
        """Fast credential submission for probing without verbose field logging."""
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    def is_login_successful(self) -> bool:
        """Checks if navigation reached the authenticated inventory landing page."""
        return "/inventory.html" in self.current_url

    def get_error_message(self) -> str:
        """Extracts the displayed validation/auth error message."""
        return self.get_text(self.error_banner_selector)

    def is_error_banner_visible(self) -> bool:
        """Returns True if the authentication error alert is rendered."""
        return self.is_visible(self.error_banner_selector)

    def reset_state(self) -> None:
        """Re-navigates to the base login page to clear form state."""
        self.navigate()
