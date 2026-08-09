"""H2020 project enrichment for Horizon projects."""

import difflib
from typing import Any, Optional

from cordis_data.api.cordis import CordisClient


class H2020Match:
    """Result of H2020 matching."""

    def __init__(
        self,
        project_id: str,
        acronym: str,
        confidence: float,
        strategy: str,
        organisations: list[dict[str, str]],
        publications: list[dict[str, str]],
        datasets: list[dict[str, str]],
        keywords: list[str],
    ) -> None:
        """Initialize match result."""
        self.project_id = project_id
        self.acronym = acronym
        self.confidence = confidence
        self.strategy = strategy
        self.organisations = organisations
        self.publications = publications
        self.datasets = datasets
        self.keywords = keywords


class H2020Enricher:
    """Enrich Horizon projects with H2020 metadata and lineage."""

    def __init__(self, cordis_client: Optional[CordisClient] = None) -> None:
        """Initialize H2020Enricher.

        Args:
            cordis_client: CordisClient for fetching H2020 data (default: creates one)
        """
        self.cordis_client = cordis_client or CordisClient()
        self.h2020_index: dict[str, dict[str, Any]] = {}
        self.h2020_by_acronym: dict[str, dict[str, Any]] = {}
        self.h2020_by_organisations: dict[str, list[str]] = {}

    def load_index(self) -> bool:
        """Load all H2020 projects into memory.

        Returns:
            True if load successful, False if error (graceful degradation)
        """
        try:
            # Fetch all H2020 projects from CORDIS H2020 API
            all_projects = self.cordis_client.fetch_h2020_projects()
            if not all_projects:
                return False

            # Build indices
            for proj in all_projects:
                proj_id = proj.get("id", "")
                if not proj_id:
                    continue

                self.h2020_index[proj_id] = proj

                # Index by acronym
                acronym = (proj.get("acronym") or "").lower().strip()
                if acronym:
                    self.h2020_by_acronym[acronym] = proj

                # Index by organisations
                for org in proj.get("organisations", []):
                    org_name = org.get("name", "").lower().strip()
                    if org_name:
                        if org_name not in self.h2020_by_organisations:
                            self.h2020_by_organisations[org_name] = []
                        self.h2020_by_organisations[org_name].append(proj_id)

            return len(self.h2020_index) > 0
        except Exception:
            return False

    def enrich(self, horizon_project: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Try to find and match a Horizon project to H2020 data.

        Returns:
            Dict with h2020_related data if match found, None otherwise
        """
        if not self.h2020_index:
            return None

        match = self._find_best_match(horizon_project)
        if not match:
            return None

        return {
            "projectId": match.project_id,
            "acronym": match.acronym,
            "matchConfidence": match.confidence,
            "matchStrategy": match.strategy,
            "organisations": match.organisations,
            "publications": match.publications,
            "datasets": match.datasets,
            "keywords": match.keywords,
        }

    def _find_best_match(self, horizon_project: dict[str, Any]) -> Optional[H2020Match]:
        """Try multiple strategies, return best match."""
        strategies = [
            self._match_by_projectid(horizon_project),
            self._match_by_acronym(horizon_project),
            self._match_by_team_overlap(horizon_project),
            self._match_by_title_similarity(horizon_project),
            self._match_by_keywords(horizon_project),
        ]

        matches = [m for m in strategies if m]
        if not matches:
            return None

        # Return highest confidence match
        return max(matches, key=lambda m: m.confidence)

    def _match_by_projectid(self, horizon_project: dict[str, Any]) -> Optional[H2020Match]:
        """Direct projectId match (confidence 0.99)."""
        proj_id = horizon_project.get("projectId", "")
        if proj_id in self.h2020_index:
            h2020 = self.h2020_index[proj_id]
            return self._build_match(h2020, "projectId_exact", 0.99)
        return None

    def _match_by_acronym(self, horizon_project: dict[str, Any]) -> Optional[H2020Match]:
        """Acronym exact match (confidence 0.95)."""
        acronym = (horizon_project.get("acronym") or "").lower().strip()
        if not acronym:
            return None

        if acronym in self.h2020_by_acronym:
            h2020 = self.h2020_by_acronym[acronym]
            return self._build_match(h2020, "acronym_exact", 0.95)
        return None

    def _match_by_team_overlap(self, horizon_project: dict[str, Any]) -> Optional[H2020Match]:
        """Team overlap (3+ orgs) with confidence 0.75-0.85."""
        horizon_orgs = set(
            org.get("name", "").lower().strip()
            for org in horizon_project.get("legalEntityNames", [])
        )
        if not horizon_orgs:
            return None

        best_match = None
        best_overlap = 0

        for h2020_proj in self.h2020_index.values():
            h2020_orgs = set(
                org.get("name", "").lower().strip()
                for org in h2020_proj.get("organisations", [])
            )
            overlap = len(horizon_orgs & h2020_orgs)

            if overlap >= 3 and overlap > best_overlap:
                best_overlap = overlap
                best_match = h2020_proj

        if best_match and best_overlap >= 3:
            # Confidence scales with overlap: 0.75 for 3, 0.85 for 5+
            confidence = min(0.75 + (best_overlap - 3) * 0.025, 0.85)
            return self._build_match(best_match, f"team_overlap({best_overlap})", confidence)

        return None

    def _match_by_title_similarity(self, horizon_project: dict[str, Any]) -> Optional[H2020Match]:
        """Title similarity (Levenshtein) + team context."""
        horizon_title = (horizon_project.get("acronym") or "").lower().strip()
        horizon_orgs = set(
            org.get("name", "").lower().strip()
            for org in horizon_project.get("legalEntityNames", [])
        )

        if not horizon_title:
            return None

        best_match = None
        best_ratio = 0.0
        best_overlap = 0

        for h2020_proj in self.h2020_index.values():
            h2020_title = (h2020_proj.get("acronym") or "").lower().strip()
            if not h2020_title:
                continue

            ratio = difflib.SequenceMatcher(None, horizon_title, h2020_title).ratio()
            h2020_orgs = set(
                org.get("name", "").lower().strip() for org in h2020_proj.get("organisations", [])
            )
            overlap = len(horizon_orgs & h2020_orgs)

            # Prefer matches with both title similarity and team overlap
            if ratio > 0.7 and overlap > 0 and ratio > best_ratio:
                best_ratio = ratio
                best_match = h2020_proj
                best_overlap = overlap

        if best_match and best_ratio > 0.7:
            # Confidence scales: 0.70 for weak match, 0.80 for good match
            # Boost confidence if team overlap also exists
            confidence = min(0.70 + (best_ratio - 0.7) * (1 - 0.7) / (1 - 0.7), 0.80)
            if best_overlap > 0:
                confidence = min(confidence + 0.05, 0.80)
            return self._build_match(
                best_match, f"title_similarity({best_ratio:.2f})", confidence
            )

        return None

    def _match_by_keywords(self, horizon_project: dict[str, Any]) -> Optional[H2020Match]:
        """Keyword/subject overlap (2+ matches)."""
        horizon_keywords = set(
            (kw or "").lower().strip()
            for kw in horizon_project.get("keywords", "").split(",")
            if kw.strip()
        )

        if not horizon_keywords:
            return None

        best_match = None
        best_overlap = 0

        for h2020_proj in self.h2020_index.values():
            h2020_keywords = set(
                (kw or "").lower().strip() for kw in h2020_proj.get("keywords", [])
            )
            overlap = len(horizon_keywords & h2020_keywords)

            if overlap >= 2 and overlap > best_overlap:
                best_overlap = overlap
                best_match = h2020_proj

        if best_match and best_overlap >= 2:
            # Confidence scales with overlap: 0.60 for 2, 0.75 for 5+
            confidence = min(0.60 + (best_overlap - 2) * 0.03, 0.75)
            return self._build_match(best_match, f"keywords({best_overlap})", confidence)

        return None

    def _build_match(
        self, h2020_project: dict[str, Any], strategy: str, confidence: float
    ) -> H2020Match:
        """Build a match result from H2020 project data."""
        organisations = [
            {
                "name": org.get("name", ""),
                "country": org.get("country", ""),
                "role": org.get("role", ""),
            }
            for org in h2020_project.get("organisations", [])
        ]

        publications = [
            {"title": pub.get("title", ""), "doi": pub.get("doi", ""), "url": pub.get("url", "")}
            for pub in h2020_project.get("publications", [])
        ]

        datasets = [
            {"title": ds.get("title", ""), "doi": ds.get("doi", ""), "url": ds.get("url", "")}
            for ds in h2020_project.get("datasets", [])
        ]

        return H2020Match(
            project_id=h2020_project.get("id", ""),
            acronym=h2020_project.get("acronym", ""),
            confidence=confidence,
            strategy=strategy,
            organisations=organisations,
            publications=publications,
            datasets=datasets,
            keywords=h2020_project.get("keywords", []),
        )
