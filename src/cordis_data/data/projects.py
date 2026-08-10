"""EU research project fetcher and CORDIS enricher."""

import datetime
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Generator, Optional, TypeVar, cast

from cordis_data.api.cordis import CordisClient
from cordis_data.api.rate_limiter import TokenBucket
from cordis_data.api.sedia import SediaClient
from cordis_data.config import (
    CORDIS_ENRICHMENT_WORKERS,
    CORDIS_RATE_LIMIT,
    CORDIS_TTL_DAYS,
    PROJECTS_API_KEY,
    PROJECTS_BATCH_SIZE,
    SEDIA_API_URL,
)
from cordis_data.utils import merge_projects

T = TypeVar("T")

log = logging.getLogger(__name__)


class ProjectsFetcher:
    """Fetches awarded projects from SEDIA and enriches with CORDIS data.

    Fetches awarded-project data for closed calls from SEDIA_NONH2020_PROD API
    and enriches each project with CORDIS narrative data (objective, grantDoi).

    Dependency injection enables testing without network calls and allows
    customizing rate limiting and API clients.
    """

    def __init__(
        self,
        sedia_client: Optional[SediaClient] = None,
        cordis_client: Optional[CordisClient] = None,
        rate_limiter: Optional[TokenBucket] = None,
    ) -> None:
        """Initialize ProjectsFetcher with optional API clients.

        Args:
            sedia_client: SediaClient instance with PROJECTS_API_KEY
                (default: creates one with SEDIA defaults)
            cordis_client: CordisClient instance for CORDIS enrichment
                (default: creates one with defaults)
            rate_limiter: TokenBucket for CORDIS rate limiting
                (default: creates one with CORDIS_RATE_LIMIT)
        """
        self.sedia_client = sedia_client or SediaClient(
            api_url=SEDIA_API_URL,
            api_key=PROJECTS_API_KEY,
        )
        # Rate limiter: create if not provided (always needed for CORDIS)
        if rate_limiter is None:
            rate_limiter = TokenBucket(rate=CORDIS_RATE_LIMIT)
        self.rate_limiter = rate_limiter

        self.cordis_client = cordis_client or CordisClient(
            rate_limiter=self.rate_limiter,
        )
        self.batch_size = PROJECTS_BATCH_SIZE
        self.enrichment_workers = CORDIS_ENRICHMENT_WORKERS

    def _build_projects_query(self, topic_ids: list[str]) -> dict[str, Any]:
        """Build Elasticsearch query for projects by topic IDs.

        Args:
            topic_ids: List of topic identifiers (topicAbbreviation)

        Returns:
            Query dict for SEDIA API
        """
        return {"bool": {"must": [{"terms": {"topicAbbreviation": topic_ids}}]}}

    def _fetch_projects_batch(self, topic_ids: list[str], page_num: int, retries: int = 3) -> dict[str, Any]:
        """Fetch a single page of projects for a batch of topic IDs.

        Args:
            topic_ids: List of topic identifiers
            page_num: Page number (1-indexed)
            retries: Number of retry attempts

        Returns:
            Response dict with 'results' and 'totalResults'
        """
        query = self._build_projects_query(topic_ids)
        # SEDIA_NONH2020_PROD API doesn't use sort specification
        return self.sedia_client.search(query, {}, page_num, 100, retries)

    def _fetch_batch_all_pages(self, batch: list[str], retries: int = 3) -> list[dict[str, Any]]:
        """Fetch all pages of results for a single batch of topic IDs.

        Kept as one unit of work so concurrency applies across batches while
        each batch's pagination (depends on running total) stays sequential.

        Args:
            batch: List of topic identifiers
            retries: Number of retry attempts

        Returns:
            List of all result dicts across all pages
        """
        page_num = 1
        batch_results: list[dict[str, Any]] = []
        while True:
            data = self._fetch_projects_batch(batch, page_num, retries=retries)
            results = cast(list[dict[str, Any]], data.get("results", []))
            batch_results.extend(results)
            total = int(data.get("totalResults", 0) or 0)
            if len(batch_results) >= total or not results:
                break
            page_num += 1
        return batch_results

    def _transform_project_record(self, r: dict[str, Any]) -> dict[str, Any]:
        """Map one raw SEDIA_NONH2020_PROD result into project record shape.

        Note: SEDIA's "topicId" field is an internal numeric id, not the
        human-readable topic string. "topicAbbreviation" matches calls.json's
        topicId.

        Args:
            r: Raw result dict from API

        Returns:
            Transformed project record dict
        """
        m = r.get("metadata", {})
        return {
            "topicId": (m.get("topicAbbreviation") or [""])[0],
            "acronym": (m.get("acronym") or [""])[0],
            "projectId": (m.get("projectId") or [""])[0],
            "euContributionAmount": (m.get("euContributionAmount") or [None])[0],
            "overallBudget": (m.get("overallBudget") or [None])[0],
            "status": (m.get("status") or [""])[0],
            "startDate": (m.get("startDate") or [""])[0],
            "endDate": (m.get("endDate") or [""])[0],
            "legalEntityNames": m.get("legalEntityNames") or [],
            "countries": m.get("countries") or [],
            "objective": None,
            "grantDoi": None,
            "lastEnrichedAt": "",
        }

    def _needs_cordis_enrichment(
        self,
        project: dict[str, Any],
        existing_by_id: dict[str, dict[str, Any]],
        now: Optional[datetime.date] = None,
    ) -> bool:
        """Check if project needs CORDIS enrichment.

        Returns False only if the project's existing stored record already has
        both objective and grantDoi populated and was enriched within the TTL
        window.

        Args:
            project: Project dict (needs 'projectId')
            existing_by_id: Dict of existing projects keyed by projectId
            now: Reference date (default: today)

        Returns:
            True if enrichment is needed, False otherwise
        """
        if now is None:
            now = datetime.date.today()

        project_id = cast(str, project.get("projectId"))
        existing = existing_by_id.get(project_id)
        if not existing:
            return True
        if not (existing.get("objective") and existing.get("grantDoi")):
            return True

        last_enriched = existing.get("lastEnrichedAt")
        if not last_enriched:
            return True

        try:
            age_days = (now - datetime.date.fromisoformat(last_enriched)).days
            return age_days >= CORDIS_TTL_DAYS
        except (ValueError, TypeError):
            return True

    def _enrich_projects_with_cordis(
        self,
        to_enrich: list[dict[str, Any]],
        output_path: Optional[Path] = None,
    ) -> list[dict[str, Any]]:
        """Enrich projects with CORDIS data using thread pool.

        Writes checkpoints to output_path after every 500 projects enriched.

        Args:
            to_enrich: List of project dicts needing enrichment
            output_path: Optional Path to write checkpoints

        Returns:
            Same list with objective/grantDoi/lastEnrichedAt populated
        """
        enriched_batch = []
        checkpoint_interval = 500

        with ThreadPoolExecutor(max_workers=self.enrichment_workers) as executor:
            future_to_project = {
                executor.submit(self.cordis_client.fetch_project, p["projectId"]): p
                for p in to_enrich
            }
            completed = 0
            for future in as_completed(future_to_project):
                completed += 1
                p = future_to_project[future]
                enrichment = future.result()
                if enrichment:
                    p["objective"] = enrichment["objective"]
                    p["grantDoi"] = enrichment["grantDoi"]
                p["lastEnrichedAt"] = datetime.date.today().isoformat()

                enriched_batch.append(p)

                # Checkpoint: write every checkpoint_interval enriched projects
                if len(enriched_batch) >= checkpoint_interval and output_path:
                    self._write_and_merge_projects(
                        enriched_batch,
                        output_path,
                        batch_num=(completed // checkpoint_interval),
                        total_batches=(len(to_enrich) // checkpoint_interval) + 1,
                    )
                    enriched_batch = []

                if completed % 20 == 0:
                    print(f"  CORDIS-enriched {completed}/{len(to_enrich)}", flush=True)

            # Final checkpoint for remaining projects
            if enriched_batch and output_path:
                self._write_and_merge_projects(enriched_batch, output_path)

        return to_enrich

    def _write_and_merge_projects(
        self,
        new_projects: list[dict[str, Any]],
        output_path: Path,
        batch_num: Optional[int] = None,
        total_batches: Optional[int] = None,
    ) -> tuple[int, int]:
        """Write projects to output_path, merging with existing data by projectId.

        Args:
            new_projects: List of project dicts to write
            output_path: Path to projects.json
            batch_num: Current batch number (for progress display)
            total_batches: Total number of batches (for progress display)

        Returns:
            Tuple of (projects_written_this_batch, total_projects_after_merge)
        """
        # Load existing projects if they exist
        existing_projects = []
        if output_path.exists():
            with open(output_path, "r", encoding="utf-8") as f:
                existing_projects = json.load(f)

        # Merge by projectId
        merged_by_id = merge_projects(existing_projects, new_projects)
        merged_projects = sorted(merged_by_id.values(), key=lambda p: p.get("topicId") or "")

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(merged_projects, f, separators=(",", ":"), ensure_ascii=False)

        # Log progress
        if batch_num is not None and total_batches is not None:
            pct = int(100.0 * len(merged_projects) / max(1, 3825))  # Rough estimate
            print(f"  Batch {batch_num}/{total_batches} done: {len(new_projects)} projects written | "
                  f"Total: {len(merged_projects)}/3825 ({pct}%)", flush=True)

        return len(new_projects), len(merged_projects)

    def _chunk(self, items: list[T], size: int) -> Generator[list[T], None, None]:
        """Yield successive chunks of items.

        Args:
            items: List of items to chunk
            size: Size of each chunk

        Yields:
            Lists of up to 'size' items
        """
        for i in range(0, len(items), size):
            yield items[i:i + size]

    def _load_closed_calls(
        self,
        calls_path: Optional[Path] = None,
    ) -> list[dict[str, Any]]:
        """Load closed calls from calls.closed.json.

        Args:
            calls_path: Path to calls.closed.json (default: data/calls.closed.json)

        Returns:
            List of closed call dicts (already filtered by callStatus="closed")
        """
        if calls_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            calls_path = project_root / "data" / "calls.closed.json"
        else:
            calls_path = Path(calls_path)

        with open(calls_path, "r", encoding="utf-8") as f:
            calls = json.load(f)

        return calls  # Already filtered (closed only)

    def _load_existing_projects(
        self,
        output_path: Path,
    ) -> list[dict[str, Any]]:
        """Load existing projects from projects.json (or return empty list).

        Args:
            output_path: Path to projects.json

        Returns:
            List of project dicts (or empty list if file doesn't exist)
        """
        if not output_path.exists():
            return []

        with open(output_path, "r", encoding="utf-8") as f:
            projects = json.load(f)

        return projects

    def _build_dedup_index(
        self,
        projects: list[dict[str, Any]],
    ) -> dict[tuple[str, str], bool]:
        """Build deduplication index from existing projects.

        Args:
            projects: List of project dicts

        Returns:
            {(topicId, projectId): True, ...} for O(1) lookups
        """
        index = {}
        for p in projects:
            key = (p.get("topicId") or "", p.get("projectId") or "")
            index[key] = True

        return index

    def _fetch_projects_for_single_topic(
        self,
        topic_id: str,
    ) -> list[dict[str, Any]]:
        """Fetch projects from SEDIA for a single topicId.

        Args:
            topic_id: Topic identifier (topicAbbreviation or topicId)

        Returns:
            List of raw project dicts from SEDIA (or empty list if none found)
        """
        query = self._build_projects_query([topic_id])
        response = self.sedia_client.search(query, {}, 1, 10000, retries=3)
        return response.get("results", [])

    def _enrich_with_cordis(
        self,
        project: dict[str, Any],
    ) -> dict[str, Any]:
        """Enrich single project with CORDIS data (objective, grantDoi).

        Args:
            project: Project dict from SEDIA

        Returns:
            Enriched project dict (with objective and grantDoi added if available)
        """
        project_id = project.get("projectId")
        if not project_id:
            return project

        try:
            enrichment = self.cordis_client.fetch_project(project_id)
            if enrichment:
                project["objective"] = enrichment.get("objective")
                project["grantDoi"] = enrichment.get("grantDoi")
        except Exception as e:
            log.warning(f"CORDIS enrichment failed for {project_id}: {e}")
            # Partial enrichment is OK; continue without these fields

        project["lastEnrichedAt"] = datetime.date.today().isoformat()
        return project

    def main(
        self,
        output_path: Optional[Path] = None,
        calls_path: Optional[Path] = None,
    ) -> None:
        """Fetch and enrich projects for closed calls (rolling 1-year window).

        Fetches projects from SEDIA for closed calls with deadline within last 1 year,
        deduplicates by (topicId, projectId), and enriches with CORDIS data.

        Args:
            output_path: Path to write projects.json (default: data/projects.json)
            calls_path: Path to calls.closed.json (default: data/calls.closed.json)
        """
        if output_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            output_path = project_root / "data" / "projects.json"
        else:
            output_path = Path(output_path)

        # Load closed calls and existing projects
        closed_calls = self._load_closed_calls(calls_path)
        projects_existing = self._load_existing_projects(output_path)
        dedup_index = self._build_dedup_index(projects_existing)

        print(f"Found {len(closed_calls)} closed calls", flush=True)
        print(f"Existing projects: {len(projects_existing)}", flush=True)

        # Rolling window: 1 year
        one_year_ago = (datetime.date.today() - datetime.timedelta(days=365)).isoformat()

        topics_processed = 0
        topics_without_projects = 0
        projects_new = []

        # Main iteration loop: fetch projects for each recent call
        for call in closed_calls:
            topic_id = call.get("topicId", "")
            deadline = call.get("deadline", "")

            # Skip if too old (>1 year)
            if deadline < one_year_ago:
                continue

            # Fetch projects for this topicId (always, may have new projects)
            try:
                raw_projects = self._fetch_projects_for_single_topic(topic_id)
            except Exception as e:
                log.warning(f"Error fetching projects for {topic_id}: {e}")
                continue  # Skip this topic, continue with next

            if not raw_projects:
                # No projects for this topic (closed call without awards)
                topics_without_projects += 1
                topics_processed += 1
                continue

            # Transform and enrich each project
            for raw_project in raw_projects:
                project_id = raw_project.get("projectId", "")
                dedup_key = (topic_id, project_id)

                # Skip if already in projects.json (dedup)
                if dedup_key in dedup_index:
                    continue

                # Transform record
                enriched = self._transform_project_record(raw_project)
                if not enriched.get("topicId") or not enriched.get("projectId"):
                    continue

                # Enrich with CORDIS data
                enriched = self._enrich_with_cordis(enriched)
                projects_new.append(enriched)
                dedup_index[dedup_key] = True

            topics_processed += 1

        # Final write: merge existing with new projects
        projects_final = projects_existing + projects_new
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(projects_final, f, indent=2, ensure_ascii=False)

        # Update metadata
        from cordis_data.data.metadata import load_metadata, save_metadata
        metadata_path = output_path.parent / ".metadata.json"
        metadata = load_metadata(metadata_path)
        metadata["projects_topics_processed_count"] = topics_processed
        metadata["projects_fetched_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        metadata["projects_rolling_window_days"] = 365
        metadata["projects_topics_without_projects_count"] = topics_without_projects
        save_metadata(metadata, metadata_path)

        print(f"Completed: {topics_processed} topics processed, "
              f"{len(projects_new)} new projects, {len(projects_final)} total, "
              f"{topics_without_projects} without projects", flush=True)
