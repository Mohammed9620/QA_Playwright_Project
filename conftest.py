"""
Pytest Global Configuration & Test Fixtures
───────────────────────────────────────────
Provides dependency injection fixtures for Playwright browser lifecycles,
API clients, Page Objects, reporting hooks, and failure artifact captures.
"""

import sys
import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from config.settings import get_settings, Settings
from core.browser_factory import BrowserFactory
from pages.login_page import LoginPage
from pages.auth_security_page import AuthSecurityPage
from utils.api_client import APIClient
from utils.logger import get_logger

logger = get_logger("Conftest")


# ──────────────────────────────────────────────
#  Pytest Report Customization Hooks
# ──────────────────────────────────────────────
def pytest_html_report_title(report):
    """Overrides the default pytest-html report title."""
    report.title = "QA Automation Engine — Test Report"


def pytest_configure(config):
    """Registers metadata and ensures output directories exist."""
    settings = get_settings()
    settings.ensure_directories()

    # Add custom metadata to HTML report if available
    if hasattr(config, "_metadata"):
        config._metadata["Project"] = "Enterprise QA Playwright Framework"
        config._metadata["Target URL"] = settings.TARGET_URL
        config._metadata["Browser"] = settings.BROWSER
        config._metadata["Headless"] = str(settings.HEADLESS)


# ──────────────────────────────────────────────
#  Core Fixtures
# ──────────────────────────────────────────────
@pytest.fixture(scope="session")
def settings() -> Settings:
    """Provides application configuration settings."""
    cfg = get_settings()
    cfg.validate_target()
    return cfg


@pytest.fixture(scope="function")
def browser_context_page(settings: Settings):
    """Provides a fresh isolated Browser, BrowserContext, and Page per test with clean teardown."""
    factory = BrowserFactory(settings)
    with factory.session() as (browser, context, page):
        yield browser, context, page


@pytest.fixture(scope="function")
def page(browser_context_page) -> Page:
    """Provides an isolated Playwright Page instance for UI testing."""
    _, _, page_obj = browser_context_page
    return page_obj


@pytest.fixture(scope="function")
def context(browser_context_page) -> BrowserContext:
    """Provides the active BrowserContext for cookie and session testing."""
    _, ctx, _ = browser_context_page
    return ctx


@pytest.fixture(scope="function")
def login_page(page: Page, settings: Settings) -> LoginPage:
    """Provides an initialized LoginPage object."""
    return LoginPage(page, base_url=settings.TARGET_URL)


@pytest.fixture(scope="function")
def auth_security_page(page: Page, context: BrowserContext, settings: Settings) -> AuthSecurityPage:
    """Provides an initialized AuthSecurityPage object."""
    return AuthSecurityPage(page, context, base_url=settings.TARGET_URL)


@pytest.fixture(scope="function")
def api_client(settings: Settings) -> APIClient:
    """Provides an initialized APIClient object with automatic session closure."""
    client = APIClient(
        base_url=settings.TARGET_URL,
        expected_status=settings.API_EXPECTED_STATUS,
        sla_ms=settings.API_SLA_MS
    )
    yield client
    client.close()
