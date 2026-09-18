"""
Browser Factory Module
──────────────────────
Manages Playwright browser lifecycles, contexts, and page instances
with standard timeouts, multi-browser engine support, and clean teardowns.
"""

from contextlib import contextmanager
from typing import Generator, Tuple
from playwright.sync_api import Playwright, Browser, BrowserContext, Page, sync_playwright
from config.settings import Settings, get_settings


class BrowserFactory:
    """Factory responsible for instantiating and configuring Playwright browser instances."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def launch_browser(self, playwright: Playwright) -> Browser:
        """Launches the browser engine specified in configuration."""
        browser_type = self.settings.BROWSER.lower()
        headless = self.settings.HEADLESS

        if browser_type == "firefox":
            return playwright.firefox.launch(headless=headless)
        elif browser_type == "webkit":
            return playwright.webkit.launch(headless=headless)
        else:
            # Default to Chromium
            return playwright.chromium.launch(
                headless=headless,
                args=["--disable-dev-shm-usage", "--no-sandbox"]
            )

    def create_context(self, browser: Browser, **context_kwargs) -> BrowserContext:
        """Creates an isolated browser context with standard viewport and options."""
        default_options = {
            "viewport": {"width": 1280, "height": 720},
            "ignore_https_errors": True,
        }
        default_options.update(context_kwargs)
        return browser.new_context(**default_options)

    def create_page(self, context: BrowserContext) -> Page:
        """Creates a page within the given context and configures default timeouts."""
        page = context.new_page()
        page.set_default_timeout(self.settings.DEFAULT_TIMEOUT_MS)
        return page

    @contextmanager
    def session(self) -> Generator[Tuple[Browser, BrowserContext, Page], None, None]:
        """Convenience context manager yielding (browser, context, page) with guaranteed cleanup."""
        with sync_playwright() as playwright:
            browser = self.launch_browser(playwright)
            context = self.create_context(browser)
            page = self.create_page(context)
            try:
                yield browser, context, page
            finally:
                page.close()
                context.close()
                browser.close()
