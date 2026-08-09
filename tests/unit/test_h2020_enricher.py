"""Tests for H2020Enricher."""

from unittest.mock import Mock

from cordis_data.data.h2020 import H2020Enricher


class TestH2020Enricher:
    """Tests for H2020Enricher class."""

    def test_init_default(self) -> None:
        """Test H2020Enricher initialization."""
        enricher = H2020Enricher()
        assert enricher.cordis_client is not None
        assert enricher.h2020_index == {}

    def test_init_with_client(self) -> None:
        """Test initialization with provided client."""
        client = Mock()
        enricher = H2020Enricher(cordis_client=client)
        assert enricher.cordis_client == client

    def test_load_index_success(self) -> None:
        """Test successful index loading."""
        mock_client = Mock()
        mock_client.fetch_h2020_projects.return_value = [
            {
                "id": "H2020-001",
                "acronym": "PROJECT-A",
                "organisations": [{"name": "Org-A", "country": "DE", "role": "coordinator"}],
                "keywords": ["ai", "ml"],
            },
            {
                "id": "H2020-002",
                "acronym": "PROJECT-B",
                "organisations": [{"name": "Org-B", "country": "FR", "role": "partner"}],
                "keywords": ["blockchain"],
            },
        ]

        enricher = H2020Enricher(cordis_client=mock_client)
        result = enricher.load_index()

        assert result is True
        assert len(enricher.h2020_index) == 2
        assert "H2020-001" in enricher.h2020_index

    def test_load_index_failure(self) -> None:
        """Test index load failure (graceful degradation)."""
        mock_client = Mock()
        mock_client.fetch_h2020_projects.side_effect = Exception("API error")

        enricher = H2020Enricher(cordis_client=mock_client)
        result = enricher.load_index()

        assert result is False

    def test_match_by_projectid(self) -> None:
        """Test direct projectId match (confidence 0.99)."""
        enricher = H2020Enricher()
        enricher.h2020_index = {
            "H2020-001": {
                "id": "H2020-001",
                "acronym": "PROJECT-A",
                "organisations": [],
                "publications": [],
                "datasets": [],
                "keywords": [],
            }
        }

        horizon_project = {"projectId": "H2020-001", "acronym": "test"}
        match = enricher._match_by_projectid(horizon_project)

        assert match is not None
        assert match.confidence == 0.99
        assert match.strategy == "projectId_exact"

    def test_match_by_acronym(self) -> None:
        """Test acronym exact match (confidence 0.95)."""
        enricher = H2020Enricher()
        enricher.h2020_by_acronym = {
            "project-a": {
                "id": "H2020-001",
                "acronym": "PROJECT-A",
                "organisations": [],
                "publications": [],
                "datasets": [],
                "keywords": [],
            }
        }

        horizon_project = {"acronym": "PROJECT-A"}
        match = enricher._match_by_acronym(horizon_project)

        assert match is not None
        assert match.confidence == 0.95

    def test_match_by_team_overlap(self) -> None:
        """Test team overlap matching (3+ orgs)."""
        enricher = H2020Enricher()
        enricher.h2020_index = {
            "H2020-001": {
                "id": "H2020-001",
                "acronym": "PROJECT-A",
                "organisations": [
                    {"name": "Org-A", "country": "DE", "role": "coordinator"},
                    {"name": "Org-B", "country": "FR", "role": "partner"},
                    {"name": "Org-C", "country": "IT", "role": "partner"},
                    {"name": "Org-D", "country": "ES", "role": "partner"},
                ],
                "publications": [],
                "datasets": [],
                "keywords": [],
            }
        }

        horizon_project = {
            "acronym": "test",
            "legalEntityNames": [
                {"name": "Org-A"},
                {"name": "Org-B"},
                {"name": "Org-C"},
            ],
        }

        match = enricher._match_by_team_overlap(horizon_project)

        assert match is not None
        assert match.confidence >= 0.75

    def test_no_match_found(self) -> None:
        """Test when no match is found."""
        enricher = H2020Enricher()
        enricher.h2020_index = {
            "H2020-001": {
                "id": "H2020-001",
                "acronym": "PROJECT-A",
                "organisations": [],
                "publications": [],
                "datasets": [],
                "keywords": ["ai"],
            }
        }

        horizon_project = {
            "projectId": "OTHER-ID",
            "acronym": "COMPLETELY-DIFFERENT",
            "legalEntityNames": [],
            "keywords": "biology",
        }

        result = enricher.enrich(horizon_project)
        assert result is None

    def test_enrich_with_match(self) -> None:
        """Test enrichment when match is found."""
        enricher = H2020Enricher()
        enricher.h2020_index = {
            "H2020-001": {
                "id": "H2020-001",
                "acronym": "PROJECT-A",
                "organisations": [{"name": "Org-A", "country": "DE", "role": "coordinator"}],
                "publications": [{"title": "Paper 1", "doi": "10.xxxx/1", "url": ""}],
                "datasets": [{"title": "Dataset 1", "doi": "10.xxxx/2", "url": ""}],
                "keywords": ["ai"],
            }
        }

        horizon_project = {"projectId": "H2020-001", "acronym": "test"}
        result = enricher.enrich(horizon_project)

        assert result is not None
        assert result["projectId"] == "H2020-001"
        assert result["matchConfidence"] == 0.99
        assert len(result["organisations"]) == 1
        assert len(result["publications"]) == 1

    def test_keyword_matching(self) -> None:
        """Test keyword overlap matching."""
        enricher = H2020Enricher()
        enricher.h2020_index = {
            "H2020-001": {
                "id": "H2020-001",
                "acronym": "PROJECT-A",
                "organisations": [],
                "publications": [],
                "datasets": [],
                "keywords": ["ai", "machine-learning", "nlp"],
            }
        }

        horizon_project = {
            "projectId": "OTHER",
            "acronym": "different",
            "legalEntityNames": [],
            "keywords": "ai,nlp,blockchain",
        }

        match = enricher._match_by_keywords(horizon_project)

        assert match is not None
        assert match.confidence >= 0.60
