"""End-to-end integration tests for committee monitoring."""

from pathlib import Path
from unittest.mock import Mock, patch

from cordis_data.data.committees.config import CommitteeConfig
from cordis_data.data.committees.fetcher import CommitteeDocumentsFetcher


class TestCommitteeMonitoringE2E:
    """End-to-end tests for committee monitoring flow."""

    def test_full_monitoring_flow(self, tmp_path: Path) -> None:
        """Test full monitoring flow: config, fetch, detect changes."""
        config_path = tmp_path / "config.json"
        output_path = tmp_path / "documents.json"

        # Step 1: Configure committees
        with patch.object(CommitteeConfig, "_get_current_config_path", return_value=config_path):
            CommitteeConfig.add_committee("C70408", "Digital Committee")
            config = CommitteeConfig.load()
            assert len(config["committees"]) == 1

        # Step 2: Mock fetch and detect changes
        with patch("cordis_data.data.committees.fetcher.CommitteeDocumentsClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock API response with 2 documents
            mock_client.fetch_documents.return_value = {
                "content": [
                    {
                        "documentReference": "116169",
                        "title": "Committee Opinion",
                        "creationDate": "2026-07-01T00:00:00Z",
                        "committeeCoding": "C70408",
                        "documentType": "Opinion",
                    },
                    {
                        "documentReference": "116170",
                        "title": "Another Document",
                        "creationDate": "2026-07-02T00:00:00Z",
                        "committeeCoding": "C70408",
                        "documentType": "Report",
                    },
                ],
                "totalPages": 1,
            }

            fetcher = CommitteeDocumentsFetcher(mock_client)

            # Step 3: Run fetch
            new_docs = fetcher.main(
                ["C70408"],
                output_path=output_path,
                window_days=90,
            )

            # Verify new documents detected
            assert len(new_docs) == 2

            # Step 4: Verify file saved
            assert output_path.exists()
            import json

            saved_docs = json.loads(output_path.read_text())
            assert len(saved_docs) == 2
            assert saved_docs[0]["documentReference"] == "116169"

    def test_change_detection_on_second_fetch(self, tmp_path: Path) -> None:
        """Test that second fetch detects updates and new documents."""
        output_path = tmp_path / "documents.json"

        # First fetch: 2 documents
        first_batch = [
            {
                "documentReference": "116169",
                "title": "Committee Opinion",
                "updateDate": "2026-07-01T12:00:00Z",
                "creationDate": "2026-07-01T00:00:00Z",
            },
            {
                "documentReference": "116170",
                "title": "Another Document",
                "updateDate": "2026-07-02T12:00:00Z",
                "creationDate": "2026-07-02T00:00:00Z",
            },
        ]

        with patch("cordis_data.data.committees.fetcher.CommitteeDocumentsClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.fetch_documents.return_value = {
                "content": first_batch,
                "totalPages": 1,
            }

            fetcher = CommitteeDocumentsFetcher(mock_client)
            fetcher.main(["C70408"], output_path=output_path)

            # Second fetch: 1 old (updated), 1 old (unchanged), 1 new
            second_batch = [
                {
                    "documentReference": "116169",
                    "title": "Committee Opinion",
                    "updateDate": "2026-07-01T14:00:00Z",  # Updated
                    "creationDate": "2026-07-01T00:00:00Z",
                },
                {
                    "documentReference": "116170",
                    "title": "Another Document",
                    "updateDate": "2026-07-02T12:00:00Z",  # Unchanged
                    "creationDate": "2026-07-02T00:00:00Z",
                },
                {
                    "documentReference": "116171",
                    "title": "New Document",
                    "updateDate": "2026-07-03T12:00:00Z",  # New
                    "creationDate": "2026-07-03T00:00:00Z",
                },
            ]

            mock_client.fetch_documents.return_value = {
                "content": second_batch,
                "totalPages": 1,
            }

            new_docs = fetcher.main(["C70408"], output_path=output_path)

            # Should detect 1 new document
            assert len(new_docs) == 1
            assert new_docs[0]["documentReference"] == "116171"

            # All 3 should be saved
            import json

            saved_docs = json.loads(output_path.read_text())
            assert len(saved_docs) == 3

    def test_changelog_generation(self, tmp_path: Path) -> None:
        """Test changelog generation during fetch."""
        output_path = tmp_path / "documents.json"
        changelog_dir = tmp_path / "changelog"

        with patch("cordis_data.data.committees.fetcher.CommitteeDocumentsClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.fetch_documents.return_value = {
                "content": [
                    {
                        "documentReference": "116169",
                        "title": "Test",
                        "creationDate": "2026-07-01T00:00:00Z",
                    }
                ],
                "totalPages": 1,
            }

            fetcher = CommitteeDocumentsFetcher(mock_client)
            fetcher.main(["C70408"], output_path=output_path)

            # Generate changelog
            from cordis_data.data.changelog import ChangeEvent

            events = [
                ChangeEvent(
                    reference="test-ref",
                    topicId="116169",
                    event_type="NEW",
                    detected_at="2026-08-01T12:00:00Z",
                    snapshot={"title": "Test"},
                )
            ]

            fetcher.save_changelog(events, changelog_dir)

            # Verify changelog created
            from datetime import UTC, datetime

            today = datetime.now(UTC).strftime("%Y-%m-%d")
            changelog_file = changelog_dir / f"{today}.json"
            assert changelog_file.exists()

            import json

            changelog = json.loads(changelog_file.read_text())
            assert changelog["summary"]["new"] == 1
            assert len(changelog["events"]) == 1
