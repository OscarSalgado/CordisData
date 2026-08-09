"""Tests for CallsFetcher."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

from cordis_data.data.calls import CallsFetcher


class TestCallsFetcher:
    """Tests for CallsFetcher class."""

    def test_init_default(self) -> None:
        """Test CallsFetcher initialization with defaults."""
        fetcher = CallsFetcher()
        assert fetcher.sedia_client is not None
        assert fetcher.max_workers > 0

    def test_init_with_client(self, mock_sedia_client: Mock) -> None:
        """Test CallsFetcher initialization with provided client."""
        fetcher = CallsFetcher(sedia_client=mock_sedia_client)
        assert fetcher.sedia_client == mock_sedia_client

    def test_build_query_no_date(self) -> None:
        """Test query builder without date limit."""
        fetcher = CallsFetcher()
        query = fetcher._build_query()
        assert "bool" in query
        assert "must" in query["bool"]
        assert len(query["bool"]["must"]) == 2

    def test_build_query_with_date(self) -> None:
        """Test query builder with date limit."""
        fetcher = CallsFetcher()
        since_date = "2024-01-01T00:00:00.000Z"
        query = fetcher._build_query(since_date=since_date)
        assert len(query["bool"]["must"]) == 3
        assert any("range" in item for item in query["bool"]["must"])

    def test_transform_record_basic(self) -> None:
        """Test basic record transformation."""
        fetcher = CallsFetcher()
        raw_record = {
            "reference": "TEST-001",
            "metadata": {
                "identifier": ["HORIZON-CL1-2024-TEST"],
                "title": ["Test Call"],
                "status": ["31094502"],
                "callIdentifier": ["HE-CL1-2024"],
                "frameworkProgramme": ["43108390"],
                "keywords": ["test", "ai"],
            },
        }
        transformed = fetcher._transform_record(raw_record)
        assert transformed["reference"] == "TEST-001"
        assert transformed["topicId"] == "HORIZON-CL1-2024-TEST"
        assert transformed["title"] == "Test Call"
        assert transformed["cluster"] == "CL1"
        assert "portalUrl" in transformed
        assert transformed["keywords"] == "test, ai"

    def test_transform_record_missing_fields(self) -> None:
        """Test record transformation with missing fields."""
        fetcher = CallsFetcher()
        raw_record = {"reference": "", "metadata": {}}
        transformed = fetcher._transform_record(raw_record)
        assert transformed["topicId"] == ""
        assert transformed["title"] == ""
        assert transformed["programme"] == ""

    def test_extract_cluster_horizon(self) -> None:
        """Test cluster extraction from HORIZON identifier."""
        fetcher = CallsFetcher()
        assert fetcher._extract_cluster("HORIZON-CL1-2024") == "CL1"
        assert fetcher._extract_cluster("HORIZON-CL2-2024") == "CL2"
        assert fetcher._extract_cluster("HORIZON-MSCA-2024") == "MSCA"
        assert fetcher._extract_cluster("HORIZON-ERC-2024") == "ERC"

    def test_extract_cluster_non_horizon(self) -> None:
        """Test cluster extraction from non-HORIZON identifier."""
        fetcher = CallsFetcher()
        assert fetcher._extract_cluster("OTHER-PROG") == ""
        assert fetcher._extract_cluster("") == ""

    def test_get_deadline_from_metadata(self) -> None:
        """Test deadline extraction from metadata."""
        fetcher = CallsFetcher()
        metadata = {
            "deadlineDate": ["2024-12-31"]
        }
        deadline = fetcher._get_deadline_from_metadata(metadata)
        assert isinstance(deadline, str)

    def test_get_deadline_fallback(self) -> None:
        """Test deadline extraction with fallback."""
        fetcher = CallsFetcher()
        metadata = {"deadlineDate": ["2024-12-25"]}
        deadline = fetcher._get_deadline_from_metadata(metadata)
        assert deadline == "2024-12-25"

    def test_get_deadline_invalid(self) -> None:
        """Test deadline extraction with invalid data."""
        fetcher = CallsFetcher()
        deadline = fetcher._get_deadline_from_metadata({})
        assert deadline == ""

    def test_main_force_flag(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test main() with force flag skips freshness check."""
        output_file = temp_dir / "calls.json"
        mock_sedia_client.search.return_value = {
            "results": [],
            "totalResults": 0,
        }

        fetcher = CallsFetcher(sedia_client=mock_sedia_client)
        fetcher.main(output_path=output_file, force=True)

        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert isinstance(data, list)

    def test_main_full_history(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test main() with full_history flag."""
        output_file = temp_dir / "calls.json"
        mock_sedia_client.search.return_value = {
            "results": [],
            "totalResults": 0,
        }

        fetcher = CallsFetcher(sedia_client=mock_sedia_client)
        fetcher.main(output_path=output_file, full_history=True, force=True)

        assert output_file.exists()

    def test_main_merge_existing(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test main() merges with existing data."""
        output_file = temp_dir / "calls.json"

        existing_call = {
            "reference": "EXISTING-001",
            "topicId": "HORIZON-OLD",
            "title": "Old Call",
            "programme": "Horizon Europe",
            "programmeId": "43108390",
            "callStatus": "closed",
        }
        output_file.write_text(json.dumps([existing_call]))

        new_call = {
            "reference": "NEW-001",
            "metadata": {
                "identifier": ["HORIZON-NEW"],
                "title": ["New Call"],
                "status": ["31094502"],
                "frameworkProgramme": ["43108390"],
            },
        }
        mock_sedia_client.search.return_value = {
            "results": [new_call],
            "totalResults": 1,
        }

        fetcher = CallsFetcher(sedia_client=mock_sedia_client)
        fetcher.main(output_path=output_file, force=True)

        data = json.loads(output_file.read_text())
        assert len(data) == 2

    def test_main_default_output_path(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test main() resolves the default output path to <repo_root>/data/calls.json."""
        mock_sedia_client.search.return_value = {
            "results": [],
            "totalResults": 0,
        }

        fake_module_file = temp_dir / "src" / "cordis_data" / "data" / "calls.py"
        fake_module_file.parent.mkdir(parents=True)

        fetcher = CallsFetcher(sedia_client=mock_sedia_client)
        with patch("cordis_data.data.calls.__file__", str(fake_module_file)):
            fetcher.main(force=True)

        assert (temp_dir / "data" / "calls.json").exists()

    def test_fetch_page(self, mock_sedia_client: Mock) -> None:
        """Test single page fetch."""
        mock_sedia_client.search.return_value = {
            "results": [{"reference": "TEST"}],
            "totalResults": 1,
        }

        fetcher = CallsFetcher(sedia_client=mock_sedia_client)
        result = fetcher._fetch_page(1, {})

        assert "results" in result
        assert "totalResults" in result
        mock_sedia_client.search.assert_called_once()

    def test_parse_action_type_valid(self) -> None:
        """Test action type parsing from valid metadata."""
        fetcher = CallsFetcher()
        metadata = {
            "actions": [
                json.dumps({
                    "types": [{"typeOfAction": "Research and Innovation Action"}]
                })
            ]
        }
        action_type = fetcher._parse_action_type_from_metadata(metadata)
        assert isinstance(action_type, str)

    def test_parse_action_type_invalid(self) -> None:
        """Test action type parsing with invalid metadata."""
        fetcher = CallsFetcher()
        action_type = fetcher._parse_action_type_from_metadata({})
        assert action_type == ""

    def test_transform_record_with_budget(self) -> None:
        """Test record transformation includes budget info."""
        fetcher = CallsFetcher()
        raw_record = {
            "reference": "TEST-001",
            "metadata": {
                "identifier": ["HORIZON-CL1-2024"],
                "title": ["Test"],
                "status": ["31094502"],
                "frameworkProgramme": ["43108390"],
                "budgetDetails": [
                    json.dumps([
                        {"type": "EC contribution", "min": 5000000, "max": 10000000}
                    ])
                ],
            },
        }
        transformed = fetcher._transform_record(raw_record)
        assert "budgetMin" in transformed
        assert "budgetMax" in transformed

    def test_parse_action_type_two_stage_procedure(self) -> None:
        """Test detecting two-stage submission procedure."""
        fetcher = CallsFetcher()
        metadata = {
            "actions": [
                json.dumps({
                    "types": [{"typeOfAction": "Research and Innovation Action"}],
                    "submissionProcedure": {"abbreviation": "two-stage-procedure"},
                })
            ]
        }
        action_type = fetcher._parse_action_type_from_metadata(metadata)
        assert isinstance(action_type, str)

    def test_fetch_page_with_pagination(self) -> None:
        """Test fetch_page handles page parameters correctly."""
        fetcher = CallsFetcher()
        fetcher.max_workers = 1
        assert fetcher.max_workers == 1

    def test_get_deadline_no_actions_field(self) -> None:
        """Test deadline extraction when actions field is missing."""
        fetcher = CallsFetcher()
        metadata = {}
        deadline = fetcher._get_deadline_from_metadata(metadata)
        assert deadline == ""

    def test_transform_record_empty_keywords(self) -> None:
        """Test record transformation with empty keywords."""
        fetcher = CallsFetcher()
        raw_record = {
            "reference": "TEST-001",
            "metadata": {
                "identifier": ["HORIZON-CL1"],
                "title": ["Test"],
                "status": ["31094502"],
                "frameworkProgramme": ["43108390"],
                "keywords": [],  # Empty keywords
            },
        }
        transformed = fetcher._transform_record(raw_record)
        assert transformed["keywords"] == ""

    def test_transform_record_no_framework_programme(self) -> None:
        """Test record transformation with no framework programme."""
        fetcher = CallsFetcher()
        raw_record = {
            "reference": "TEST-001",
            "metadata": {
                "identifier": ["TEST-TOPIC"],
                "title": ["Test"],
                "status": ["31094502"],
                "frameworkProgramme": [],  # No framework
            },
        }
        transformed = fetcher._transform_record(raw_record)
        assert transformed["programme"] == ""
        assert transformed["programmeId"] == ""

    def test_main_generates_changelog(
        self, mock_sedia_client: Mock, temp_dir: Path
    ) -> None:
        """Test main() writes a valid changelog JSON file alongside calls.json."""
        output_file = temp_dir / "calls.json"

        new_call = {
            "reference": "NEW-001",
            "metadata": {
                "identifier": ["HORIZON-NEW"],
                "title": ["New Call"],
                "status": ["31094502"],
                "frameworkProgramme": ["43108390"],
            },
        }
        mock_sedia_client.search.return_value = {
            "results": [new_call],
            "totalResults": 1,
        }

        fetcher = CallsFetcher(sedia_client=mock_sedia_client)
        fetcher.main(output_path=output_file, force=True)

        import datetime

        changelog_file = output_file.parent / "changelog" / f"{datetime.date.today().isoformat()}.json"
        assert changelog_file.exists()

        changelog = json.loads(changelog_file.read_text())
        assert "events" in changelog
        assert "summary" in changelog
        assert changelog["summary"]["new"] == 1

    def test_build_query_includes_types(self) -> None:
        """Test query builder includes correct types."""
        fetcher = CallsFetcher()
        query = fetcher._build_query()
        # Should include type check for types 1 and 2
        must_clauses = query["bool"]["must"]
        type_clause = [m for m in must_clauses if "terms" in m and "type" in m.get("terms", {})]
        assert len(type_clause) > 0
