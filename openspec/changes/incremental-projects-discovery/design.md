# ProjectsFetcher: Design Document

## Architecture Overview

```
calls.closed.json (6305 topics)
        │
        ├─ Load into memory
        │
        ├─ Load projects.json (existing projects)
        │  └─ Index by (topicId, projectId) for dedup
        │
        └─→ [Iteration Loop]
            │
            ├─ For each call in calls.closed.json:
            │  │
            │  ├─ Check: deadline >= (today - 1 year)?
            │  │  ├─ Too old (>1 year) → Skip (optimization)
            │  │  └─ Recent → Fetch projects
            │  │
            │  ├─ Fetch projects for topicId from SEDIA
            │  │  ├─ Success, found N projects:
            │  │  │  ├─ For each project:
            │  │  │  │  ├─ Check (topicId, projectId) dedup
            │  │  │  │  ├─ If new: Enrich with CORDIS (2 req/s)
            │  │  │  │  └─ Append to projects list
            │  │  │  └─ Update processed count
            │  │  │
            │  │  ├─ Success, found 0 projects:
            │  │  │  ├─ Log "no projects for topicId"
            │  │  │  └─ Update processed count
            │  │  │
            │  │  └─ Error (API, network, etc):
            │  │     ├─ Retry with backoff (max 3 attempts)
            │  │     ├─ If still fails: Log error, continue
            │  │
            │  └─ Update processed count
            │
            └─→ Final write:
                ├─ Write projects.json
                ├─ Update metadata:
                │  ├─ projects_topics_processed_count
                │  ├─ projects_fetched_at (cycle start time)
                │  ├─ projects_rolling_window_days (365)
                │  └─ projects_topics_without_projects_count
                └─ Log completion summary
```

## Class Structure

```python
class ProjectsFetcher:
    """Fetch and enrich awarded projects from closed call topics."""
    
    def main(
        self,
        output_path: Optional[Path] = None,
        calls_path: Optional[Path] = None,
        years: Optional[int] = None,
        force: bool = False,
    ) -> None:
        """
        Incrementally fetch and enrich projects for closed calls.
        
        Args:
            output_path: Path to write projects.json (default: data/projects.json)
            calls_path: Path to calls.closed.json (default: data/calls.closed.json)
            years: Limit to calls closed within last N years (optional)
            force: Skip freshness check and fetch unconditionally
        
        Algorithm:
        1. Load calls.closed.json
        2. Load existing projects.json (or start empty)
        3. Load metadata (resumption state)
        4. Iterate topics, fetch projects, enrich, checkpoint
        5. Write final projects.json and updated metadata
        """
    
    def _load_closed_calls(
        self,
        calls_path: Path,
        years: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Load and optionally filter closed calls by deadline."""
        with open(calls_path, 'r', encoding='utf-8') as f:
            calls = json.load(f)
        
        if years:
            cutoff_date = (date.today() - timedelta(days=365 * years)).isoformat()
            calls = [c for c in calls if c.get('deadline', '') >= cutoff_date]
        
        return calls
    
    def _load_existing_projects(
        self,
        output_path: Path,
    ) -> list[dict]:
        """
        Load existing projects from projects.json.
        
        Returns:
            List of project dicts (or empty list if file doesn't exist)
        """
    
    def _build_dedup_index(
        self,
        projects: list[dict],
    ) -> dict[tuple[str, str], bool]:
        """
        Build deduplication index from existing projects.
        
        Returns:
            {(topicId, projectId): True, ...}
        
        Used for O(1) check if (topicId, projectId) already exists.
        """
    
    def _fetch_projects_for_topic(
        self,
        topic_id: str,
    ) -> list[dict[str, Any]]:
        """
        Fetch projects from SEDIA for a single topicId.
        
        Returns list of raw project dicts (before CORDIS enrichment).
        Empty list if no projects found for this topic (graceful).
        
        Raises:
            TemporaryError: Network/transient error (will retry on next run)
            PermanentError: Invalid topicId format or API incompatibility
        """
    
    def _enrich_project_with_cordis(
        self,
        project: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Enrich single project with CORDIS data (objective, grantDoi).
        
        Rate-limited to max 2 requests/second.
        """
```

## Data Structures

### projects.json (Output)

```json
[
  {
    "topicId": "HORIZON-2023-CL5-01-01",
    "projectId": "999999",
    "title": "Project Title",
    "status": "funded",
    "grantDoi": "10.3030/...",
    "objective": "Project objective and description...",
    "coordinator": "University of Example",
    "startDate": "2023-01-01",
    "endDate": "2025-12-31",
    ...
  }
]
```

**Retention:** Append-only, grows over time
**Deduplication:** (topicId, projectId) is unique; prevent duplicate rows

### Metadata Tracking

```json
{
  "projects_topics_processed_count": 2140,
  "projects_fetched_at": "2026-08-10T12:00:00Z",
  "projects_freshness_ttl_days": 30,
  "projects_rolling_window_days": 365,
  "projects_topics_without_projects_count": 1234
}
```

**Used for:**
- Progress tracking: topics_processed_count vs total closed calls
- Freshness check: projects_fetched_at + TTL
- Observability: how many topics have no projects

## Algorithm: Main Loop

