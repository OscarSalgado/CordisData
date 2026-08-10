"""EU research project fetcher and CORDIS enricher."""

import datetime
import json
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
from cordis_data.data.h2020 import H2020Enricher
from cordis_data.utils import merge_projects, normalize_date, summarize_changes

T = TypeVar("T")


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
        self.rate_limiter = rate_limiter or TokenBucket(rate=CORDIS_RATE_LIMIT)
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
            "startDate": normalize_date((m.get("startDate") or [""])[0]),
            "endDate": normalize_date((m.get("endDate") or [""])[0]),
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

    def _load_closed_topic_ids(
        self,
        calls_path: Path,
        since_date: Optional[str] = None,
    ) -> list[str]:
        """Load topicIds for closed calls, optionally filtered by deadline.

        Args:
            calls_path: Path to calls.json
            since_date: Optional ISO YYYY-MM-DD string to filter by deadline

        Returns:
            List of topic identifiers for closed calls
        """
        with open(calls_path, "r", encoding="utf-8") as f:
            calls = json.load(f)
        closed = [c for c in calls if c.get("callStatus") == "closed"]
        if since_date:
            closed = [c for c in closed if not c.get("deadline") or c["deadline"] >= since_date]
        return [c["topicId"] for c in closed]

    def main(
        self,
        output_path: Optional[Path] = None,
        calls_path: Optional[Path] = None,
        years: Optional[int] = None,
    ) -> None:
        """Fetch projects from SEDIA and enrich with CORDIS data.

        Args:
            output_path: Path to write projects.json (default: data/projects.json)
            calls_path: Path to calls.json (default: data/calls.json)
            years: Limit to closed topics whose deadline is within last N years
                (default: None = all closed topics)
        """
        if output_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            output_path = project_root / "data" / "projects.json"
        else:
            output_path = Path(output_path)

        if calls_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            calls_path = project_root / "data" / "calls.json"
        else:
            calls_path = Path(calls_path)

        since_date = None
        if years:
            since_date = (datetime.date.today() - datetime.timedelta(days=365 * years)).isoformat()
            print(f"Limiting to closed topics with deadline >= {since_date} "
                  f"(--years={years})", flush=True)

        topic_ids = self._load_closed_topic_ids(calls_path, since_date=since_date)
        print(f"Found {len(topic_ids)} closed topics", flush=True)

        existing_projects = []
        if output_path.exists():
            with open(output_path, "r", encoding="utf-8") as f:
                existing_projects = json.load(f)
        existing_by_id = {p["projectId"]: p for p in existing_projects if p.get("projectId")}

        all_results = []
        batches = list(self._chunk(topic_ids, self.batch_size))
        print(f"Fetching {len(batches)} batches of projects...", flush=True)
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {executor.submit(self._fetch_batch_all_pages, batch): i
                       for i, batch in enumerate(batches, start=1)}
            completed = 0
            for future in as_completed(futures):
                completed += 1
                print(f"Batch {completed}/{len(batches)} done...", flush=True)
                all_results.extend(future.result())

        print(f"\nFetched {len(all_results)} raw awarded-project results", flush=True)

        projects = [self._transform_project_record(r) for r in all_results]
        projects = [p for p in projects if p["topicId"] and p["projectId"]]
        print(f"Transformed {len(projects)} valid projects", flush=True)

        to_enrich = [p for p in projects if self._needs_cordis_enrichment(p, existing_by_id)]
        print(
            f"{len(to_enrich)}/{len(projects)} projects needed CORDIS enrichment "
            "(rest already enriched)", flush=True,
        )

        # Copy existing enrichment data to non-new projects
        to_enrich_ids = {p["projectId"] for p in to_enrich}
        for p in projects:
            if p["projectId"] not in to_enrich_ids:
                existing = existing_by_id.get(p["projectId"])
                if existing:
                    p["objective"] = existing.get("objective")
                    p["grantDoi"] = existing.get("grantDoi")
                    p["lastEnrichedAt"] = existing.get("lastEnrichedAt")

        # Enrich with CORDIS and write incrementally (checkpoint every 500 projects)
        if to_enrich:
            self._enrich_projects_with_cordis(to_enrich, output_path=output_path)

        # Final write for non-enriched projects
        non_enriched = [p for p in projects if p["projectId"] not in to_enrich_ids]
        if non_enriched:
            self._write_and_merge_projects(non_enriched, output_path)

        # H2020 enrichment (optional, non-blocking)
        print("\nEnriching projects with H2020 data...", flush=True)
        try:
            h2020_enricher = H2020Enricher(cordis_client=self.cordis_client)
            if h2020_enricher.load_index():
                # Read current projects and enrich with H2020
                if output_path.exists():
                    with open(output_path, "r", encoding="utf-8") as f:
                        current_projects = json.load(f)

                    h2020_enriched = 0
                    for proj in current_projects:
                        h2020_data = h2020_enricher.enrich(proj)
                        if h2020_data:
                            proj["h2020_related"] = h2020_data
                            h2020_enriched += 1

                    # Write back enriched projects
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(current_projects, f, separators=(",", ":"), ensure_ascii=False)

                    print(f"H2020-enriched {h2020_enriched} projects", flush=True)
            else:
                print("H2020 index load failed; skipping H2020 enrichment", flush=True)
        except Exception as e:
            print(f"H2020 enrichment error: {e}; continuing without H2020 data", flush=True)

        # Final summary
        if output_path.exists():
            with open(output_path, "r", encoding="utf-8") as f:
                final_projects = json.load(f)
            merged_by_id = {p["projectId"]: p for p in final_projects}
            change_summary = summarize_changes(existing_by_id, merged_by_id)
            print(
                f"\nChanges: {change_summary['added']} added, {change_summary['changed']} changed, "
                f"{change_summary['unchanged']} unchanged", flush=True,
            )
            size_kb = output_path.stat().st_size / 1024
            print(f"\nWritten {output_path} ({len(final_projects)} projects, {size_kb:.0f} KB)")
