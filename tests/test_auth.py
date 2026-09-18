"""
Broken Authentication & Session Security Audit Suite
────────────────────────────────────────────────────
Conducts penetration checks for session cookie security flags (HttpOnly, Secure, SameSite),
sensitive token leakage in browser URLs, and session termination invalidation.
"""

import pytest
from pages.auth_security_page import AuthSecurityPage
from config.settings import Settings
from utils.logger import get_logger

logger = get_logger("TestAuth")


@pytest.mark.security
@pytest.mark.auth
def test_cookie_security_flags(auth_security_page: AuthSecurityPage, settings: Settings):
    """Audits session cookies to ensure mandatory security flags (HttpOnly, Secure, SameSite) are active."""
    issues = []

    auth_security_page.navigate_to_login()
    auth_security_page.login(username=settings.TEST_USER, password=settings.TEST_PASS)
    auth_security_page.wait_for_timeout(1500)

    cookies = auth_security_page.get_cookies()
    logger.info(f"Inspecting {len(cookies)} cookie(s)...")

    for cookie in cookies:
        name = cookie.get("name", "<unnamed>")

        if not cookie.get("httpOnly", False):
            issues.append(f"Cookie '{name}' is missing the HttpOnly flag.")
            logger.warn(f"Cookie '{name}': missing HttpOnly")

        if not cookie.get("secure", False):
            issues.append(f"Cookie '{name}' is missing the Secure flag.")
            logger.warn(f"Cookie '{name}': missing Secure")

        same_site = cookie.get("sameSite", "").lower()
        if same_site not in ("strict", "lax"):
            issues.append(
                f"Cookie '{name}' has a weak or missing SameSite attribute: '{same_site}'."
            )
            logger.warn(f"Cookie '{name}': SameSite = '{same_site}'")

    assert len(issues) == 0, (
        f"[FAIL] {len(issues)} cookie security issue(s) detected:\n"
        + "\n".join(f"  - {i}" for i in issues)
    )
    logger.pass_step(f"All {len(cookies)} cookie(s) passed security flag checks.")


@pytest.mark.security
@pytest.mark.auth
def test_session_token_not_in_url(auth_security_page: AuthSecurityPage, settings: Settings):
    """Verifies that authentication tokens and session identifiers are never exposed in browser URLs."""
    auth_security_page.navigate_to_login()
    auth_security_page.login(username=settings.TEST_USER, password=settings.TEST_PASS)
    auth_security_page.wait_for_timeout(1500)

    final_url = auth_security_page.current_url
    logger.info(f"Post-login URL: {final_url}")

    sensitive_params = ["token", "session", "auth", "key", "access_token", "sessionid"]
    found_in_url = [p for p in sensitive_params if p in final_url.lower()]

    assert len(found_in_url) == 0, (
        f"[FAIL] Sensitive parameter(s) detected in URL post-login: {found_in_url}\n"
        f"URL: {final_url}"
    )
    logger.pass_step("No session token or auth credential exposed in the post-login URL.")


@pytest.mark.security
@pytest.mark.auth
def test_logout_invalidates_session(auth_security_page: AuthSecurityPage, settings: Settings):
    """Verifies that session termination properly revokes access to protected routes."""
    # Step 1: Establish authenticated session
    auth_security_page.navigate_to_login()
    auth_security_page.login(username=settings.TEST_USER, password=settings.TEST_PASS)
    auth_security_page.wait_for_timeout(1500)

    assert "/inventory.html" in auth_security_page.current_url, (
        "[FAIL] Pre-condition failed — could not authenticate prior to logout verification."
    )
    logger.info("Logged in successfully. Now testing logout invalidation...")

    # Step 2: Trigger logout
    auth_security_page.logout()
    auth_security_page.wait_for_timeout(1500)

    # Step 3: Attempt accessing protected catalog
    still_accessible = auth_security_page.is_protected_page_accessible()

    assert not still_accessible, (
        "[FAIL] Protected page (/inventory.html) was accessible after logout. "
        "Session was NOT properly invalidated on the server."
    )
    logger.pass_step("Logout invalidation check passed — protected page is no longer accessible.")
