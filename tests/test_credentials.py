"""
Credential Bruteforce & Weak Password Probe
───────────────────────────────────────────
Automates dictionary probing against the login form using externalized datasets.
PASS criteria: Zero unauthorized credential pairs succeed.
FAIL criteria: Any unauthorized weak/default credentials grant authenticated access.
"""

import pytest
from pages.login_page import LoginPage
from utils.data_loader import get_credential_wordlists
from utils.logger import get_logger

logger = get_logger("TestCredentials")


@pytest.mark.security
@pytest.mark.slow
def test_credential_bruteforce_probe(login_page: LoginPage):
    """Probes the authentication interface with dictionary wordlists."""
    users, passwords = get_credential_wordlists()
    successful_pairs = []

    login_page.navigate_to_login()

    for username in users:
        for password in passwords:
            logger.info(f"Trying: {username} / {'*' * len(password)}")
            login_page.attempt_login(username, password)
            login_page.wait_for_timeout(600)

            if login_page.is_login_successful():
                logger.warn(f"Successful login with: {username} / {password}")
                successful_pairs.append((username, password))

            # Reset back to login form for next probe iteration
            login_page.reset_state()

    # Assert no dictionary passwords breached authentication
    assert len(successful_pairs) == 0, (
        f"[FAIL] {len(successful_pairs)} common credential pair(s) granted access: "
        + ", ".join(f"{u}/{p}" for u, p in successful_pairs)
    )

    total_attempts = len(users) * len(passwords)
    logger.pass_step(
        f"Credential bruteforce probe complete. No common credentials succeeded "
        f"out of {total_attempts} attempts."
    )
