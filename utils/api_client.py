"""
API Client Utility
──────────────────
Encapsulates HTTP interactions, latency measurements, and assertion helpers
for REST API health checks and SLA benchmarking.
"""

import time
from typing import Any, Dict, Optional
import requests
from config.settings import get_settings
from utils.logger import get_logger

logger = get_logger("APIClient")


class APIClient:
    """Client for making HTTP requests with latency tracking and SLA verification."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        expected_status: Optional[int] = None,
        sla_ms: Optional[int] = None,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.TARGET_URL).rstrip("/")
        self.expected_status = expected_status or settings.API_EXPECTED_STATUS
        self.sla_ms = sla_ms or settings.API_SLA_MS
        self.session = requests.Session()

    def get(self, path: str = "", timeout: int = 30, **kwargs) -> Dict[str, Any]:
        """Sends a GET request and records latency and response metadata."""
        url = f"{self.base_url}/{path}".rstrip("/") if path else self.base_url
        logger.info(f"GET {url}")

        start_time = time.monotonic()
        response = self.session.get(url, timeout=timeout, allow_redirects=True, **kwargs)
        elapsed_ms = (time.monotonic() - start_time) * 1000

        logger.info(f"Status: {response.status_code} | Elapsed: {elapsed_ms:.1f}ms")
        return {
            "url": url,
            "status": response.status_code,
            "elapsed_ms": elapsed_ms,
            "headers": dict(response.headers),
            "text": response.text,
            "ok": response.ok,
            "response": response,
        }

    def post(
        self,
        path: str = "",
        payload: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        **kwargs,
    ) -> Dict[str, Any]:
        """Sends a POST request and records latency and response metadata."""
        url = f"{self.base_url}/{path}".rstrip("/") if path else self.base_url
        payload = payload or {}
        logger.info(f"POST {url} | payload keys: {list(payload.keys())}")

        start_time = time.monotonic()
        response = self.session.post(
            url, json=payload, timeout=timeout, allow_redirects=True, **kwargs
        )
        elapsed_ms = (time.monotonic() - start_time) * 1000

        logger.info(f"Status: {response.status_code} | Elapsed: {elapsed_ms:.1f}ms")
        return {
            "url": url,
            "status": response.status_code,
            "elapsed_ms": elapsed_ms,
            "headers": dict(response.headers),
            "text": response.text,
            "ok": response.ok,
            "response": response,
        }

    def close(self) -> None:
        """Closes the underlying HTTP session."""
        self.session.close()
