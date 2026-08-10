"""Integration tests for committee discovery."""

from pathlib import Path
from unittest.mock import Mock, patch

from cordis_data.data.committees.discovery import CommitteeDiscovery
from cordis_data.data.committees.issue_formatter import format_issue_body


class TestCommitteeDiscoveryE2E:
    """End-to-end tests for committee discovery."""

    def test_discovery_workflow_no_new(self, tmp_path: Path) -> None:
        """Test complete discovery workflow with no new committees."""
        log_path = tmp_path / "discovery.json"

        with patch("cordis_data.data.committees.discovery.CommitteeConfig") as mock_config_class:
            mock_config_class.load.return_value = {
                "committees": [
                    {"code": "C70408", "name": "Digital Committee"}
                ]
            }

            with patch("cordis_data.data.committees.discovery.CommitteeDocumentsClient") as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                mock_client.list_committees.return_value = [
                    {"code": "C70408", "title": "Digital Committee"}
                ]

                discovery = CommitteeDiscovery(mock_client)
                discovery.DISCOVERY_LOG_PATH = log_path

                result = discovery.discover()

                assert not result.has_new()
                assert len(result.new_committees) == 0
                assert result.total_committees == 1
                assert result.currently_monitored == 1

    def test_discovery_workflow_with_new(self, tmp_path: Path) -> None:
        """Test complete discovery workflow with new committees."""
        log_path = tmp_path / "discovery.json"

        with patch("cordis_data.data.committees.discovery.CommitteeConfig") as mock_config_class:
            mock_config_class.load.return_value = {
                "committees": [
                    {"code": "C70408", "name": "Digital Committee"}
                ]
            }

            with patch("cordis_data.data.committees.discovery.CommitteeDocumentsClient") as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                mock_client.list_committees.return_value = [
                    {"code": "C70408", "title": "Digital Committee"},
                    {"code": "C70409", "title": "Innovation Committee"},
                    {"code": "C70410", "title": "Research Committee"},
                ]

                discovery = CommitteeDiscovery(mock_client)
                discovery.DISCOVERY_LOG_PATH = log_path

                result = discovery.discover()

                assert result.has_new()
                assert len(result.new_committees) == 2
                assert result.total_committees == 3
                assert result.currently_monitored == 1

                # Verify log was written
                assert log_path.exists()

    def test_discovery_deduplication(self, tmp_path: Path) -> None:
        """Test that discovery doesn't report same committee twice."""
        log_path = tmp_path / "discovery.json"

        with patch("cordis_data.data.committees.discovery.CommitteeConfig") as mock_config_class:
            mock_config_class.load.return_value = {
                "committees": []
            }

            with patch("cordis_data.data.committees.discovery.CommitteeDocumentsClient") as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                mock_client.list_committees.return_value = [
                    {"code": "C70409", "title": "Innovation Committee"}
                ]

                discovery = CommitteeDiscovery(mock_client)
                discovery.DISCOVERY_LOG_PATH = log_path

                # First run - should find new committee
                result1 = discovery.discover()
                assert result1.has_new()
                assert len(result1.new_committees) == 1

                # Second run - should NOT find as new (deduped)
                result2 = discovery.discover()
                assert not result2.has_new()
                assert len(result2.new_committees) == 0

    def test_issue_formatting(self) -> None:
        """Test GitHub issue formatting."""
        committees = [
            {"code": "C70409", "title": "Innovation Committee"},
            {"code": "C70410", "title": "Research Coordination"},
        ]

        body = format_issue_body(committees)

        assert "C70409" in body
        assert "Innovation Committee" in body
        assert "C70410" in body
        assert "Research Coordination" in body
        assert "EU Comitology Register" in body
        assert "Add to Monitoring" in body
        assert "cordis-data monitor add-committee" in body

    def test_issue_formatting_markdown_table(self) -> None:
        """Test that issue body contains proper markdown table."""
        committees = [
            {"code": "C70409", "title": "Committee A"},
        ]

        body = format_issue_body(committees)

        # Check for markdown table structure
        assert "| Code | Title |" in body
        assert "| C70409 | Committee A |" in body
        assert "https://ec.europa.eu/transparency/comitology-register" in body

    def test_discovery_log_persistence(self, tmp_path: Path) -> None:
        """Test that discovery log persists across runs."""
        log_path = tmp_path / "discovery.json"

        with patch("cordis_data.data.committees.discovery.CommitteeConfig") as mock_config_class:
            mock_config_class.load.return_value = {"committees": []}

            with patch("cordis_data.data.committees.discovery.CommitteeDocumentsClient") as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client

                # First discovery run
                mock_client.list_committees.return_value = [
                    {"code": "C1", "title": "Committee 1"}
                ]

                discovery = CommitteeDiscovery(mock_client)
                discovery.DISCOVERY_LOG_PATH = log_path
                discovery.discover()

                # Second discovery run
                mock_client.list_committees.return_value = [
                    {"code": "C1", "title": "Committee 1"},
                    {"code": "C2", "title": "Committee 2"},
                ]

                discovery.discover()

                # Verify both are in log
                log = discovery._load_discovery_log()
                codes = {d["code"] for d in log["discoveries"]}
                assert "C1" in codes
                assert "C2" in codes

    def test_discovery_reporting_history(self, tmp_path: Path) -> None:
        """Test that discovery tracks reported issues."""
        log_path = tmp_path / "discovery.json"

        with patch("cordis_data.data.committees.discovery.CommitteeConfig") as mock_config_class:
            mock_config_class.load.return_value = {"committees": []}

            with patch("cordis_data.data.committees.discovery.CommitteeDocumentsClient") as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                mock_client.list_committees.return_value = [
                    {"code": "C70409", "title": "New Committee"}
                ]

                discovery = CommitteeDiscovery(mock_client)
                discovery.DISCOVERY_LOG_PATH = log_path

                # Run discovery
                discovery.discover()

                # Mark as reported
                discovery.mark_as_reported(["C70409"])

                # Verify status
                log = discovery._load_discovery_log()
                assert log["discoveries"][0]["reported"] is True
                assert len(log["history"]["issues_created"]) > 0
