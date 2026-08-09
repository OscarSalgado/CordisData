"""Tests for CommitteeDocumentsClient."""

from unittest.mock import Mock, patch

import pytest

from cordis_data.data.committees.client import CommitteeDocumentsClient


class TestCommitteeDocumentsClient:
    """Test CommitteeDocumentsClient."""

    def test_init_default(self) -> None:
        """Test client initialization."""
        client = CommitteeDocumentsClient()
        assert client.max_retries == 3
        assert client.rate_limiter is not None

    def test_fetch_documents_success(self) -> None:
        """Test successful document fetch."""
        client = CommitteeDocumentsClient()
        with patch("cordis_data.data.committees.client.requests.post") as mock_post:
            mock_post.return_value.json.return_value = {
                "content": [{"documentReference": "116169"}],
                "totalElements": 1,
            }
            result = client.fetch_documents(["C70408"])
            assert result["totalElements"] == 1
            assert len(result["content"]) == 1

    def test_download_attachment_success(self) -> None:
        """Test attachment download."""
        client = CommitteeDocumentsClient()
        with patch("cordis_data.data.committees.client.requests.get") as mock_get:
            mock_get.return_value.content = b"%PDF-1.4"
            result = client.download_attachment(533495, "116169", 1)
            assert result.startswith(b"%PDF")

    def test_retry_on_429(self) -> None:
        """Test retry on rate limit."""
        client = CommitteeDocumentsClient()
        with patch("cordis_data.data.committees.client.requests.get") as mock_get:
            mock_get.side_effect = [
                Mock(status_code=429),
                Mock(status_code=200, json=lambda: {}),
            ]
            # Should retry and succeed
            with patch.object(client, "_request_with_retry") as mock_retry:
                mock_retry.return_value = Mock(json=lambda: {"ok": True})
                result = client.fetch_document_detail("116169", 1)
                assert result["ok"] is True

    def test_list_committees_success(self) -> None:
        """Test committee list fetch."""
        client = CommitteeDocumentsClient()
        with patch("cordis_data.data.committees.client.requests.get") as mock_get:
            mock_get.return_value.json.return_value = [
                {"code": "C70408", "title": "Digital, Industry and Space"}
            ]
            result = client.list_committees()
            assert len(result) == 1
            assert result[0]["code"] == "C70408"
