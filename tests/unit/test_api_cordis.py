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

    @patch("cordis_data.api.cordis.time.sleep")
    @patch("cordis_data.api.cordis.urllib.request.urlopen")
    def test_fetch_project_retry_on_500(
        self, mock_urlopen: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Test fetch_project retries on HTTP 500."""
        response_data = {"objective": "Success"}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__.return_value = mock_response

        mock_urlopen.side_effect = [
            urllib.error.HTTPError("url", 500, "Server Error", {}, None),
            mock_response,
        ]

        client = CordisClient()
        result = client.fetch_project("TEST123", retries=2)

        assert result["objective"] == "Success"
        assert mock_urlopen.call_count == 2
        mock_sleep.assert_called_once()

    @patch("cordis_data.api.cordis.time.sleep")
    @patch("cordis_data.api.cordis.urllib.request.urlopen")
    def test_fetch_project_retry_on_429(
        self, mock_urlopen: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Test fetch_project retries on HTTP 429 (rate limit)."""
        response_data = {"objective": "Success"}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__.return_value = mock_response

        mock_urlopen.side_effect = [
            urllib.error.HTTPError("url", 429, "Too Many Requests", {}, None),
            mock_response,
        ]

        client = CordisClient()
        result = client.fetch_project("TEST123", retries=2)

        assert result["objective"] == "Success"

    @patch("cordis_data.api.cordis.time.sleep")
    @patch("cordis_data.api.cordis.urllib.request.urlopen")
    def test_fetch_project_retry_on_connection_error(
        self, mock_urlopen: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Test fetch_project retries on connection errors."""
        response_data = {"objective": "Success"}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__.return_value = mock_response

        mock_urlopen.side_effect = [
            ConnectionError("Connection refused"),
            mock_response,
        ]

        client = CordisClient()
        result = client.fetch_project("TEST123", retries=2)

        assert result["objective"] == "Success"

    def test_backoff_seconds_rate_limit(self) -> None:
        """Test backoff calculation for rate limit (429)."""
        assert CordisClient._get_backoff_seconds(429, 0) == 15
        assert CordisClient._get_backoff_seconds(429, 1) == 45
        assert CordisClient._get_backoff_seconds(429, 2) == 120

    def test_backoff_seconds_server_errors(self) -> None:
        """Test backoff calculation for 5xx errors."""
        assert CordisClient._get_backoff_seconds(500, 0) == 2
        assert CordisClient._get_backoff_seconds(502, 1) == 4
        assert CordisClient._get_backoff_seconds(503, 2) == 8

    def test_backoff_seconds_other_errors(self) -> None:
        """Test backoff calculation for other errors."""
        assert CordisClient._get_backoff_seconds(0, 0) == 1
        assert CordisClient._get_backoff_seconds(0, 1) == 3
        assert CordisClient._get_backoff_seconds(0, 2) == 5
        assert CordisClient._get_backoff_seconds(400, 0) == 1

    @patch("cordis_data.api.cordis.time.sleep")
    @patch("cordis_data.api.cordis.urllib.request.urlopen")
    def test_fetch_project_all_retries_fail(
        self, mock_urlopen: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Test fetch_project returns None when all retries exhaust."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "url", 500, "Server Error", {}, None
        )

        client = CordisClient()
        result = client.fetch_project("TEST123", retries=2)

        assert result is None
        assert mock_urlopen.call_count == 2
