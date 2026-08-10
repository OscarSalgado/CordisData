"""Tests for ClosedCallsFetcher (historical closed calls)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cordis_data.data.closed_calls import ClosedCallsFetcher


@pytest.fixture
def mock_sedia_client() -> MagicMock:
    """Create a mock SEDIA client."""
    return MagicMock()


@pytest.fixture
def closed_calls_fetcher(mock_sedia_client: MagicMock) -> ClosedCallsFetcher:
    """Create a ClosedCallsFetcher with mock client."""
    return ClosedCallsFetcher(sedia_client=mock_sedia_client)


def test_closed_calls_fetcher_initialization(mock_sedia_client: MagicMock) -> None:
    """Test ClosedCallsFetcher initializes correctly."""
    fetcher = ClosedCallsFetcher(sedia_client=mock_sedia_client)
    assert fetcher.sedia_client == mock_sedia_client


def test_build_query_closed_calls(closed_calls_fetcher: ClosedCallsFetcher) -> None:
    """Test query building for closed calls (status 31094503)."""
    query = closed_calls_fetcher._build_query()

    assert "bool" in query
    assert "must" in query["bool"]
    must_clauses = query["bool"]["must"]

    # Should have type and status filters
    status_clause = [c for c in must_clauses if "terms" in c and "status" in c["terms"]]
    assert len(status_clause) == 1
    # Should only include closed
    assert status_clause[0]["terms"]["status"] == ["31094503"]


def test_build_query_with_until_date(closed_calls_fetcher: ClosedCallsFetcher) -> None:
    """Test query includes date filter when provided."""
    until_date = "2026-05-01T23:59:59.999Z"
    query = closed_calls_fetcher._build_query(until_date=until_date)

    must_clauses = query["bool"]["must"]
    date_clause = [c for c in must_clauses if "range" in c and "startDate" in c["range"]]
    assert len(date_clause) == 1
    assert date_clause[0]["range"]["startDate"]["lte"] == until_date


def test_transform_record(closed_calls_fetcher: ClosedCallsFetcher) -> None:
    """Test record transformation for closed call."""
    raw_record = {
        "reference": "CLOSED-REF-001",
        "metadata": {
            "identifier": ["HORIZON-2024-01"],
            "title": ["Closed Call"],
            "status": ["31094503"],
            "frameworkProgramme": ["H2020"],
        }
    }

    transformed = closed_calls_fetcher._transform_record(raw_record)

    assert transformed["reference"] == "CLOSED-REF-001"
    assert transformed["topicId"] == "HORIZON-2024-01"
    assert transformed["title"] == "Closed Call"
    assert transformed["callStatus"] == "closed"


def test_main_fetches_and_writes(
    closed_calls_fetcher: ClosedCallsFetcher,
    tmp_path: Path
) -> None:
    """Test main() fetches closed calls and writes to file."""
    output_path = tmp_path / "calls.closed.json"

    # Mock API response
    closed_calls_fetcher.sedia_client.search.return_value = {
        "results": [
            {
                "reference": "CLOSED-REF-001",
                "metadata": {
                    "identifier": ["HORIZON-2024-01"],
                    "title": ["Closed Call"],
                    "status": ["31094503"],
                    "frameworkProgramme": ["H2020"],
                }
            }
        ],
        "totalResults": 1
    }

    with patch("cordis_data.data.closed_calls.load_metadata") as mock_load:
        mock_load.return_value = {
            "calls_closed_fetched_at": None,
            "calls_closed_freshness_ttl_days": 7
        }

        with patch("cordis_data.data.closed_calls.save_metadata"):
            closed_calls_fetcher.main(output_path=output_path, force=True)

    # Verify output file was created
    assert output_path.exists()

    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 1
    assert data[0]["reference"] == "CLOSED-REF-001"
    assert data[0]["callStatus"] == "closed"
