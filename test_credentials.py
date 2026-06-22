import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page


# ──────────────────────────────────────────────
#  Load environment variables from .env file
# ──────────────────────────────────────────────
load_dotenv()

TARGET_URL = os.getenv("TARGET_URL")

# Guard: fail early with a clear message if the required variable is missing
if not TARGET_URL:
    raise EnvironmentError(
        "[ERROR] TARGET_URL is not set. "
        "Please check your .env file or environment before running this module."
    )

# ──────────────────────────────────────────────
#  Configurable wordlist
#  Override by setting WORDLIST_USERS / WORDLIST_PASSES in .env
#  Each env var is a comma-separated list.
# ──────────────────────────────────────────────
_DEFAULT_USERS = [
    "admin", "administrator", "user", "test", "guest",
    "root", "demo", "standard_user", "operator", "support",
]

_DEFAULT_PASSES = [
    "password", "123456", "password1", "admin", "letmein",
    "welcome", "monkey", "dragon", "qwerty", "secret_sauce",
]

WORDLIST_USERS = (
    os.getenv("WORDLIST_USERS", "").split(",")
    if os.getenv("WORDLIST_USERS")
    else _DEFAULT_USERS
)

WORDLIST_PASSES = (
    os.getenv("WORDLIST_PASSES", "").split(",")
    if os.getenv("WORDLIST_PASSES")
    else _DEFAULT_PASSES
)


# ──────────────────────────────────────────────
#  Page Object: CredentialProbePage
# ──────────────────────────────────────────────
class CredentialProbePage:
    """Encapsulates login interactions for the credential bruteforce probe.
    Reuses the same locator strategy as LoginPage in main_test.py.
    """

    def __init__(self, page: Page, url: str):
        self.page = page
        self.url  = url

    def Maps(self) -> dict:
        """Returns a dictionary of all locators used on the Login page."""
        return {
            "username_field": self.page.locator(os.getenv("USER_LOCATOR", "#user-name")),
            "password_field": self.page.locator(os.getenv("PASS_LOCATOR", "#password")),
            "login_button":   self.page.locator(os.getenv("LOGIN_LOCATOR", "#login-button")),
        }

    def navigate(self):
        """Opens the login page in the browser."""
        self.page.goto(self.url)
        print(f"[INFO] Navigated to: {self.url}")

    def attempt_login(self, username: str, password: str):
        """Fills in credentials and clicks the Login button."""
        locators = self.Maps()
        locators["username_field"].fill(username)
        locators["password_field"].fill(password)
        locators["login_button"].click()

    def is_login_successful(self) -> bool:
        """Returns True if the browser redirected away from the login page."""
        return "/inventory.html" in self.page.url

    def reset_to_login(self):
        """Navigate back to the login page to reset state for the next attempt."""
        self.page.goto(self.url)


# ──────────────────────────────────────────────
#  pytest Test Function
# ──────────────────────────────────────────────
def test_credential_bruteforce_probe():
    """Probes the login form with a list of common credentials.

    PASS criteria: No credential pair from the wordlist grants access.
    FAIL criteria: At least one credential pair successfully authenticates
                   (indicates a weak default credential is active).
    """
    successful_pairs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page    = browser.new_page()

        probe_page = CredentialProbePage(page, url=TARGET_URL)
        probe_page.navigate()

        for username in WORDLIST_USERS:
            for password in WORDLIST_PASSES:
                print(f"[INFO] Trying: {username} / {'*' * len(password)}")

                probe_page.attempt_login(username, password)
                page.wait_for_timeout(800)  # brief wait for redirect

                if probe_page.is_login_successful():
                    print(f"[WARN] Successful login with: {username} / {password}")
                    successful_pairs.append((username, password))

                # Always reset back to login page for the next attempt
                probe_page.reset_to_login()

        browser.close()

    # ── Assertion ────────────────────────────────
    assert len(successful_pairs) == 0, (
        f"[FAIL] {len(successful_pairs)} common credential pair(s) granted access: "
        + ", ".join(f"{u}/{p}" for u, p in successful_pairs)
    )
    print(
        f"[PASS] Credential bruteforce probe complete. "
        f"No common credentials succeeded out of "
        f"{len(WORDLIST_USERS) * len(WORDLIST_PASSES)} attempts."
    )
