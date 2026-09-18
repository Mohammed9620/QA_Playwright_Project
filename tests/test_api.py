"""
API Health & Performance SLA Test Suite
───────────────────────────────────────
Verifies HTTP endpoint availability, status codes, and latency compliance
against configured Service Level Agreements (SLAs).
"""

import pytest
import requests
from utils.api_client import APIClient
from config.settings import Settings
from utils.logger import get_logger

logger = get_logger("TestAPI")


@pytest.mark.api
def test_api_get_status(api_client: APIClient, settings: Settings):
    """Verifies that a GET request to the target returns the expected HTTP status code."""
    try:
        result = api_client.get()
    except requests.exceptions.ConnectionError as exc:
        raise AssertionError(f"[FAIL] Could not connect to {settings.TARGET_URL}: {exc}") from exc
    except requests.exceptions.Timeout as exc:
        raise AssertionError(f"[FAIL] Request to {settings.TARGET_URL} timed out: {exc}") from exc

    assert result["status"] == settings.API_EXPECTED_STATUS, (
        f"[FAIL] Expected HTTP {settings.API_EXPECTED_STATUS}, got {result['status']} "
        f"for URL: {result['url']}"
    )
    logger.pass_step(f"GET status check passed — HTTP {result['status']}.")


@pytest.mark.api
@pytest.mark.performance
def test_api_response_time_sla(api_client: APIClient, settings: Settings):
    """Verifies that the target responds within the designated SLA threshold."""
    try:
        result = api_client.get()
    except requests.exceptions.ConnectionError as exc:
        raise AssertionError(f"[FAIL] Could not connect to {settings.TARGET_URL}: {exc}") from exc
    except requests.exceptions.Timeout as exc:
        raise AssertionError(f"[FAIL] Request timed out before SLA could be measured: {exc}") from exc

    assert result["elapsed_ms"] <= settings.API_SLA_MS, (
        f"[FAIL] Response time {result['elapsed_ms']:.1f}ms exceeded SLA of {settings.API_SLA_MS}ms "
        f"for URL: {result['url']}"
    )
    logger.pass_step(
        f"Response time SLA passed — {result['elapsed_ms']:.1f}ms (SLA: {settings.API_SLA_MS}ms)."
    )
