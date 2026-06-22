import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, BrowserContext


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
#  Page Object: AuthSecurityPage
# ──────────────────────────────────────────────
class AuthSecurityPage:
    """Encapsulates session and cookie security checks.
    Follows the same structural pattern as LoginPage in main_test.py.
    """

    def __init__(self, page: Page, context: BrowserContext, url: str):
        self.page    = page
        self.context = context
        self.url     = url

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

    def get_cookies(self) -> list:
        """Returns all cookies for the current context."""
        return self.context.cookies()

    def get_session_storage_keys(self) -> list:
        """Returns all keys stored in sessionStorage."""
        return self.page.evaluate("() => Object.keys(sessionStorage)")

    def get_local_storage_keys(self) -> list:
        """Returns all keys stored in localStorage."""
        return self.page.evaluate("() => Object.keys(localStorage)")

    def logout(self):
        """Attempts to trigger logout by navigating to a common logout path."""
        self.page.goto(f"{self.url.rstrip('/')}/index.html")
        print("[INFO] Triggered logout / session reset via navigation.")

    def is_protected_page_accessible(self) -> bool:
        """Returns True if the inventory page is reachable without re-authenticating."""
        self.page.goto(f"{self.url.rstrip('/')}/inventory.html")
        self.page.wait_for_timeout(1000)
        return "/inventory.html" in self.page.url


# ──────────────────────────────────────────────
#  pytest Test Functions
# ──────────────────────────────────────────────
def test_cookie_security_flags():
    """Checks that session cookies carry HttpOnly, Secure, and SameSite flags."""
    issues = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page    = context.new_page()

        auth_page = AuthSecurityPage(page, context, url=TARGET_URL)
        auth_page.navigate()
        auth_page.login(username=TEST_USER, password=TEST_PASS)

        page.wait_for_timeout(1500)
        cookies = auth_page.get_cookies()

        print(f"[INFO] Inspecting {len(cookies)} cookie(s)...")

        for cookie in cookies:
            name = cookie.get("name", "<unnamed>")

            if not cookie.get("httpOnly", False):
                issues.append(f"Cookie '{name}' is missing the HttpOnly flag.")
                print(f"[WARN] Cookie '{name}': missing HttpOnly")

            if not cookie.get("secure", False):
                issues.append(f"Cookie '{name}' is missing the Secure flag.")
                print(f"[WARN] Cookie '{name}': missing Secure")

            same_site = cookie.get("sameSite", "").lower()
            if same_site not in ("strict", "lax"):
                issues.append(
                    f"Cookie '{name}' has a weak or missing SameSite value: '{same_site}'."
                )
                print(f"[WARN] Cookie '{name}': SameSite = '{same_site}'")

        browser.close()

    # ── Assertion ────────────────────────────────
    assert len(issues) == 0, (
        f"[FAIL] {len(issues)} cookie security issue(s) found:\n"
        + "\n".join(f"  - {i}" for i in issues)
    )
    print(f"[PASS] All {len(cookies)} cookie(s) passed security flag checks.")


def test_session_token_not_in_url():
    """Checks that the session token or auth credential is NOT exposed in the URL."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page    = context.new_page()

        auth_page = AuthSecurityPage(page, context, url=TARGET_URL)
        auth_page.navigate()
        auth_page.login(username=TEST_USER, password=TEST_PASS)

        page.wait_for_timeout(1500)
        final_url = page.url
        print(f"[INFO] Post-login URL: {final_url}")

        # Common token parameter names to check for
        sensitive_params = ["token", "session", "auth", "key", "access_token", "sessionid"]
        found_in_url = [p for p in sensitive_params if p in final_url.lower()]

        browser.close()

    # ── Assertion ────────────────────────────────
    assert len(found_in_url) == 0, (
        f"[FAIL] Sensitive parameter(s) found in URL after login: {found_in_url}\n"
        f"URL: {final_url}"
    )
    print("[PASS] No session token or auth credential exposed in the post-login URL.")


def test_logout_invalidates_session():
    """Checks that navigating to a protected page after logout is blocked."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page    = context.new_page()

        auth_page = AuthSecurityPage(page, context, url=TARGET_URL)

        # Step 1: Log in successfully
        auth_page.navigate()
        auth_page.login(username=TEST_USER, password=TEST_PASS)
        page.wait_for_timeout(1500)

        assert "/inventory.html" in page.url, (
            "[FAIL] Pre-condition failed — could not log in before testing logout."
        )
        print("[INFO] Logged in successfully. Now testing logout invalidation...")

        # Step 2: Trigger logout
        auth_page.logout()
        page.wait_for_timeout(1500)

        # Step 3: Attempt to re-access the protected page directly
        still_accessible = auth_page.is_protected_page_accessible()

        browser.close()

    # ── Assertion ────────────────────────────────
    assert not still_accessible, (
        "[FAIL] Protected page (inventory.html) was accessible after logout. "
        "Session was NOT properly invalidated."
    )
    print("[PASS] Logout invalidation check passed — protected page is no longer accessible.")
