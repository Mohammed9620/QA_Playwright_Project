"""Page Object Model (POM) package encapsulating UI locators and user interactions."""

from pages.base_page import BasePage
from pages.login_page import LoginPage
from pages.auth_security_page import AuthSecurityPage

__all__ = ["BasePage", "LoginPage", "AuthSecurityPage"]
