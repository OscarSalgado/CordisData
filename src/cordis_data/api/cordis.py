"""CORDIS public API client."""

import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Optional, cast

from cordis_data.api.rate_limiter import TokenBucket


class CordisClient:
    """Client for the CORDIS public API."""

    def __init__(
        self,
        base_url: str = "https://cordis.europa.eu/project/id/{project_id}",
        rate_limiter: Optional[TokenBucket] = None,
        timeout: int = 30,
    ) -> None:
        """Initialize CORDIS client.

        Args:
            base_url: Base URL template for CORDIS project endpoints
            rate_limiter: Optional TokenBucket for rate limiting (default: creates one)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.rate_limiter = rate_limiter or TokenBucket(rate=2.0)
        self.timeout = timeout

    def fetch_project(self, project_id: str, retries: int = 3) -> Optional[dict[str, Any]]:
        """Fetch a project's data from CORDIS.

        Returns objective, grantDoi, and other top-level fields. Does not fetch
        nested relations (organizations, deliverables, etc.).

        A 404 means CORDIS has no record for this project — not retried. Only
        transient errors (timeouts, 5xx) are retried.

        Args:
            project_id: CORDIS project ID
            retries: Number of retry attempts

        Returns:
            Dict with 'objective' and 'grantDoi' keys, or None on failure
        """
        if not project_id:
            return None

        url = self.base_url.format(project_id=project_id) + "?format=json"

        for attempt in range(retries):
            try:
                self.rate_limiter.acquire()

                req = urllib.request.Request(url, method="GET")
                req.add_header("Accept", "application/json")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = cast(dict[str, Any], json.loads(resp.read().decode()))
                return {
                    "objective": data.get("objective"),
                    "grantDoi": (data.get("identifiers") or {}).get("grantDoi"),
                }
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                if attempt < retries - 1:
                    wait_seconds = self._get_backoff_seconds(e.code, attempt)
                    print(
                        f"  HTTP {e.code} for {project_id}: waiting {wait_seconds}s "
                        f"(attempt {attempt + 1}/{retries})",
                        file=sys.stderr,
                    )
                    time.sleep(wait_seconds)
            except Exception:
                if attempt < retries - 1:
                    wait_seconds = self._get_backoff_seconds(0, attempt)
                    print(
                        f"  Connection error for {project_id}: waiting {wait_seconds}s "
                        f"(attempt {attempt + 1}/{retries})",
                        file=sys.stderr,
                    )
                    time.sleep(wait_seconds)
        return None

    @staticmethod
    def _get_backoff_seconds(error_code: int, attempt: int) -> int:
        """Return backoff duration in seconds based on HTTP error code and attempt number.

        HTTP 429 (rate limit) gets long backoff (15s, 45s, 120s) to respect
        the API's explicit rate-limit signal.

        HTTP 5xx (server errors) gets moderate backoff (2s, 4s, 8s).

        Other errors (connection timeouts, etc.) get short backoff (1s, 3s, 5s).

        Args:
            error_code: HTTP status code (429, 500, etc.) or 0 for non-HTTP errors
            attempt: attempt number (0, 1, 2, ...)

        Returns:
            int, seconds to wait before retrying
        """
        if error_code == 429:  # Rate limit
            return [15, 45, 120][attempt]
        elif error_code in [500, 502, 503]:  # Server error
            return [2, 4, 8][attempt]
        else:  # Connection timeout, socket error, etc.
            return [1, 3, 5][attempt]

    def fetch_h2020_projects(self, retries: int = 3) -> list[dict[str, Any]]:
        """Fetch all H2020 projects from CORDIS H2020 API.

        Args:
            retries: Number of retry attempts

        Returns:
            List of project dicts, empty list on failure
        """
        base_url = "https://cordis.europa.eu/api/result/h2020/projects"
        all_projects = []
        page = 1

        while True:
            try:
                self.rate_limiter.acquire()

                url = f"{base_url}?pageSize=100&pageNumber={page}&format=json"
                req = urllib.request.Request(url, method="GET")
                req.add_header("Accept", "application/json")

                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = cast(dict[str, Any], json.loads(resp.read().decode()))
                    results = data.get("results", [])
                    all_projects.extend(results)

                    # Check if there are more pages
                    total = data.get("totalResults", 0)
                    if len(all_projects) >= total:
                        break

                    page += 1

            except urllib.error.HTTPError as e:
                if e.code == 404:
                    break
                if page < 10:  # Limit retries at page level
                    wait_seconds = self._get_backoff_seconds(e.code, 0)
                    time.sleep(wait_seconds)
                else:
                    break
            except Exception:
                if page < 10:
                    wait_seconds = self._get_backoff_seconds(0, 0)
                    time.sleep(wait_seconds)
                else:
                    break

        return all_projects

    def fetch_h2020_project(self, project_id: str, retries: int = 3) -> Optional[dict[str, Any]]:
        """Fetch single H2020 project from CORDIS.

        Args:
            project_id: H2020 project ID
            retries: Number of retry attempts

        Returns:
            Project dict or None on failure
        """
        if not project_id:
            return None

        base_url = "https://cordis.europa.eu/project/id"
        url = f"{base_url}/{project_id}?format=json"

        for attempt in range(retries):
            try:
                self.rate_limiter.acquire()

                req = urllib.request.Request(url, method="GET")
                req.add_header("Accept", "application/json")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return cast(dict[str, Any], json.loads(resp.read().decode()))
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                if attempt < retries - 1:
                    wait_seconds = self._get_backoff_seconds(e.code, attempt)
                    time.sleep(wait_seconds)
            except Exception:
                if attempt < retries - 1:
                    wait_seconds = self._get_backoff_seconds(0, attempt)
                    time.sleep(wait_seconds)

        return None
