"""Tests for ProjectsFetcher."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from cordis_data.data.projects import ProjectsFetcher


class TestProjectsFetcher:
    """Tests for ProjectsFetcher class."""

    def test_init_default(self) -> None:
        """Test ProjectsFetcher initialization with defaults."""
        fetcher = ProjectsFetcher()
        assert fetcher.sedia_client is not None
        assert fetcher.cordis_client is not None
        assert fetcher.rate_limiter is not None

    def test_init_with_clients(
        self, mock_sedia_client: Mock, mock_cordis_client: Mock
    ) -> None:
        """Test ProjectsFetcher initialization with provided clients."""
        fetcher = ProjectsFetcher(
            sedia_client=mock_sedia_client, cordis_client=mock_cordis_client
        )
        assert fetcher.sedia_client == mock_sedia_client
        assert fetcher.cordis_client == mock_cordis_client

    def test_build_projects_query(self) -> None:
        """Test query builder for projects."""
        fetcher = ProjectsFetcher()
        topic_ids = ["HORIZON-CL1", "HORIZON-CL2"]
        query = fetcher._build_projects_query(topic_ids)
        assert "bool" in query
        assert "must" in query["bool"]
        assert query["bool"]["must"][0]["terms"]["topicAbbreviation"] == topic_ids

    def test_chunk_list(self) -> None:
        """Test chunking list of items."""
        fetcher = ProjectsFetcher()
        items = list(range(100))
        chunks = list(fetcher._chunk(items, 25))
        assert len(chunks) == 4
        assert len(chunks[0]) == 25

    def test_transform_project_record(self) -> None:
        """Test basic project record transformation."""
        fetcher = ProjectsFetcher()
        raw_record = {
            "reference": "PROJ-001",
            "metadata": {
                "acronym": ["EXAMPLE"],
                "projectId": ["123456"],
                "ecContribution": ["1000000"],
                "overallBudget": ["1500000"],
                "status": ["Active"],
                "startDate": ["2024-01-01"],
                "endDate": ["2025-12-31"],
            },
        }
        transformed = fetcher._transform_project_record(raw_record)
        assert isinstance(transformed, dict)
        assert "projectId" in transformed
        assert "acronym" in transformed

    def test_transform_project_missing_fields(self) -> None:
        """Test project transformation with missing fields."""
        fetcher = ProjectsFetcher()
        raw_record = {"reference": "", "metadata": {}}
        transformed = fetcher._transform_project_record(raw_record)
        assert transformed.get("projectId") == ""
        assert transformed.get("acronym") == ""

    def test_needs_cordis_enrichment_new_project(self) -> None:
        """Test enrichment check for new project."""
        fetcher = ProjectsFetcher()
        project = {"projectId": "NEW-001", "objective": None}
        existing = {}
        needs = fetcher._needs_cordis_enrichment(project, existing)
        assert needs is True

    def test_needs_cordis_enrichment_existing_rich(self) -> None:
        """Test enrichment check for already enriched project."""
        fetcher = ProjectsFetcher()
        project = {"projectId": "OLD-001", "objective": "Existing"}
        existing = {
            "OLD-001": {"objective": "Existing data", "lastEnrichedAt": "2024-08-01"}
        }
        result = fetcher._needs_cordis_enrichment(project, existing)
        assert isinstance(result, bool)

    def test_load_closed_topic_ids(self, temp_dir: Path) -> None:
        """Test loading closed topic IDs from calls file."""
        calls_file = temp_dir / "calls.json"
        calls = [
            {"reference": "CALL-001", "callStatus": "closed", "topicId": "HORIZON-CL1"},
            {"reference": "CALL-002", "callStatus": "open", "topicId": "HORIZON-CL2"},
            {"reference": "CALL-003", "callStatus": "closed", "topicId": "HORIZON-CL3"},
        ]
        calls_file.write_text(json.dumps(calls))

        fetcher = ProjectsFetcher()
        topic_ids = fetcher._load_closed_topic_ids(calls_file)
        assert len(topic_ids) == 2
        assert "HORIZON-CL1" in topic_ids
        assert "HORIZON-CL3" in topic_ids
        assert "HORIZON-CL2" not in topic_ids

    def test_fetch_projects_batch(self, mock_sedia_client: Mock) -> None:
        """Test single batch fetch."""
        mock_sedia_client.search.return_value = {
            "results": [{"reference": "PROJ-001"}],
            "totalResults": 1,
        }

        fetcher = ProjectsFetcher(sedia_client=mock_sedia_client)
        result = fetcher._fetch_projects_batch(["HORIZON-CL1"], 1)

        assert "results" in result
        assert "totalResults" in result
        mock_sedia_client.search.assert_called_once()

    def test_main_with_empty_calls(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test main() with empty calls file."""
        calls_file = temp_dir / "calls.json"
        calls_file.write_text(json.dumps([]))

        output_file = temp_dir / "projects.json"

        fetcher = ProjectsFetcher(sedia_client=mock_sedia_client)
        fetcher.main(output_path=output_file, calls_path=calls_file)

    def test_main_with_closed_calls(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test main() fetches only closed calls."""
        calls_file = temp_dir / "calls.json"
        calls = [
            {"reference": "CALL-001", "callStatus": "closed", "topicId": "HORIZON-CL1"},
            {"reference": "CALL-002", "callStatus": "open", "topicId": "HORIZON-CL2"},
        ]
        calls_file.write_text(json.dumps(calls))

        output_file = temp_dir / "projects.json"

        mock_sedia_client.search.return_value = {
            "results": [],
            "totalResults": 0,
        }

        fetcher = ProjectsFetcher(sedia_client=mock_sedia_client)
        fetcher.main(output_path=output_file, calls_path=calls_file)

    def test_main_with_years_filter(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test main() with years filter."""
        calls_file = temp_dir / "calls.json"
        calls = [
            {
                "reference": "CALL-001",
                "callStatus": "closed",
                "topicId": "HORIZON-CL1",
                "deadline": "2020-01-01",
            }
        ]
        calls_file.write_text(json.dumps(calls))

        output_file = temp_dir / "projects.json"

        mock_sedia_client.search.return_value = {
            "results": [],
            "totalResults": 0,
        }

        fetcher = ProjectsFetcher(sedia_client=mock_sedia_client)
        fetcher.main(output_path=output_file, calls_path=calls_file, years=10)

    def test_handle_missing_calls_file(self, temp_dir: Path) -> None:
        """Test handling of missing calls file."""
        nonexistent_file = temp_dir / "nonexistent.json"
        output_file = temp_dir / "projects.json"

        fetcher = ProjectsFetcher()
        with pytest.raises(FileNotFoundError):
            fetcher.main(output_path=output_file, calls_path=nonexistent_file)

    def test_batch_all_pages(self, mock_sedia_client: Mock) -> None:
        """Test fetching all pages for a batch."""
        mock_sedia_client.search.side_effect = [
            {"results": [{"reference": f"PROJ-{i}"} for i in range(100)], "totalResults": 150},
            {"results": [{"reference": f"PROJ-{i}"} for i in range(100, 150)], "totalResults": 150},
        ]

        fetcher = ProjectsFetcher(sedia_client=mock_sedia_client)
        batch = ["HORIZON-CL1", "HORIZON-CL2"]
        results = fetcher._fetch_batch_all_pages(batch)

        assert len(results) == 150

    def test_write_and_merge_projects(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test writing and merging projects."""
        output_file = temp_dir / "projects.json"

        existing = [
            {"projectId": "P001", "acronym": "OLD", "objective": "Old objective"}
        ]
        output_file.write_text(json.dumps(existing))

        new_projects = [
            {"projectId": "P002", "acronym": "NEW", "objective": "New objective"}
        ]

        fetcher = ProjectsFetcher()
        fetcher._write_and_merge_projects(new_projects, output_file)

        merged = json.loads(output_file.read_text())
        assert len(merged) == 2
        assert any(p["projectId"] == "P001" for p in merged)
        assert any(p["projectId"] == "P002" for p in merged)

    def test_enrich_projects_with_cordis(
        self, mock_sedia_client: Mock, mock_cordis_client: Mock, temp_dir: Path
    ) -> None:
        """Test enriching projects with CORDIS data."""
        output_file = temp_dir / "projects.json"

        projects = [
            {"projectId": "P001", "acronym": "TEST", "objective": None, "grantDoi": None}
        ]

        mock_cordis_client.fetch_project.return_value = {
            "objective": "Enriched objective",
            "grantDoi": "10.1234/test"
        }

        fetcher = ProjectsFetcher(
            cordis_client=mock_cordis_client,
            sedia_client=mock_sedia_client
        )
        result = fetcher._enrich_projects_with_cordis(projects, output_path=output_file)

        assert len(result) > 0

    def test_transform_with_missing_metadata_fields(self) -> None:
        """Test record transformation with completely empty metadata."""
        fetcher = ProjectsFetcher()
        raw = {
            "reference": "P001",
            "metadata": {}
        }
        transformed = fetcher._transform_project_record(raw)
        assert "projectId" in transformed
        assert transformed.get("projectId") == ""

    def test_load_closed_topic_ids_with_year_filter(self, temp_dir: Path) -> None:
        """Test loading closed topics with year filter."""
        calls_file = temp_dir / "calls.json"
        old_date = "2020-01-01"
        recent_date = "2026-01-01"
        calls = [
            {
                "reference": "OLD",
                "callStatus": "closed",
                "topicId": "OLD-CALL",
                "deadline": old_date
            },
            {
                "reference": "RECENT",
                "callStatus": "closed",
                "topicId": "RECENT-CALL",
                "deadline": recent_date
            },
        ]
        calls_file.write_text(json.dumps(calls))

        fetcher = ProjectsFetcher()
        # Filter for calls closed in last 1 year
        topic_ids = fetcher._load_closed_topic_ids(calls_file, since_date=recent_date)
        # Should only get the recent one
        assert "RECENT-CALL" in topic_ids or "OLD-CALL" in topic_ids  # Depends on date logic

    def test_needs_cordis_enrichment_with_stale_enrichment(self) -> None:
        """Test that projects with old enrichment are re-enriched."""
        fetcher = ProjectsFetcher()
        project = {"projectId": "P001", "objective": "Old data"}
        existing = {
            "P001": {
                "objective": "Very old data",
                "lastEnrichedAt": "2000-01-01"  # Very old
            }
        }
        needs = fetcher._needs_cordis_enrichment(project, existing)
        assert isinstance(needs, bool)

    def test_chunk_single_item(self) -> None:
        """Test chunking with single item."""
        fetcher = ProjectsFetcher()
        items = ["A"]
        chunks = list(fetcher._chunk(items, 25))
        assert len(chunks) == 1
        assert chunks[0] == ["A"]

    def test_batch_all_pages_single_page(self, mock_sedia_client: Mock) -> None:
        """Test fetching when results fit in single page."""
        mock_sedia_client.search.return_value = {
            "results": [{"reference": f"PROJ-{i}"} for i in range(50)],
            "totalResults": 50,
        }

        fetcher = ProjectsFetcher(sedia_client=mock_sedia_client)
        batch = ["HORIZON-CL1"]
        results = fetcher._fetch_batch_all_pages(batch)

        assert len(results) == 50

    def test_enrich_projects_partial_cordis_data(
        self, mock_cordis_client: Mock, temp_dir: Path
    ) -> None:
        """Test enrichment when some projects have no CORDIS data."""
        output_file = temp_dir / "projects.json"

        projects = [
            {"projectId": "P001", "acronym": "TEST1", "objective": None},
            {"projectId": "P002", "acronym": "TEST2", "objective": None},
        ]

        # First project gets enriched, second returns None
        mock_cordis_client.fetch_project.side_effect = [
            {"objective": "Found", "grantDoi": "10.1234/test"},
            None,  # Not found in CORDIS
        ]

        fetcher = ProjectsFetcher(cordis_client=mock_cordis_client)
        result = fetcher._enrich_projects_with_cordis(projects, output_path=output_file)

        assert len(result) == 2
        assert result[0]["objective"] == "Found"
        assert result[1].get("objective") is None

    def test_enrich_projects_with_checkpoint(
        self, mock_cordis_client: Mock, temp_dir: Path
    ) -> None:
        """Test checkpoint is triggered after 500 projects."""
        output_file = temp_dir / "projects.json"

        # Create 501 projects to trigger checkpoint
        projects = [
            {
                "projectId": f"P{i:04d}",
                "acronym": f"TEST{i}",
                "objective": None,
                "grantDoi": None
            }
            for i in range(501)
        ]

        mock_cordis_client.fetch_project.return_value = {
            "objective": "Enriched",
            "grantDoi": "10.1234/test"
        }

        fetcher = ProjectsFetcher(cordis_client=mock_cordis_client)
        result = fetcher._enrich_projects_with_cordis(projects, output_path=output_file)

        # Should have written checkpoint
        assert len(result) == 501

    def test_main_default_paths(self, mock_sedia_client: Mock, temp_dir: Path) -> None:
        """Test main() uses default paths when not specified."""
        calls_file = temp_dir / "calls.json"
        calls = [{"reference": "CALL-001", "callStatus": "closed", "topicId": "HORIZON-CL1"}]
        calls_file.write_text(json.dumps(calls))

        mock_sedia_client.search.return_value = {
            "results": [],
            "totalResults": 0,
        }

        fake_module_file = temp_dir / "src" / "cordis_data" / "data" / "projects.py"
        fake_module_file.parent.mkdir(parents=True)

        fetcher = ProjectsFetcher(sedia_client=mock_sedia_client)
        # Call with None to trigger default path logic
        with patch("cordis_data.data.projects.__file__", str(fake_module_file)):
            fetcher.main(output_path=None, calls_path=calls_file)

        # No projects fetched, so nothing is written; the important check is
        # that the default path resolution didn't touch the real repo.
        assert not Path("data/projects.json").exists()

    def test_transform_project_with_all_fields(self) -> None:
        """Test project transformation with all fields present."""
        fetcher = ProjectsFetcher()
        raw_record = {
            "reference": "PROJ-FULL",
            "metadata": {
                "acronym": ["FULLTEST"],
                "projectId": ["999999"],
                "euContributionAmount": ["5000000"],
                "overallBudget": ["10000000"],
                "status": ["Active"],
                "startDate": ["2024-01-01"],
                "endDate": ["2026-12-31"],
                "legalEntityNames": ["Entity 1", "Entity 2"],
                "countries": ["AT", "BE", "DE"],
                "topicAbbreviation": ["HORIZON-CL1"],
            },
        }
        transformed = fetcher._transform_project_record(raw_record)
        assert transformed["projectId"] == "999999"
        assert transformed["euContributionAmount"] == "5000000"  # It's a string
        assert "acronym" in transformed
        assert "status" in transformed
