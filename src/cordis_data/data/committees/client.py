"""Client for EU comitology-register REST API."""

import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests

from cordis_data.api.rate_limiter import TokenBucket


class CommitteeDocumentsClient:
    """Client for EU comitology-register REST API."""

    BASE_URL = "https://ec.europa.eu/transparency/comitology-register/core/api/front"
    INTEGRATION_BASE = "https://ec.europa.eu/transparency/comitology-register/core/api/integration/ers"

    def __init__(self, rate_limiter: Optional[TokenBucket] = None) -> None:
        """Initialize client with optional rate limiter.

        Args:
            rate_limiter: TokenBucket for rate limiting (default: 2 requests/sec)
        """
        self.rate_limiter = rate_limiter or TokenBucket(rate=2)
        self.session = requests.Session()
        self.max_retries = 3

    def _request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """Execute HTTP request with exponential backoff retry.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional request parameters

        Returns:
            Response object

        Raises:
            requests.HTTPError: If request fails after all retries
        """
        for attempt in range(self.max_retries):
            try:
                if method.upper() == "GET":
                    resp = requests.get(url, **kwargs)
                elif method.upper() == "POST":
                    resp = requests.post(url, **kwargs)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                # Retry on rate limit or server error
                if resp.status_code in [429, 500, 502, 503, 504]:
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) + (1 if attempt > 0 else 0)
                        time.sleep(wait_time)
                        continue
                    resp.raise_for_status()
                else:
                    resp.raise_for_status()
                    return resp

            except requests.RequestException:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = (2 ** attempt) + (1 if attempt > 0 else 0)
                time.sleep(wait_time)

        return resp

    def fetch_documents(
        self,
        committee_codes: list[str],
        start_date: Optional[str] = None,
        page: int = 0,
        size: int = 100,
    ) -> dict:
        """Fetch documents from comitology-register API.

        Args:
            committee_codes: List of committee codes to fetch
            start_date: ISO-8601 start date (default: 90 days ago)
            page: Page number (0-indexed)
            size: Results per page (max 100)

        Returns:
            API response with content[], totalElements, totalPages, pageable
        """
        if start_date is None:
            # Default to 90 days ago
            start_date = (datetime.now(timezone.utc) - timedelta(days=90)).strftime(
                "%Y-%m-%dT%H:%M:%S.000Z"
            )

        self.rate_limiter.acquire()

        url = f"{self.BASE_URL}/documents/search?page={page}&size={size}&sort=documentReference,asc"
        payload = {
            "reset": True,
            "committeeCodes": committee_codes,
            "documentStartDate": start_date,
        }

        resp = self._request_with_retry("POST", url, json=payload, timeout=10)
        return resp.json()

    def fetch_document_detail(self, document_reference: str, version: int) -> dict:
        """Fetch complete document details including attachments.

        Args:
            document_reference: Document reference ID
            version: Document version number

        Returns:
            Document metadata including documentsAttached[], meeting, etc.
        """
        self.rate_limiter.acquire()

        url = f"{self.BASE_URL}/documents/{document_reference}/{version}"
        resp = self._request_with_retry("GET", url, timeout=10)
        return resp.json()

    def download_attachment(
        self,
        attachment_id: int,
        document_reference: str,
        version: int,
    ) -> bytes:
        """Download PDF attachment.

        Args:
            attachment_id: Attachment ID
            document_reference: Document reference
            version: Document version

        Returns:
            PDF binary content
        """
        self.rate_limiter.acquire()

        url = f"{self.INTEGRATION_BASE}/{attachment_id}/{document_reference}/{version}/attachment"
        resp = self._request_with_retry("GET", url, timeout=10)
        return resp.content

    def list_committees(self) -> list[dict]:
        """Fetch list of all available committees.

        Returns:
            List of dicts with 'code' and 'title' fields
        """
        self.rate_limiter.acquire()

        url = f"{self.BASE_URL}/committees"
        resp = self._request_with_retry("GET", url, timeout=10)
        return resp.json()
