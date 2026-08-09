"""Tests for SediaClient."""

import json
from unittest.mock import MagicMock, patch

from cordis_data.api.sedia import SediaClient


class TestSediaClient:
    """Tests for SEDIA API client."""

    def test_client_initialization(self) -> None:
        """Test initializing SediaClient with defaults."""
        client = SediaClient()
        assert client.api_key == "SEDIA"
        assert "api.tech.ec.europa.eu" in client.api_url

    def test_client_with_custom_params(self) -> None:
        """Test initializing with custom parameters."""
        client = SediaClient(api_key="CUSTOM", timeout=60)
        assert client.api_key == "CUSTOM"
        assert client.timeout == 60

    @patch("cordis_data.api.sedia.urllib.request.urlopen")
    def test_search_success(self, mock_urlopen: MagicMock) -> None:
        """Test successful search call."""
        response_data = {
            "results": [{"id": "1"}],
            "totalResults": 1,
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        client = SediaClient()
        result = client.search(query={"test": "query"}, sort={"field": "date"})

        assert result["totalResults"] == 1
        assert len(result["results"]) == 1

    @patch("cordis_data.api.sedia.urllib.request.urlopen")
    def test_search_returns_empty_on_failure(
        self, mock_urlopen: MagicMock
    ) -> None:
        """Test search returns empty on network error."""
        mock_urlopen.side_effect = Exception("Network error")

        client = SediaClient(timeout=1)
        result = client.search(query={"test": "query"}, sort={"field": "date"}, retries=1)

        assert result["results"] == []

    @patch("cordis_data.api.sedia.time.sleep")
    @patch("cordis_data.api.sedia.urllib.request.urlopen")
    def test_search_retry_with_sleep(
        self, mock_urlopen: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Test search retries and sleeps on error."""
        response_data = {
            "results": [{"id": "1"}],
            "totalResults": 1,
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__.return_value = mock_response

        # First attempt fails, second succeeds
        mock_urlopen.side_effect = [
            Exception("First attempt fails"),
            mock_response,
        ]

        client = SediaClient(timeout=1)
        result = client.search(
            query={"test": "query"},
            sort={"field": "date"},
            retries=2
        )

        # Should succeed on second attempt
        assert result["totalResults"] == 1
        # Verify sleep was called during retry
        mock_sleep.assert_called()
