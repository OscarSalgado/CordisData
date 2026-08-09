"""Tests for CordisClient."""

import json
from unittest.mock import MagicMock, patch

import urllib.error

from cordis_data.api.cordis import CordisClient
from cordis_data.api.rate_limiter import TokenBucket

class TestCordisClient:
    """Tests for CORDIS API client."""

    def test_client_initialization(self) -> None:
        """Test initializing CordisClient with defaults."""
        client = CordisClient()
        assert "cordis.europa.eu" in client.base_url
        assert client.rate_limiter is not None

    def test_client_with_custom_rate_limiter(self) -> None:
        """Test initializing with custom rate limiter."""
        limiter = TokenBucket(rate=1.0)
        client = CordisClient(rate_limiter=limiter)
        assert client.rate_limiter is limiter

    @patch("cordis_data.api.cordis.urllib.request.urlopen")
    def test_fetch_project_success(self, mock_urlopen: MagicMock) -> None:
        """Test successful project fetch."""
        response_data = {
            "objective": "Test objective",
            "identifiers": {"grantDoi": "10.1234/test"},
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        client = CordisClient()
        result = client.fetch_project("TEST123")

        assert result["objective"] == "Test objective"
        assert result["grantDoi"] == "10.1234/test"

    def test_fetch_project_with_empty_id(self) -> None:
        """Test fetching with empty project ID."""
        client = CordisClient()
        result = client.fetch_project("")
        assert result is None

    @patch("cordis_data.api.cordis.urllib.request.urlopen")
    def test_fetch_project_404_returns_none(self, mock_urlopen: MagicMock) -> None:
        """Test that 404 returns None without retry."""
        error = urllib.error.HTTPError("url", 404, "Not Found", {}, None)
        mock_urlopen.side_effect = error

        client = CordisClient()
        result = client.fetch_project("NOTFOUND")

        assert result is None
        assert mock_urlopen.call_count == 1  # No retries for 404
