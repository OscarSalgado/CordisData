"""Tests for committee document enrichment with download URLs."""

from unittest.mock import Mock
from cordis_data.data.committees.fetcher import CommitteeDocumentsFetcher


class TestDocumentEnrichment:
    """Test document enrichment with attachments and URLs."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.BASE_URL = (
            "https://ec.europa.eu/transparency/comitology-register/core/api/front"
        )
        self.fetcher = CommitteeDocumentsFetcher(self.mock_client)

    def test_enrich_document_with_single_attachment(self) -> None:
        """Test enriching document with one attachment."""
        self.mock_client.fetch_document_detail.return_value = {
            "documentsAttached": [
                {"id": 12345, "fileName": "document.pdf"}
            ]
        }

        doc = {
            "documentReference": "108662",
            "version": 6,
            "title": "Test Document",
        }

        enriched = self.fetcher._enrich_with_attachments(doc)

        assert "attachments" in enriched
        assert len(enriched["attachments"]) == 1
        assert enriched["attachments"][0]["id"] == 12345
        assert enriched["attachments"][0]["filename"] == "document.pdf"
        assert "download_url" in enriched["attachments"][0]
        assert enriched["attachments"][0]["download_url"].startswith("https://")

    def test_enrich_document_with_multiple_attachments(self) -> None:
        """Test enriching document with multiple attachments."""
        self.mock_client.fetch_document_detail.return_value = {
            "documentsAttached": [
                {"id": 111, "fileName": "main.pdf"},
                {"id": 222, "fileName": "annex.pdf"},
                {"id": 333, "fileName": "summary.pdf"},
            ]
        }

        doc = {
            "documentReference": "115416",
            "version": 3,
            "title": "Multi-Attachment Document",
        }

        enriched = self.fetcher._enrich_with_attachments(doc)

        assert len(enriched["attachments"]) == 3
        assert enriched["attachments"][0]["download_url"].startswith("https://")

    def test_enrich_document_without_attachments(self) -> None:
        """Test enriching document with no attachments."""
        self.mock_client.fetch_document_detail.return_value = {
            "documentsAttached": []
        }

        doc = {
            "documentReference": "999999",
            "version": 1,
            "title": "Document without attachments",
        }

        enriched = self.fetcher._enrich_with_attachments(doc)

        assert "attachments" in enriched
        assert enriched["attachments"] == []
        assert "download_url" not in enriched

    def test_url_construction_format(self) -> None:
        """Test that download URLs follow correct format."""
        self.mock_client.fetch_document_detail.return_value = {
            "documentsAttached": [
                {"id": 99999, "fileName": "test.pdf"}
            ]
        }

        doc = {
            "documentReference": "108662",
            "version": 6,
            "title": "Test",
        }

        enriched = self.fetcher._enrich_with_attachments(doc)
        url = enriched["attachments"][0]["download_url"]

        assert url.startswith("https://ec.europa.eu/transparency/comitology-register")
        assert "/core/api/integration/ers/99999/108662/6/attachment" in url
        assert url.endswith("/attachment")

    def test_enrich_handles_missing_document_reference(self) -> None:
        """Test enrichment gracefully handles missing documentReference."""
        doc = {
            "version": 6,
            "title": "No reference",
        }

        enriched = self.fetcher._enrich_with_attachments(doc)

        assert enriched["attachments"] == []

    def test_enrich_handles_api_failure(self) -> None:
        """Test enrichment handles API call failures gracefully."""
        self.mock_client.fetch_document_detail.side_effect = Exception(
            "API connection error"
        )

        doc = {
            "documentReference": "108662",
            "version": 6,
            "title": "Test",
        }

        enriched = self.fetcher._enrich_with_attachments(doc)

        assert "attachments" in enriched
        assert enriched["attachments"] == []
        assert "download_url" not in enriched

    def test_enriched_document_has_all_original_fields(self) -> None:
        """Test that enrichment preserves all original document fields."""
        self.mock_client.fetch_document_detail.return_value = {
            "documentsAttached": [{"id": 123, "fileName": "doc.pdf"}]
        }

        original_fields = {
            "documentReference": "108662",
            "version": 6,
            "title": "Original Title",
            "committeeCode": "C70407",
            "creationDate": "2026-08-03T07:50:48Z",
            "updateDate": "2026-08-03T11:12:19Z",
        }

        enriched = self.fetcher._enrich_with_attachments(original_fields.copy())

        for field, value in original_fields.items():
            assert enriched[field] == value
        assert "attachments" in enriched
        assert len(enriched["attachments"]) > 0
        assert "download_url" in enriched["attachments"][0]
