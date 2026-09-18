"""
UI Authentication Test Suite
────────────────────────────
Validates core authentication behaviors, positive session initiation,
and negative error validation handling using the Page Object Model.
"""

import pytest
from pages.login_page import LoginPage
from config.settings import Settings
from utils.logger import get_logger

logger = get_logger("TestLogin")


@pytest.mark.ui
@pytest.mark.auth
def test_successful_login(login_page: LoginPage, settings: Settings):
    """
    Scenario: Valid user credentials authentication
    Expected: Redirects to inventory catalog (/inventory.html).
    """
    # Step 1: Navigate to authentication portal
    login_page.navigate_to_login()

    # Step 2: Fill credentials and submit
    login_page.login(username=settings.TEST_USER, password=settings.TEST_PASS)

    # Step 3: Allow UI transition
    login_page.wait_for_timeout(2000)
    current_url = login_page.current_url
    logger.info(f"Final URL: {current_url}")

    # Step 4: Validate redirection to protected inventory
    assert "/inventory.html" in current_url, (
        f"[FAIL] Login failed to redirect to inventory catalog. Actual URL: '{current_url}'"
    )
    logger.pass_step("Assertion passed — inventory page loaded successfully.")


@pytest.mark.ui
@pytest.mark.negative
def test_invalid_credentials_displays_error(login_page: LoginPage):
    """
    Scenario: Deliberately invalid credentials submission
    Expected: Access denied, user remains on login page, error alert displayed.
    """
    # Step 1: Navigate to authentication portal
    login_page.navigate_to_login()

    # Step 2: Attempt submission with invalid credentials
    login_page.login(username="invalid_user", password="wrong_password_999")

    # Step 3: Allow UI transition
    login_page.wait_for_timeout(2000)
    current_url = login_page.current_url
    logger.info(f"Final URL after invalid login: {current_url}")

    # Step 4: Verify navigation was blocked
    assert "/inventory.html" not in current_url, (
        "[FAIL] Invalid credentials unexpectedly granted access to inventory page."
    )

    # Step 5: Verify error alert is rendered
    assert login_page.is_error_banner_visible(), (
        "[FAIL] Authentication error banner was not visible after invalid login attempt."
    )

    # Step 6: Verify error message content
    error_text = login_page.get_error_message()
    assert "Username and password do not match" in error_text, (
        f"[FAIL] Unexpected error message received: '{error_text}'"
    )
    logger.pass_step(f"Error banner visible with message: '{error_text}'")
