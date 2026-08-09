"""SEDIA Search API client."""

import json
import sys
import time
import urllib.parse
import urllib.request
import uuid
from typing import Any, cast


def build_multipart(
    fields: dict[str, tuple[str, str | bytes, str]],
    boundary: str,
) -> bytes:
    """Build multipart/form-data body."""
    body = b""
    for name, (fn, data, ct) in fields.items():
        body += f"--{boundary}\r\n".encode()
        content_disposition = (
            f'Content-Disposition: form-data; name="{name}"; '
            f'filename="{fn}"\r\n'
        )
        body += content_disposition.encode()
        body += f"Content-Type: {ct}\r\n\r\n".encode()
        body += data.encode() if isinstance(data, str) else data
        body += b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    return body


class SediaClient:
    """Client for the SEDIA Search API."""

    def __init__(
        self,
        api_url: str = "https://api.tech.ec.europa.eu/search-api/prod/rest/search",
        api_key: str = "SEDIA",
        timeout: int = 30,
    ) -> None:
        """Initialize SEDIA client.

        Args:
            api_url: Base URL of SEDIA Search API
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.api_url = api_url
        self.api_key = api_key
        self.timeout = timeout

    def search(
        self,
        query: dict[str, Any],
        sort: dict[str, str],
        page_num: int = 1,
        page_size: int = 100,
        retries: int = 3,
    ) -> dict[str, Any]:
        """Execute a search query against SEDIA API.

        Args:
            query: Elasticsearch query dict
            sort: Sort specification dict
            page_num: Page number (1-indexed)
            page_size: Results per page
            retries: Number of retry attempts

        Returns:
            Response dict with 'results', 'totalResults', etc.
        """
        for attempt in range(retries):
            try:
                boundary = uuid.uuid4().hex
                params = urllib.parse.urlencode({
                    "apiKey": self.api_key,
                    "text": "***",
                    "pageSize": str(page_size),
                    "pageNumber": str(page_num),
                })
                fields_dict = {
                    "query": ("blob", json.dumps(query), "application/json"),
                    "sort": ("blob", json.dumps(sort), "application/json"),
                    "languages": (
                        "blob",
                        json.dumps(["en"]),
                        "application/json",
                    ),
                }
                fields = cast(
                    dict[str, tuple[str, str | bytes, str]], fields_dict
                )
                body = build_multipart(fields, boundary)
                req = urllib.request.Request(
                    f"{self.api_url}?{params}",
                    data=body,
                    method="POST",
                )
                content_type = (
                    f"multipart/form-data; boundary={boundary}"
                )
                req.add_header("Content-Type", content_type)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode())
            except Exception as e:
                print(
                    f"  Attempt {attempt + 1} failed: {e}",
                    file=sys.stderr,
                )
                if attempt < retries - 1:
                    time.sleep(2 * (attempt + 1))
        return {"results": []}
