"""End-to-end integration tests."""

import json
from pathlib import Path
from unittest.mock import Mock

from cordis_data.data.closed_calls import ClosedCallsFetcher
from cordis_data.data.open_calls import OpenCallsFetcher
from cordis_data.data.projects import ProjectsFetcher


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_workflow_open_calls_to_projects(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test full workflow: fetch open calls then fetch projects."""
        (temp_dir / "calls").mkdir(exist_ok=True)
        calls_file = temp_dir / "calls" / "open.jsonl.gz"

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

        open_fetcher = OpenCallsFetcher(sedia_client=mock_sedia_client)
        open_fetcher.main(force=True)

        assert calls_file.exists()

    def test_open_calls_fetcher_produces_valid_jsonl_gz(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test OpenCallsFetcher produces valid JSONL.GZ format."""
        (temp_dir / "calls").mkdir(exist_ok=True)
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

        fetcher = OpenCallsFetcher(sedia_client=mock_sedia_client)
        fetcher.main(force=True)

        output_file = temp_dir / "calls" / "open.jsonl.gz"
        assert output_file.exists()

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
        (temp_dir / "calls").mkdir(exist_ok=True)
        metadata_file = temp_dir.parent / ".metadata.json"

        mock_sedia_client.search.return_value = {
            "results": [],
            "totalResults": 0,
        }

        fetcher = OpenCallsFetcher(sedia_client=mock_sedia_client)
        fetcher.main(force=True)

        assert metadata_file.exists()
        metadata = json.loads(metadata_file.read_text())
        assert "calls_open_fetched_at" in metadata
        assert "calls_open_freshness_ttl_days" in metadata

    def test_consecutive_fetches_merge_data(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test consecutive fetches merge data correctly."""
        (temp_dir / "calls").mkdir(exist_ok=True)
        output_file = temp_dir / "calls" / "open.jsonl.gz"

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

        fetcher = OpenCallsFetcher(sedia_client=mock_sedia_client)
        fetcher.main(force=True)

        assert output_file.exists()

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

        fetcher.main(force=True)

        assert output_file.exists()

    def test_error_recovery_with_jsonl_gz_file(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test error handling with JSONL.GZ files."""
        (temp_dir / "calls").mkdir(exist_ok=True)
        output_file = temp_dir / "calls" / "open.jsonl.gz"

        mock_sedia_client.search.return_value = {
            "results": [],
            "totalResults": 0,
        }

        fetcher = OpenCallsFetcher(sedia_client=mock_sedia_client)
        fetcher.main(force=True)

        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_closed_calls_fetcher_produces_valid_jsonl_gz(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test ClosedCallsFetcher produces valid JSONL.GZ format."""
        (temp_dir / "calls").mkdir(exist_ok=True)
        mock_sedia_client.search.return_value = {
            "results": [
                {
                    "reference": f"CALL-{i:03d}",
                    "metadata": {
                        "identifier": [f"HORIZON-CL{i}-2023"],
                        "title": [f"Closed Call {i}"],
                        "status": ["31094501"],
                        "frameworkProgramme": ["43108390"],
                    },
                }
                for i in range(3)
            ],
            "totalResults": 3,
        }

        fetcher = ClosedCallsFetcher(sedia_client=mock_sedia_client)
        fetcher.main(force=True)

        output_file = temp_dir / "calls" / "closed.jsonl.gz"
        assert output_file.exists()

    def test_data_integrity_after_enrichment(
        self, mock_sedia_client: Mock, mock_cordis_client: Mock, temp_dir: Path
    ) -> None:
        """Test data integrity after CORDIS enrichment."""
        (temp_dir / "calls").mkdir(exist_ok=True)
        calls_file = temp_dir / "calls" / "closed.jsonl.gz"
        projects_file = temp_dir / "projects.json"

        # Create a closed calls file with test data
        mock_sedia_client.search.return_value = {
            "results": [
                {
                    "reference": "CALL-001",
                    "metadata": {
                        "identifier": ["HORIZON-CL1"],
                        "title": ["Closed Call"],
                        "status": ["31094501"],
                        "frameworkProgramme": ["43108390"],
                    },
                }
            ],
            "totalResults": 1,
        }

        closed_fetcher = ClosedCallsFetcher(sedia_client=mock_sedia_client)
        closed_fetcher.main(force=True)

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