```python
def main(self, ...):
    closed_calls = self._load_closed_calls(calls_path, years=None)
    projects_existing = self._load_existing_projects(output_path)
    dedup_index = self._build_dedup_index(projects_existing)  # (topicId, projectId) → True
    metadata = load_metadata(metadata_path)
    
    one_year_ago = (date.today() - timedelta(days=365)).isoformat()
    
    topics_processed = 0
    topics_without_projects = 0
    projects_new = []
    
    for call in closed_calls:
        topic_id = call['topicId']
        deadline = call.get('deadline', '')
        
        # Skip if too old (>1 year)
        if deadline < one_year_ago:
            log.debug(f"Skipping {topic_id}: deadline {deadline} too old")
            continue
        
        # Fetch projects for this topicId (always, may have new projects)
        try:
            raw_projects = self._fetch_projects_for_topic(topic_id)
        except TemporaryError as e:
            log.warning(f"Transient error for {topic_id}: {e}")
            continue  # Skip this topic, continue with next
        except PermanentError as e:
            log.error(f"Permanent error for {topic_id}, skipping: {e}")
            topics_processed += 1
            continue
        
        if not raw_projects:
            # No projects for this topic (closed call without awards)
            topics_without_projects += 1
            topics_processed += 1
            log.debug(f"No projects for {topic_id}")
            continue
        
        # Enrich and deduplicate
        for raw_project in raw_projects:
            project_id = raw_project['projectId']
            dedup_key = (topic_id, project_id)
            
            # Skip if already in projects.json (dedup)
            if dedup_key in dedup_index:
                continue
            
            # Enrich with CORDIS data
            enriched = self._enrich_project_with_cordis(raw_project)
            projects_new.append(enriched)
            dedup_index[dedup_key] = True
        
        topics_processed += 1
    
    # Final write: merge with existing projects
    projects_final = projects_existing + projects_new
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(projects_final, f, indent=2, ensure_ascii=False)
    
    # Update metadata
    metadata['projects_topics_processed_count'] = topics_processed
    metadata['projects_fetched_at'] = datetime.now(datetime.UTC).isoformat()
    metadata['projects_rolling_window_days'] = 365
    metadata['projects_topics_without_projects_count'] = topics_without_projects
    save_metadata(metadata_path, metadata)
    
    log.info(
        f"Completed: {topics_processed} topics processed, "
        f"{len(projects_new)} new projects, "
        f"{len(projects_final)} total, "
        f"{topics_without_projects} without projects"
    )
```

## Error Handling

| Scenario | Handling |
|----------|----------|
| Network error on SEDIA fetch | Retry with backoff (3x), then break loop |
| CORDIS API rate limit | Respect 2 req/s, queue and wait |
| topicId not found (404) | Graceful: 0 projects, log, continue |
| Invalid topicId format | Log error, skip, continue |
| Write failure on checkpoint | Fail fast (data integrity > resumption) |
| Interrupted mid-fetch | Resumable: last_visited_topic_id in metadata |

## Rate Limiting

- **SEDIA fetch:** No explicit limit mentioned in current code; assume reasonable
- **CORDIS enrichment:** Max 2 requests/second (from existing code)

Implementation:
```python
from time import time, sleep

class RateLimiter:
    def __init__(self, max_per_second: float = 2.0):
        self.max_per_second = max_per_second
        self.min_interval = 1.0 / max_per_second
        self.last_request_time = 0
    
    def wait(self):
        elapsed = time() - self.last_request_time
        if elapsed < self.min_interval:
            sleep(self.min_interval - elapsed)
        self.last_request_time = time()
```

## CLI Changes

```bash
cordis-data fetch-projects [OPTIONS]

Options:
  --output PATH               Output file path (default: data/projects.json)
  --calls-closed PATH         Path to calls.closed.json (default: data/calls.closed.json)
  --help
```

**Breaking change:** 
- --calls parameter is removed (deprecated, was pointing to calls.json)
- --years parameter is removed (not needed: rolling window is fixed at 1 year)
- --force parameter is removed (always fetches: freshness is implicit in rolling window)

## GitHub Actions

Update `fetch-calls.yml` to run ProjectsFetcher after ClosedCallsFetcher:

```yaml
- name: Fetch closed calls
  run: cordis-data fetch-closed-calls --force

- name: Discover projects from closed calls
  run: cordis-data fetch-projects
```

(Runs always; fetches only topics from last 1 year, incremental projects addition)

## Testing Strategy

1. **Unit tests:**
   - _load_closed_calls from calls.closed.json
   - _load_existing_projects (empty and existing)
   - _build_dedup_index (O(1) lookups)
   - _fetch_projects_for_topic SEDIA API interaction
   - _enrich_project_with_cordis CORDIS API interaction
   - Rolling window filtering (deadline >= 1 year ago)

2. **Integration tests:**
   - End-to-end: closed calls → projects → enriched data
   - Idempotency: running twice produces same projects.json + same count
   - Rolling window: calls >1 year old are skipped

3. **Edge cases:**
   - Empty calls.closed.json
   - TopicId with 0 projects
   - All calls older than 1 year (no processing)
   - API errors on fetch (continue gracefully)
   - CORDIS enrichment failure (partial enrichment)
