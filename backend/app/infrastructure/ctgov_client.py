"""Thin client for the ClinicalTrials.gov Data API v2 (ML/Data Layer ingestion).

See https://clinicaltrials.gov/api/v2/studies for the upstream API contract.
"""

import time
from collections.abc import Callable, Iterator
from typing import Any

import httpx

DEFAULT_PAGE_SIZE = 100
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_SECONDS = 1.0

# 429 (rate limited) and 5xx (transient upstream issues) are worth retrying;
# other 4xx errors (e.g. 400 bad request) indicate a bug in our request, not a
# transient failure, so they should fail fast instead of retrying.
RETRIABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class ClinicalTrialsGovClient:
    def __init__(
        self,
        base_url: str,
        page_size: int = DEFAULT_PAGE_SIZE,
        http_client: httpx.Client | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._page_size = page_size
        self._http_client = http_client or httpx.Client(timeout=30.0)
        self._max_retries = max_retries
        self._backoff_seconds = backoff_seconds
        self._sleep = sleep

    def search_studies(
        self,
        condition: str,
        statuses: list[str] | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Yield raw study records matching the given condition, following pagination."""
        params: dict[str, Any] = {
            "query.cond": condition,
            "pageSize": self._page_size,
        }
        if statuses:
            params["filter.overallStatus"] = ",".join(statuses)

        page_token: str | None = None
        while True:
            request_params = dict(params)
            if page_token:
                request_params["pageToken"] = page_token

            payload = self._get_page(request_params)

            yield from payload.get("studies", [])

            page_token = payload.get("nextPageToken")
            if not page_token:
                break

    def _get_page(self, params: dict[str, Any]) -> dict[str, Any]:
        attempt = 0
        while True:
            response = self._http_client.get(f"{self._base_url}/studies", params=params)

            if response.status_code in RETRIABLE_STATUS_CODES and attempt < self._max_retries:
                self._sleep(self._retry_delay_seconds(response, attempt))
                attempt += 1
                continue

            response.raise_for_status()
            return response.json()

    def _retry_delay_seconds(self, response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after is not None:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return self._backoff_seconds * (2**attempt)
