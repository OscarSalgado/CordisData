"""EU research funding calls fetcher for active (open/forthcoming) opportunities."""

import datetime
import json
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional, cast

from cordis_data.api.sedia import SediaClient
from cordis_data.data.archival import RETENTION_DAYS, cleanup_old_changelogs
from cordis_data.data.changelog import generate_compact_changelog_calls
from cordis_data.data.html_clean import clean_html_to_text
from cordis_data.config import (
    PROGRAMME_NAMES,
    SEDIA_API_KEY,
    SEDIA_API_URL,
    SEDIA_MAX_WORKERS,
    STATUS_MAP,
)
from cordis_data.data.metadata import (
    is_stale,
    load_metadata,
    save_metadata,
    update_timestamp,
)
from cordis_data.data.merger import get_programme_distribution, get_status_distribution, mark_expired_closed
from cordis_data.utils import extract_budget, merge_calls, normalize_date, parse_action_type, summarize_changes
from cordis_data.utils.compression import JSONLGzipReader, JSONLGzipWriter


class OpenCallsFetcher:
    """Fetches active EU research funding calls (open/forthcoming) from SEDIA.

    Fetches open and forthcoming EU grant calls published in the last 9 months
    and writes them to data/calls/open.jsonl.gz. Merges into existing data,
    preserving older records within the 9-month window.

    Dependency injection of SediaClient enables testing without network calls.
    """

    def __init__(self, sedia_client: Optional[SediaClient] = None) -> None:
        """Initialize OpenCallsFetcher with optional SEDIA client.

        Args:
            sedia_client: SediaClient instance (default: creates one with defaults)
        """
        self.sedia_client = sedia_client or SediaClient(
            api_url=SEDIA_API_URL,
            api_key=SEDIA_API_KEY,
        )
        self.max_workers = SEDIA_MAX_WORKERS

    def _build_query(self, since_date: Optional[str] = None) -> dict[str, Any]:
        """Build Elasticsearch query for open/forthcoming calls.

        Args:
            since_date: ISO date string (YYYY-MM-DDTHH:MM:SS.SSSZ) or None

        Returns:
            Query dict for SEDIA API
        """
        must: list[dict[str, Any]] = [
            # Type 8 excluded: cascade-funding calls not genuine EU topic calls
            {"terms": {"type": ["1", "2"]}},
            # Only open and forthcoming (31094501, 31094502)
            {"terms": {"status": ["31094501", "31094502"]}}
        ]
        if since_date:
            must.append({"range": {"startDate": {"gte": since_date}}})
        return {"bool": {"must": must}}

    def _fetch_page(self, page_num: int, query: dict[str, Any], page_size: int = 100, retries: int = 3) -> dict[str, Any]:
        """Fetch a single page of results from SEDIA API.

        Args:
            page_num: Page number (1-indexed)
            query: Elasticsearch query dict
            page_size: Results per page
            retries: Number of retry attempts

        Returns:
            Response dict with 'results' and 'totalResults'
        """
        sort = {"field": "startDate", "order": "DESC"}
        return self.sedia_client.search(query, sort, page_num, page_size, retries)

    def _parse_action_type_from_metadata(self, m: dict[str, Any]) -> str:
        """Extract and parse action type from metadata.

        Args:
            m: Metadata dict from API response

        Returns:
            Normalized action type code
        """
        action_type = ""
        try:
            actions_str = (m.get("actions") or ["[]"])[0]
            actions = cast(list[Any], json.loads(actions_str))
            if actions:
                act = actions[0]
                types = act.get("types", [])
                if types and isinstance(types[0], dict):
                    action_type = parse_action_type(types[0].get("typeOfAction", ""))
                proc = act.get("submissionProcedure", {}).get("abbreviation", "")
                if "two" in proc.lower():
                    pass
        except (json.JSONDecodeError, KeyError, AttributeError, TypeError):
            pass
        return action_type

    def _get_deadline_from_metadata(self, m: dict[str, Any]) -> str:
        """Extract and normalize deadline from metadata.

        Args:
            m: Metadata dict from API response

        Returns:
            Deadline as YYYY-MM-DD string or empty string
        """
        deadline = ""
        try:
            actions_str = (m.get("actions") or ["[]"])[0]
            actions = cast(list[Any], json.loads(actions_str))
            if actions:
                dls = actions[0].get("deadlineDates", [])
                if dls:
                    deadline = dls[0]
        except (json.JSONDecodeError, KeyError, AttributeError, TypeError):
            pass

        if not deadline:
            dl = (m.get("deadlineDate") or [""])[0]
            if dl:
                deadline = dl

        return normalize_date(deadline)

    def _extract_cluster(self, identifier: str) -> str:
        """Extract cluster from HORIZON identifier.

        Args:
            identifier: Topic identifier

        Returns:
            Cluster code (e.g., 'CL1', 'MSCA', 'ERC') or empty string
        """
        cluster = ""
        if identifier.startswith("HORIZON-"):
            parts = identifier.split("-")
            if len(parts) >= 2:
                tag = parts[1]
                cl_map = {
                    "HLTH": "CL1", "CL1": "CL1", "CL2": "CL2", "CL3": "CL3",
                    "CL4": "CL4", "CL5": "CL5", "CL6": "CL6", "MSCA": "MSCA",
                    "ERC": "ERC", "EIC": "EIC", "EIE": "EIE", "WIDERA": "WIDERA",
                    "INFRA": "INFRA", "JU": "JU", "MISS": "MISS",
                }
                cluster = cl_map.get(tag, tag if tag.startswith("CL") else "")
        return cluster

    def _migrate_old_format(self, new_path: Path) -> None:
        """Migrate old data/calls.open.json to new format if needed.

        Args:
            new_path: Path to new calls/open.jsonl.gz file
        """
        old_path = new_path.parent.parent / "calls.open.json"
        if old_path.exists() and not new_path.exists():
            try:
                with open(old_path, "r", encoding="utf-8") as f:
                    old_calls = json.load(f)
                writer = JSONLGzipWriter(new_path, normalize_utf8=True)
                writer.write_records(old_calls)
                # Archive old file
                backup_path = old_path.with_suffix(".json.bak")
                old_path.rename(backup_path)
                print(f"Migrated {old_path} to {new_path} (old file archived to {backup_path})", flush=True)
            except Exception as e:
                print(f"Migration failed: {e}. Continuing with fetch.", flush=True)

    def _extract_submission_procedure(self, m: dict[str, Any]) -> dict[str, Any]:
        """Extract submission procedure from actions[0].

        Args:
            m: Metadata dict from API response

        Returns:
            Dict with submissionProcedure fields or empty dict
        """
        result = {}
        try:
            actions_str = (m.get("actions") or ["[]"])[0]
            actions = cast(list[Any], json.loads(actions_str))
            if actions and "submissionProcedure" in actions[0]:
                sp = actions[0].get("submissionProcedure", {})
                result = {
                    "abbreviation": sp.get("abbreviation", ""),
                    "description": sp.get("description", ""),
                }
        except (json.JSONDecodeError, KeyError, AttributeError, TypeError):
            pass
        return result

    def _transform_record(self, r: dict[str, Any]) -> dict[str, Any]:
        """Map one raw SEDIA API result into call record shape.

        Args:
            r: Raw result dict from API

        Returns:
            Transformed call record dict
        """
        m = r.get("metadata", {})
        reference = r.get("reference") or ""
        identifier = (m.get("identifier") or [""])[0]
        title = (m.get("title") or [r.get("content", "")])[0]
        status_id = (m.get("status") or [""])[0]

        action_type = self._parse_action_type_from_metadata(m)
        deadline = self._get_deadline_from_metadata(m)

        fp_ids = m.get("frameworkProgramme") or []
        programme, programme_id = "", ""
        for fp in fp_ids:
            if fp in PROGRAMME_NAMES:
                programme, programme_id = PROGRAMME_NAMES[fp], fp
                break
        if not programme and fp_ids:
            programme_id = fp_ids[0]
            programme = f"EU Programme ({programme_id})"

        cluster = self._extract_cluster(identifier)

        kw = m.get("keywords") or []
        portal_url = (
            "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/"
            f"opportunities/topic-details/{identifier.lower()}"
        )
        budget_min, budget_max, expected_grants = extract_budget(m, identifier)

        description_byte = (m.get("descriptionByte") or [""])[0]
        description = clean_html_to_text(description_byte)

        dest_desc = (m.get("destinationDescription") or [""])[0]
        dest_details = (m.get("destinationDetails") or [""])[0]
        objectives = clean_html_to_text(f"{dest_desc} {dest_details}".strip())

        submission_procedure = self._extract_submission_procedure(m)

        call_title = (m.get("callTitle") or [""])[0]
        deadline_model = (m.get("deadlineModel") or [""])[0]
        cross_cutting = (m.get("crossCuttingPriorities") or [""])[0]
        types_of_action = (m.get("typesOfAction") or [""])[0]

        topic_conditions = (m.get("topicConditions") or [""])[0]
        topic_conditions = clean_html_to_text(topic_conditions)

        support_info = (m.get("supportInfo") or [""])[0]
        support_info = clean_html_to_text(support_info)

        qna_url = f"https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/questions-answers/{identifier.lower()}"
        updates_url = f"https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-updates/{identifier.lower()}"
        documents_url = f"https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/documents/{identifier.lower()}"

        return {
            "reference": reference,
            "topicId": identifier,
            "title": title,
            "programme": programme,
            "programmeId": programme_id,
            "cluster": cluster,
            "callIdentifier": (m.get("callIdentifier") or [""])[0],
            "actionType": action_type,
            "deadline": deadline,
            "stage": "two-stage" if deadline else "single",
            "callStatus": STATUS_MAP.get(status_id, "unknown"),
            "budgetMin": budget_min,
            "budgetMax": budget_max,
            "expectedGrants": expected_grants,
            "keywords": ", ".join(kw[:10]) if kw else "",
            "portalUrl": portal_url,
            "description": description,
            "objectives": objectives,
            "submissionProcedure": submission_procedure,
            "callTitle": call_title,
            "deadlineModel": deadline_model,
            "crossCuttingPriorities": cross_cutting,
            "typesOfAction": types_of_action,
            "topicConditions": topic_conditions,
            "supportInfo": support_info,
            "qnaUrl": qna_url,
            "updatesUrl": updates_url,
            "documentsUrl": documents_url,
        }

    def main(
        self,
        output_path: Optional[Path] = None,
        force: bool = False,
    ) -> None:
        """Fetch open/forthcoming calls from SEDIA and write to output file.

        Fetches calls published in the last 9 months and merges them into
        existing data. Set force=True to skip freshness check.

        Args:
            output_path: Path to write calls/open.jsonl.gz (default: data/calls/open.jsonl.gz)
            force: If True, skip freshness check and fetch unconditionally
        """
        if output_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            output_path = project_root / "data" / "calls" / "open.jsonl.gz"
        else:
            output_path = Path(output_path)

        # Check metadata freshness (skip if force=True)
        project_root = output_path.parent.parent
        metadata = load_metadata(project_root / ".metadata.json")
        if (
            not force
            and not is_stale(
                metadata.get("calls_open_fetched_at"),
                metadata.get("calls_open_freshness_ttl_days", 3),
            )
        ):
            print("Open calls data is fresh. Skipping fetch.", flush=True)
            return

        # 9-month rolling window
        window = datetime.timedelta(days=9 * 30)
        since_day = datetime.date.today() - window
        since_date = since_day.strftime("%Y-%m-%dT00:00:00.000Z")
        print(
            f"Fetching open/forthcoming calls with startDate >= {since_date} "
            "(9-month rolling window)", flush=True,
        )

        query = self._build_query(since_date)

        print("Fetching page 1...", flush=True)
        data = self._fetch_page(1, query)
        total = int(data.get("totalResults", 0) or 0)
        print(f"Total calls: {total}", flush=True)
        num_pages = math.ceil(total / 100)

        all_results = data.get("results", [])
        print(f"Page 1: {len(all_results)} results", flush=True)

        if num_pages > 1:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self._fetch_page, page, query): page
                           for page in range(2, num_pages + 1)}
                for future in as_completed(futures):
                    page = futures[future]
                    pdata = future.result()
                    results = pdata.get("results", [])
                    all_results.extend(results)
                    print(f"  Page {page}/{num_pages}: got {len(results)}, "
                          f"total so far: {len(all_results)}", flush=True)

        print(f"\nFetched {len(all_results)} raw results", flush=True)

        calls = [self._transform_record(r) for r in all_results]

        # Migrate old format if needed
        self._migrate_old_format(output_path)

        # Load existing calls from JSONL.GZ
        used_existing = output_path.exists()
        if used_existing:
            reader = JSONLGzipReader(output_path)
            existing_calls = reader.read_all()
        else:
            existing_calls = []

        merged_by_id = merge_calls(existing_calls, calls, full_history=False)
        if used_existing:
            print(f"\nMerged {len(calls)} fetched calls into {len(existing_calls)} existing calls "
                  f"({len(merged_by_id)} total after merge)")

        existing_by_key = {
            (c.get("reference") or c["topicId"]): c
            for c in (existing_calls if existing_calls else [])
        }
        change_summary = summarize_changes(existing_by_key, merged_by_id)
        print(f"\nChanges: {change_summary['added']} added, {change_summary['changed']} changed, "
              f"{change_summary['unchanged']} unchanged")

        today_str = datetime.date.today().isoformat()
        marked_closed = mark_expired_closed(list(merged_by_id.values()), today_str)
        if marked_closed:
            print(f"\nMarked {marked_closed} calls as 'closed' (with past deadlines)")

        merged_calls = sorted(merged_by_id.values(), key=lambda c: c.get("deadline") or "9999-99-99")

        print(f"\nTotal open calls: {len(merged_calls)}")
        programme_dist = get_programme_distribution(merged_calls)
        for p, cnt in list(programme_dist.items())[:10]:
            print(f"  {p}: {cnt}")

        print("\nBy status:")
        status_dist = get_status_distribution(merged_calls)
        for s, cnt in status_dist.items():
            print(f"  {s}: {cnt}")

        # Generate changelog for open calls
        changelog = generate_compact_changelog_calls(existing_calls, merged_by_id, marked_closed)
        changelog_path = output_path.parent / "changelog" / "open" / f"{today_str}.json"
        changelog_path.parent.mkdir(parents=True, exist_ok=True)
        with open(changelog_path, "w", encoding="utf-8") as f:
            json.dump(changelog, f, separators=(",", ":"), ensure_ascii=False)
        print(f"\nChangelog: {changelog['summary']['new']} new, "
              f"{changelog['summary']['changed']} changed "
              f"-> data/calls/changelog/open/{today_str}.json")

        deleted_changelogs = cleanup_old_changelogs(changelog_path.parent, datetime.date.today())
        if deleted_changelogs:
            print(f"\nArchival: deleted {len(deleted_changelogs)} changelog(s) older than "
                  f"{RETENTION_DAYS} days: {', '.join(deleted_changelogs)}")

        # Write to JSONL.GZ with UTF-8 normalization
        writer = JSONLGzipWriter(output_path, normalize_utf8=True)
        writer.write_records(merged_calls)
        size_kb = output_path.stat().st_size / 1024

        # Update metadata timestamp
        metadata = update_timestamp(metadata, "calls_open_fetched_at")
        save_metadata(metadata, project_root / ".metadata.json")
        print(f"\nWritten {output_path} ({len(merged_calls)} calls, {size_kb:.0f} KB, compressed)")
