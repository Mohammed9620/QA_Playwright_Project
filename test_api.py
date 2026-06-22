import os
import time
import requests
from dotenv import load_dotenv


# ──────────────────────────────────────────────
#  Load environment variables from .env file
# ──────────────────────────────────────────────
load_dotenv()

TARGET_URL          = os.getenv("TARGET_URL")
API_EXPECTED_STATUS = int(os.getenv("API_EXPECTED_STATUS", "200"))
API_SLA_MS          = int(os.getenv("API_SLA_MS", "3000"))   # milliseconds

# Guard: fail early with a clear message if the required variable is missing
if not TARGET_URL:
    raise EnvironmentError(
        "[ERROR] TARGET_URL is not set. "
        "Please check your .env file or environment before running this module."
    )


# ──────────────────────────────────────────────
#  API Client Object: APIEndpoint
#  Follows the same structural pattern as LoginPage in main_test.py
# ──────────────────────────────────────────────
class APIEndpoint:
    """Encapsulates HTTP interactions with a target API endpoint."""

    def __init__(self, base_url: str, expected_status: int = 200, sla_ms: int = 3000):
        self.base_url        = base_url.rstrip("/")
        self.expected_status = expected_status
        self.sla_ms          = sla_ms

    def get(self, path: str = "") -> dict:
        """Sends a GET request and returns a result dict with status, elapsed_ms, ok."""
        url = f"{self.base_url}/{path}".rstrip("/")
        print(f"[INFO] GET {url}")

        start    = time.monotonic()
        response = requests.get(url, timeout=30, allow_redirects=True)
        elapsed  = (time.monotonic() - start) * 1000  # convert to ms

        print(f"[INFO] Status: {response.status_code} | Elapsed: {elapsed:.1f}ms")
        return {
            "url":        url,
            "status":     response.status_code,
            "elapsed_ms": elapsed,
            "headers":    dict(response.headers),
            "ok":         response.ok,
        }

    def post(self, path: str = "", payload: dict = None) -> dict:
        """Sends a POST request and returns a result dict."""
        url     = f"{self.base_url}/{path}".rstrip("/")
        payload = payload or {}
        print(f"[INFO] POST {url} | payload keys: {list(payload.keys())}")

        start    = time.monotonic()
        response = requests.post(url, json=payload, timeout=30, allow_redirects=True)
        elapsed  = (time.monotonic() - start) * 1000

        print(f"[INFO] Status: {response.status_code} | Elapsed: {elapsed:.1f}ms")
        return {
            "url":        url,
            "status":     response.status_code,
            "elapsed_ms": elapsed,
            "headers":    dict(response.headers),
            "ok":         response.ok,
        }


# ──────────────────────────────────────────────
#  pytest Test Functions
# ──────────────────────────────────────────────
def test_api_get_status():
    """Verifies that a GET request to the target URL returns the expected HTTP status code."""
    endpoint = APIEndpoint(
        base_url=TARGET_URL,
        expected_status=API_EXPECTED_STATUS,
        sla_ms=API_SLA_MS,
    )

    try:
        result = endpoint.get()
    except requests.exceptions.ConnectionError as exc:
        raise AssertionError(
            f"[FAIL] Could not connect to {TARGET_URL}: {exc}"
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise AssertionError(
            f"[FAIL] Request to {TARGET_URL} timed out: {exc}"
        ) from exc

    assert result["status"] == API_EXPECTED_STATUS, (
        f"[FAIL] Expected HTTP {API_EXPECTED_STATUS}, got {result['status']} "
        f"for URL: {result['url']}"
    )
    print(f"[PASS] GET status check passed — HTTP {result['status']}.")


def test_api_response_time_sla():
    """Verifies that the target endpoint responds within the configured SLA (default 3000ms)."""
    endpoint = APIEndpoint(
        base_url=TARGET_URL,
        expected_status=API_EXPECTED_STATUS,
        sla_ms=API_SLA_MS,
    )

    try:
        result = endpoint.get()
    except requests.exceptions.ConnectionError as exc:
        raise AssertionError(
            f"[FAIL] Could not connect to {TARGET_URL}: {exc}"
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise AssertionError(
            f"[FAIL] Request timed out before SLA could be measured: {exc}"
        ) from exc

    assert result["elapsed_ms"] <= API_SLA_MS, (
        f"[FAIL] Response time {result['elapsed_ms']:.1f}ms exceeded SLA of {API_SLA_MS}ms "
        f"for URL: {result['url']}"
    )
    print(
        f"[PASS] Response time SLA passed — {result['elapsed_ms']:.1f}ms "
        f"(SLA: {API_SLA_MS}ms)."
    )
