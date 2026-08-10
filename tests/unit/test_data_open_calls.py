"""Tests for OpenCallsFetcher (active calls)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cordis_data.data.open_calls import OpenCallsFetcher


@pytest.fixture
def mock_sedia_client() -> MagicMock:
    """Create a mock SEDIA client."""
    return MagicMock()


@pytest.fixture
def open_calls_fetcher(mock_sedia_client: MagicMock) -> OpenCallsFetcher:
    """Create an OpenCallsFetcher with mock client."""
    return OpenCallsFetcher(sedia_client=mock_sedia_client)


def test_open_calls_fetcher_initialization(mock_sedia_client: MagicMock) -> None:
    """Test OpenCallsFetcher initializes correctly."""
    fetcher = OpenCallsFetcher(sedia_client=mock_sedia_client)
    assert fetcher.sedia_client == mock_sedia_client


def test_build_query_open_calls(open_calls_fetcher: OpenCallsFetcher) -> None:
    """Test query building for open calls (status 31094501, 31094502)."""
    query = open_calls_fetcher._build_query()

    assert "bool" in query
    assert "must" in query["bool"]
    must_clauses = query["bool"]["must"]

    # Should have type and status filters
    status_clause = [c for c in must_clauses if "terms" in c and "status" in c["terms"]]
    assert len(status_clause) == 1
    # Should only include open and forthcoming
    assert set(status_clause[0]["terms"]["status"]) == {"31094501", "31094502"}


def test_build_query_with_since_date(open_calls_fetcher: OpenCallsFetcher) -> None:
    """Test query includes date filter when provided."""
    since_date = "2026-06-01T00:00:00.000Z"
    query = open_calls_fetcher._build_query(since_date=since_date)

    must_clauses = query["bool"]["must"]
    date_clause = [c for c in must_clauses if "range" in c and "startDate" in c["range"]]
    assert len(date_clause) == 1
    assert date_clause[0]["range"]["startDate"]["gte"] == since_date


def test_transform_record(open_calls_fetcher: OpenCallsFetcher) -> None:
    """Test record transformation."""
    raw_record = {
        "reference": "REF-001",
        "metadata": {
            "identifier": ["HORIZON-CL5-2026-01"],
            "title": ["Test Call"],
            "status": ["31094502"],
            "frameworkProgramme": ["H2020"],
            "keywords": ["AI", "ML"],
        }
    }

    transformed = open_calls_fetcher._transform_record(raw_record)

    assert transformed["reference"] == "REF-001"
    assert transformed["topicId"] == "HORIZON-CL5-2026-01"
    assert transformed["title"] == "Test Call"
    assert transformed["callStatus"] == "open"
    assert transformed["cluster"] == "CL5"


def test_main_fetches_and_writes(
    open_calls_fetcher: OpenCallsFetcher,
    tmp_path: Path
) -> None:
    """Test main() fetches calls and writes to file."""
    output_path = tmp_path / "calls.open.json"

    # Mock API response
    open_calls_fetcher.sedia_client.search.return_value = {
        "results": [
            {
                "reference": "REF-001",
                "metadata": {
                    "identifier": ["HORIZON-2026-01"],
                    "title": ["Test Call"],
                    "status": ["31094502"],
                    "frameworkProgramme": ["H2020"],
                }
            }
        ],
        "totalResults": 1
    }

    with patch("cordis_data.data.open_calls.load_metadata") as mock_load:
        mock_load.return_value = {
            "calls_open_fetched_at": None,
            "calls_open_freshness_ttl_days": 3
        }

        with patch("cordis_data.data.open_calls.save_metadata"):
            open_calls_fetcher.main(output_path=output_path, force=True)

    # Verify output file was created
    assert output_path.exists()

    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 1
    assert data[0]["reference"] == "REF-001"
    assert data[0]["callStatus"] == "open"
