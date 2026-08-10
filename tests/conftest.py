"""Shared pytest fixtures for all tests."""

import json
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest

from cordis_data.api.cordis import CordisClient
from cordis_data.api.rate_limiter import TokenBucket
from cordis_data.api.sedia import SediaClient


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_sedia_client() -> Mock:
    """Provide a mocked SEDIA client."""
    client = MagicMock(spec=SediaClient)
    client.search = MagicMock(
        return_value={
            "results": [],
            "totalResults": 0,
        }
    )
    return client


@pytest.fixture
def mock_cordis_client() -> Mock:
    """Provide a mocked CORDIS client."""
    client = MagicMock(spec=CordisClient)
    client.fetch_project = MagicMock(return_value=None)
    return client


@pytest.fixture
def mock_rate_limiter() -> Mock:
    """Provide a mocked TokenBucket."""
    limiter = MagicMock(spec=TokenBucket)
    limiter.acquire = MagicMock()
    return limiter


@pytest.fixture
def sample_sedia_call() -> dict[str, Any]:
    """Sample SEDIA API call response."""
    return {
        "reference": "HORIZON-CL4-2024-DIGITAL-EMERGING-01",
        "metadata": {
            "identifier": ["HORIZON-CL4-2024-DIGITAL-EMERGING-01"],
            "title": ["Sample Call Title"],
            "status": ["31094502"],
            "callIdentifier": ["HE-CL4-2024-DIGITAL"],
            "actions": [
                json.dumps({
                    "types": [{"typeOfAction": "Research and Innovation Action"}],
                    "submissionProcedure": {"abbreviation": "two-stage"},
                    "deadlineDates": ["2024-12-31"],
                })
            ],
            "frameworkProgramme": ["43108390"],
            "keywords": ["AI", "digital", "innovation"],
        },
    }


@pytest.fixture
def sample_cordis_project() -> dict[str, Any]:
    """Sample CORDIS API project response."""
    return {
        "objective": "This project aims to develop AI solutions",
        "identifiers": {
            "grantDoi": "10.1234/example.doi",
        },
    }


@pytest.fixture
def sample_call_record() -> dict[str, Any]:
    """Sample transformed Call record."""
    return {
        "reference": "HORIZON-CL4-2024-DIGITAL-EMERGING-01",
        "topicId": "HORIZON-CL4-2024-DIGITAL-EMERGING-01",
        "title": "Sample Call Title",
        "programme": "Horizon Europe",
        "programmeId": "43108390",
        "cluster": "CL4",
        "callIdentifier": "HE-CL4-2024-DIGITAL",
        "actionType": "RIA",
        "deadline": "2024-12-31",
        "stage": "two-stage",
        "callStatus": "open",
        "budgetMin": None,
        "budgetMax": None,
        "expectedGrants": None,
        "keywords": "AI, digital, innovation",
        "portalUrl": "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/horizon-cl4-2024-digital-emerging-01",
    }


@pytest.fixture
def sample_project_record() -> dict[str, Any]:
    """Sample transformed Project record."""
    return {
        "topicId": "HORIZON-CL4-2024-DIGITAL-EMERGING-01",
        "acronym": "EXAMPLE",
        "projectId": "123456",
        "euContributionAmount": 1000000,
        "overallBudget": 1500000,
        "status": "Active",
        "startDate": "2024-01-01",
        "endDate": "2025-12-31",
        "legalEntityNames": ["University of Example"],
        "countries": ["ES"],
        "objective": "This project aims to develop AI solutions",
        "grantDoi": "10.1234/example.doi",
        "lastEnrichedAt": "2024-08-09",
    }
