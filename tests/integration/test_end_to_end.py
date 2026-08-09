"""End-to-end integration tests."""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from cordis_data.data.calls import CallsFetcher
from cordis_data.data.projects import ProjectsFetcher


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_workflow_calls_to_projects(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test full workflow: fetch calls then fetch projects."""
        calls_file = temp_dir / "calls.json"
        projects_file = temp_dir / "projects.json"

        sample_call = {
            "reference": "CALL-001",
            "metadata": {
                "identifier": ["HORIZON-CL1-2024"],
                "title": ["Test Call"],
                "status": ["31094503"],
                "frameworkProgramme": ["43108390"],
            },
        }
        mock_sedia_client.search.return_value = {
            "results": [sample_call],
            "totalResults": 1,
        }

        calls_fetcher = CallsFetcher(sedia_client=mock_sedia_client)
        calls_fetcher.main(output_path=calls_file, force=True)

        assert calls_file.exists()
        calls_data = json.loads(calls_file.read_text())
        assert len(calls_data) > 0
        assert all("reference" in c for c in calls_data)

    def test_calls_fetcher_produces_valid_json(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test CallsFetcher produces valid, well-formed JSON."""
        output_file = temp_dir / "calls.json"
        mock_sedia_client.search.return_value = {
            "results": [
                {
                    "reference": f"CALL-{i:03d}",
                    "metadata": {
                        "identifier": [f"HORIZON-CL{i}-2024"],
                        "title": [f"Test Call {i}"],
                        "status": ["31094502"],
                        "frameworkProgramme": ["43108390"],
                    },
                }
                for i in range(5)
            ],
            "totalResults": 5,
        }

        fetcher = CallsFetcher(sedia_client=mock_sedia_client)
        fetcher.main(output_path=output_file, force=True)

        data = json.loads(output_file.read_text())
        assert isinstance(data, list)
        assert len(data) == 5
        assert all(isinstance(call, dict) for call in data)
        assert all("topicId" in call for call in data)
        assert all("reference" in call for call in data)

    def test_projects_fetcher_produces_valid_json(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test ProjectsFetcher produces valid, well-formed JSON."""
        calls_file = temp_dir / "calls.json"
        projects_file = temp_dir / "projects.json"

        calls = [
            {"reference": "CALL-001", "callStatus": "closed", "topicId": "HORIZON-CL1"}
        ]
        calls_file.write_text(json.dumps(calls))

        sample_project = {
            "reference": "PROJ-001",
            "metadata": {
                "projectId": ["123456"],
                "acronym": ["TEST"],
                "status": ["Active"],
                "ecContribution": ["1000000"],
            },
        }
        mock_sedia_client.search.return_value = {
            "results": [sample_project],
            "totalResults": 1,
        }

        fetcher = ProjectsFetcher(sedia_client=mock_sedia_client)
        fetcher.main(output_path=projects_file, calls_path=calls_file)

    def test_metadata_file_created(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test metadata file is created during fetch."""
        output_file = temp_dir / "calls.json"
        metadata_file = temp_dir.parent / ".metadata.json"

        mock_sedia_client.search.return_value = {
            "results": [],
            "totalResults": 0,
        }

        fetcher = CallsFetcher(sedia_client=mock_sedia_client)
        fetcher.main(output_path=output_file, force=True)

        assert metadata_file.exists()
        metadata = json.loads(metadata_file.read_text())
        assert "calls_fetched_at" in metadata
        assert "calls_freshness_ttl_days" in metadata

    def test_consecutive_fetches_merge_data(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test consecutive fetches merge data correctly."""
        output_file = temp_dir / "calls.json"

        first_call = {
            "reference": "CALL-001",
            "metadata": {
                "identifier": ["HORIZON-CL1"],
                "title": ["Call 1"],
                "status": ["31094502"],
                "frameworkProgramme": ["43108390"],
            },
        }
        mock_sedia_client.search.return_value = {
            "results": [first_call],
            "totalResults": 1,
        }

        fetcher = CallsFetcher(sedia_client=mock_sedia_client)
        fetcher.main(output_path=output_file, force=True)

        first_data = json.loads(output_file.read_text())
        assert len(first_data) == 1

        second_call = {
            "reference": "CALL-002",
            "metadata": {
                "identifier": ["HORIZON-CL2"],
                "title": ["Call 2"],
                "status": ["31094502"],
                "frameworkProgramme": ["43108390"],
            },
        }
        mock_sedia_client.search.return_value = {
            "results": [second_call],
            "totalResults": 1,
        }

        fetcher.main(output_path=output_file, force=True)

        merged_data = json.loads(output_file.read_text())
        assert len(merged_data) == 2

    def test_error_recovery_with_temporary_file(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test error handling with temporary files."""
        output_file = temp_dir / "calls.json"

        mock_sedia_client.search.return_value = {
            "results": [],
            "totalResults": 0,
        }

        fetcher = CallsFetcher(sedia_client=mock_sedia_client)
        fetcher.main(output_path=output_file, force=True)

        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_data_integrity_after_enrichment(
        self, mock_sedia_client: Mock, mock_cordis_client: Mock, temp_dir: Path
    ) -> None:
        """Test data integrity after CORDIS enrichment."""
        calls_file = temp_dir / "calls.json"
        projects_file = temp_dir / "projects.json"

        calls = [
            {
                "reference": "CALL-001",
                "callStatus": "closed",
                "topicId": "HORIZON-CL1"
            }
        ]
        calls_file.write_text(json.dumps(calls))

        sample_project = {
            "reference": "PROJ-001",
            "metadata": {
                "projectId": ["123456"],
                "acronym": ["TEST"],
                "status": ["Active"],
            },
        }
        mock_sedia_client.search.return_value = {
            "results": [sample_project],
            "totalResults": 1,
        }

        mock_cordis_client.fetch_project.return_value = {
            "objective": "Test objective",
            "identifiers": {"grantDoi": "10.1234/test"},
        }

        fetcher = ProjectsFetcher(
            sedia_client=mock_sedia_client, cordis_client=mock_cordis_client
        )
        fetcher.main(output_path=projects_file, calls_path=calls_file)
