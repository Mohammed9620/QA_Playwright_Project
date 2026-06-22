import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page



# ──────────────────────────────────────────────
#  Load environment variables from .env file
# ──────────────────────────────────────────────
load_dotenv()

TARGET_URL = os.getenv("TARGET_URL")
TEST_USER  = os.getenv("TEST_USER")
TEST_PASS  = os.getenv("TEST_PASS")

# Guard: fail early with a clear message if any variable is missing
if not all([TARGET_URL, TEST_USER, TEST_PASS]):
    raise EnvironmentError(
        "[ERROR] One or more required environment variables are missing. "
        "Please check your .env file for: TARGET_URL, TEST_USER, TEST_PASS"
    )


# ──────────────────────────────────────────────
#  Page Object: LoginPage
# ──────────────────────────────────────────────
class LoginPage:
    """Encapsulates all interactions with the login page.
    The target URL and credentials are injected at runtime from .env.
    """

    def __init__(self, page: Page, url: str):
        self.page = page
        self.url  = url

    # ── Locator Map ──────────────────────────────
    def Maps(self) -> dict:
        """Returns a dictionary of all locators used on the Login page."""
        return {
            "username_field": self.page.locator(os.getenv("USER_LOCATOR", "#user-name")),
            "password_field": self.page.locator(os.getenv("PASS_LOCATOR", "#password")),
            "login_button":   self.page.locator(os.getenv("LOGIN_LOCATOR", "#login-button")),
        }

    # ── Actions ──────────────────────────────────
    def navigate(self):
        """Opens the login page in the browser."""
        self.page.goto(self.url)
        print(f"[INFO] Navigated to: {self.url}")

    def login(self, username: str, password: str):
        """Fills in credentials and clicks the Login button."""
        locators = self.Maps()

        locators["username_field"].fill(username)
        print(f"[INFO] Entered username: {username}")

        locators["password_field"].fill(password)
        print(f"[INFO] Entered password: {'*' * len(password)}")

        locators["login_button"].click()
        print("[INFO] Clicked the Login button.")


# ──────────────────────────────────────────────
#  pytest Test Function
# ──────────────────────────────────────────────
def test_login():
    """Verifies that a valid user can log in and reach the inventory page."""
    with sync_playwright() as p:
        # Run headless for server compatibility (Step 5 audit)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Instantiate the page object — URL is injected from .env, not hardcoded
        login_page = LoginPage(page, url=TARGET_URL)

        # Execute the login flow — credentials come from .env
        login_page.navigate()
        login_page.login(username=TEST_USER, password=TEST_PASS)

        # Pause so you can see the result
        page.wait_for_timeout(3000)
        print(f"[INFO] Final URL: {page.url}")

        # ── Assertion ────────────────────────────────
        assert "/inventory.html" in page.url, (
            f"[FAIL] Login did not redirect to inventory page. "
            f"Actual URL: {page.url}"
        )
        print("[PASS] Assertion passed — inventory page loaded successfully.")

        browser.close()


# ──────────────────────────────────────────────
#  pytest Test Function — Negative Case
# ──────────────────────────────────────────────
def test_invalid_login():
    """Verifies that invalid credentials are rejected and an error is shown."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Reuse the LoginPage class with the same target URL from .env
        login_page = LoginPage(page, url=TARGET_URL)

        # Navigate and attempt login with deliberately wrong credentials
        login_page.navigate()
        login_page.login(username="invalid_user", password="wrong_pass")

        # Pause so you can see the result
        page.wait_for_timeout(3000)
        print(f"[INFO] Final URL after invalid login: {page.url}")

        # ── Assertions ───────────────────────────────
        # 1. The page must NOT have navigated away from the login screen
        assert "/inventory.html" not in page.url, (
            "[FAIL] Invalid login unexpectedly redirected to inventory page."
        )

        # 2. The error message container must be visible
        error_banner = page.locator("[data-test='error']")
        assert error_banner.is_visible(), (
            "[FAIL] Error message banner was not visible after invalid login."
        )

        # 3. The error text must mention wrong credentials
        error_text = error_banner.inner_text()
        assert "Username and password do not match" in error_text, (
            f"[FAIL] Unexpected error message: '{error_text}'"
        )

        print(f"[PASS] Error banner visible with message: '{error_text}'")

        browser.close()
