# Implementation Tasks: Incremental Projects Discovery

## Phase 1: Core Fetcher Refactoring (5 tasks)

- [x] 1. Refactor ProjectsFetcher.\_\_init\_\_ to accept optional sedia_client for testing
- [x] 2. Update ProjectsFetcher.\_load_closed_calls() to read from calls.closed.json (not calls.json)
- [x] 3. Implement ProjectsFetcher.\_load_existing_projects() to load existing projects.json
- [x] 4. Implement ProjectsFetcher.\_build_dedup_index() to index (topicId, projectId) pairs
- [x] 5. Refactor main loop: replace batch processing with topic-by-topic rolling window iteration

## Phase 2: Rolling Window & Deduplication (3 tasks)

- [x] 6. Implement rolling window filter: skip calls with deadline < (today - 365 days)
- [x] 7. Implement (topicId, projectId) deduplication: skip new projects already in projects.json
- [x] 8. Change main loop to always fetch (remove freshness check), append only new projects

## Phase 3: Error Handling & Rate Limiting (2 tasks)

- [x] 9. Add error handling with retry logic (exponential backoff, max 3 attempts)
- [x] 10. Implement RateLimiter class for CORDIS max 2 req/s

## Phase 4: CORDIS Enrichment (1 task)

- [x] 11. Extract/refine _enrich_project_with_cordis() method (move from existing code)

## Phase 5: CLI & Metadata Updates (3 tasks)

- [x] 12. Update CLI fetch_projects command: change source to calls.closed.json, remove --years/--force
- [x] 13. Update CLI fetch_projects command: change --calls to --calls-closed
- [x] 14. Update CLI status command to display projects metadata (topics_processed_count, rolling_window_days)

## Phase 6: Testing (5 tasks)

- [x] 15. Write unit tests for _load_existing_projects and _build_dedup_index (all 26 tests passing)
- [x] 16. Write unit tests for _fetch_projects_for_topic (mock SEDIA, test graceful 0 projects)
- [x] 17. Write unit test for rolling window filter (skip old calls)
- [x] 18. Write integration test: end-to-end with mock SEDIA and CORDIS
- [x] 19. Write idempotency test: run twice, same projects.json

## Phase 7: Quality & Workflow (6 tasks)

- [x] 20. Run flake8, fix linting errors to 0
- [x] 21. Run pyright, fix type checking errors to 0
- [x] 22. Run mypy, fix type checking errors to 0
- [x] 23. Verify test coverage >= 100% of new/changed code
- [x] 24. Update .github/workflows/fetch-calls.yml to add fetch-projects step (always run)
- [x] 25. Verify GitHub Actions workflow runs successfully

---

## Task Details

### Task 1: Refactor ProjectsFetcher.\_\_init\_\_ to accept optional sedia_client

**File:** `src/cordis_data/data/projects.py`

Change constructor to allow injecting mock SEDIA client for testing:

```python
def __init__(self, sedia_client: Optional[SediaClient] = None):
    self.sedia_client = sedia_client or SediaClient()
```

**Tests:** `tests/unit/test_data_projects.py::test_projects_fetcher_init`

---

### Task 2: Update _load_closed_calls() to read from calls.closed.json

**File:** `src/cordis_data/data/projects.py`

Change from reading calls.json and filtering by callStatus="closed" to directly reading calls.closed.json:

```python
def _load_closed_calls(
    self,
    calls_path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    if calls_path is None:
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        calls_path = project_root / "data" / "calls.closed.json"
    
    with open(calls_path, 'r', encoding='utf-8') as f:
        calls = json.load(f)
    
    return calls  # Already filtered (closed only)
```

Note: Remove the year filtering parameter (rolling window is fixed at 365 days)

**Tests:** Test reading calls.closed.json

---

### Task 3: Implement \_load_existing_projects()

**File:** `src/cordis_data/data/projects.py`

Load existing projects from projects.json:

```python
def _load_existing_projects(
    self,
    output_path: Path,
) -> list[dict]:
    """Load existing projects from projects.json (or return empty list)."""
    
    if not output_path.exists():
        return []
    
    with open(output_path, 'r', encoding='utf-8') as f:
        projects = json.load(f)
    
    return projects
```

**Tests:** `test_load_existing_projects_empty`, `test_load_existing_projects_existing`

---

### Task 4: Implement \_build_dedup_index()

**File:** `src/cordis_data/data/projects.py`

Build O(1) deduplication index from existing projects:

```python
def _build_dedup_index(
    self,
    projects: list[dict],
) -> dict[tuple[str, str], bool]:
    """Build dedup index: {(topicId, projectId): True, ...}"""
    
    index = {}
    for p in projects:
        key = (p['topicId'], p['projectId'])
        index[key] = True
    
    return index
```

**Tests:** `test_build_dedup_index_empty`, `test_build_dedup_index_lookup`

---

### Task 5: Refactor main loop

**File:** `src/cordis_data/data/projects.py`

Replace batch processing with rolling window iteration (see Algorithm in design.md).

Key points:
- Iterate closed_calls one topic at a time
- Check rolling window: deadline >= (today - 365 days)
- Check dedup index before appending (no duplicate (topicId, projectId))
- Append only new projects to projects_existing
- Write once at end
- Update metadata

**Tests:** `test_main_loop_iteration`

---

### Task 6: Implement rolling window filter

**File:** `src/cordis_data/data/projects.py`

In main loop, skip old calls:

```python
one_year_ago = (date.today() - timedelta(days=365)).isoformat()

for call in closed_calls:
    deadline = call.get('deadline', '')
    
    if deadline < one_year_ago:
        log.debug(f"Skipping {topic_id}: deadline {deadline} too old")
        continue
    
    # Process...
```

**Tests:** `test_rolling_window_skips_old_calls`

---

### Task 7: Implement (topicId, projectId) deduplication

**File:** `src/cordis_data/data/projects.py`

In enrichment loop:

```python
for raw_project in raw_projects:
    project_id = raw_project['projectId']
    dedup_key = (topic_id, project_id)
    
    if dedup_key in dedup_index:
        continue  # Skip, already in projects.json
    
    enriched = self._enrich_project_with_cordis(raw_project)
    projects_new.append(enriched)
    dedup_index[dedup_key] = True
```

**Tests:** `test_dedup_skips_duplicate_pairs`

---

### Task 8: Change main loop to always fetch

**File:** `src/cordis_data/data/projects.py`

Remove freshness check, always fetch (see full algorithm in design.md).

**Tests:** `test_always_fetches_recent_calls`

---

### Task 9: Add error handling with retry logic

**File:** `src/cordis_data/data/projects.py`

Implement exponential backoff:

```python
def _fetch_with_retry(self, topic_id: str, max_attempts: int = 3) -> list[dict]:
    """Fetch projects with exponential backoff retry."""
    
    for attempt in range(max_attempts):
        try:
            return self._fetch_projects_for_topic(topic_id)
        except (NetworkError, TimeoutError) as e:
            if attempt == max_attempts - 1:
                log.error(f"Failed after {max_attempts} attempts for {topic_id}: {e}")
                return []  # Graceful: treat as "no projects"
            
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            log.warning(f"Attempt {attempt+1} failed, retrying in {wait_time}s: {e}")
            time.sleep(wait_time)
```

**Tests:** Mock failures and verify retry behavior

---

### Task 10: Implement RateLimiter class

**File:** `src/cordis_data/data/projects.py` (or separate utility file)

```python
class RateLimiter:
    def __init__(self, max_per_second: float = 2.0):
        self.max_per_second = max_per_second
        self.min_interval = 1.0 / max_per_second
        self.last_request_time = 0
    
    def wait(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
```

Apply in enrichment loop:

```python
cordis_limiter = RateLimiter(max_per_second=2.0)

for project in projects_to_enrich:
    cordis_limiter.wait()
    enriched = self._enrich_project_with_cordis(project)
```

**Tests:** `test_rate_limiter_respects_max_per_second`

---

### Task 11: Extract _enrich_project_with_cordis() method

**File:** `src/cordis_data/data/projects.py`

Ensure this method exists and is properly extracted (should already exist in current code):

```python
def _enrich_project_with_cordis(
    self,
    project: dict[str, Any],
) -> dict[str, Any]:
    """Enrich single project with CORDIS data (objective, grantDoi)."""
    # ... existing implementation ...
```

**Tests:** Verify enrichment adds objective and grantDoi

---

### Task 12: Update CLI fetch_projects command

**File:** `src/cordis_data/cli/__init__.py`

Update signature and docstring:

```python
@main.command()
@click.option(
    "--calls-closed",
    type=click.Path(),
    default=None,
    help="Path to calls.closed.json (default: data/calls.closed.json)",
)
@click.option(
    "--output",
    type=click.Path(),
    default=None,
    help="Output file path (default: data/projects.json)",
)
def fetch_projects(calls_closed: str | None, output: str | None) -> None:
    """Fetch awarded projects for closed calls and enrich with CORDIS data.
    
    Fetches projects from SEDIA for closed calls (last 1 year rolling window),
    deduplicates by (topicId, projectId), enriches with CORDIS data, and
    appends to existing projects.json. Runs on every invocation.
    """
    try:
        fetcher = ProjectsFetcher()
        output_path = Path(output) if output else None
        calls_path = Path(calls_closed) if calls_closed else None
        fetcher.main(output_path=output_path, calls_path=calls_path)
    except Exception as e:
        click.echo(f"Error fetching projects: {e}", err=True)
        sys.exit(1)
```

Remove --years and --force parameters.

**Tests:** `test_cli_fetch_projects_uses_calls_closed`

---

### Task 13: Update CLI parameter name

**File:** `src/cordis_data/cli/__init__.py`

Ensure --calls-closed is the parameter (not --calls).

**Tests:** `test_cli_fetch_projects_help_shows_calls_closed`

---

### Task 14: Update CLI status command

**File:** `src/cordis_data/cli/__init__.py`

```python
def status(...):
    # ...
    click.echo("\nProjects:")
    click.echo(f"  Last fetched: {metadata.get('projects_fetched_at', 'Never')}")
    click.echo(f"  Topics processed: {metadata.get('projects_topics_processed_count', 0)}")
    click.echo(f"  Topics without projects: {metadata.get('projects_topics_without_projects_count', 0)}")
    click.echo(f"  Rolling window: {metadata.get('projects_rolling_window_days', 365)} days")
    click.echo(f"  Freshness TTL: {metadata.get('projects_freshness_ttl_days', 30)} days")
```

**Tests:** `test_status_displays_projects_metadata`

---

### Task 15: Unit tests for _load_existing_projects and _build_dedup_index

**File:** `tests/unit/test_data_projects.py`

```python
def test_load_existing_projects_empty(tmp_path):
    """Empty projects.json returns empty list."""
    fetcher = ProjectsFetcher(mock_sedia)
    projects = fetcher._load_existing_projects(tmp_path / "projects.json")
    assert projects == []

def test_load_existing_projects_existing(tmp_path):
    """Existing projects.json is loaded correctly."""
    # Setup existing projects.json
    # Verify loaded correctly

def test_build_dedup_index_empty():
    """Empty projects list returns empty index."""
    fetcher = ProjectsFetcher(mock_sedia)
    index = fetcher._build_dedup_index([])
    assert index == {}

def test_build_dedup_index_lookup():
    """Index enables O(1) lookup of (topicId, projectId)."""
    projects = [
        {"topicId": "T1", "projectId": "P1"},
        {"topicId": "T1", "projectId": "P2"},
    ]
    fetcher = ProjectsFetcher(mock_sedia)
    index = fetcher._build_dedup_index(projects)
    
    assert ("T1", "P1") in index
    assert ("T1", "P2") in index
    assert ("T2", "P1") not in index
```

---

### Task 16: Unit tests for _fetch_projects_for_topic

**File:** `tests/unit/test_data_projects.py`

```python
def test_fetch_projects_for_topic_found(mock_sedia):
    """Fetch returns projects when found."""
    mock_sedia.search.return_value = {"results": [{"projectId": "P1"}]}
    fetcher = ProjectsFetcher(sedia_client=mock_sedia)
    
    projects = fetcher._fetch_projects_for_topic("T1")
    assert len(projects) == 1
    assert projects[0]["projectId"] == "P1"

def test_fetch_projects_for_topic_not_found(mock_sedia):
    """Fetch returns empty list when no projects found."""
    mock_sedia.search.return_value = {"results": []}
    fetcher = ProjectsFetcher(sedia_client=mock_sedia)
    
    projects = fetcher._fetch_projects_for_topic("T1")
    assert projects == []

def test_fetch_projects_for_topic_api_error(mock_sedia):
    """Fetch raises error on API failure."""
    mock_sedia.search.side_effect = NetworkError("API unavailable")
    fetcher = ProjectsFetcher(sedia_client=mock_sedia)
    
    with pytest.raises(NetworkError):
        fetcher._fetch_projects_for_topic("T1")
```

---

### Task 17: Unit test for rolling window filter

**File:** `tests/unit/test_data_projects.py`

```python
def test_rolling_window_skips_old_calls(mock_sedia):
    """Calls older than 1 year are skipped."""
    fetcher = ProjectsFetcher(sedia_client=mock_sedia)
    
    two_years_ago = (date.today() - timedelta(days=730)).isoformat()
    one_month_ago = (date.today() - timedelta(days=30)).isoformat()
    
    closed_calls = [
        {"topicId": "T1", "deadline": two_years_ago},  # Should skip
        {"topicId": "T2", "deadline": one_month_ago},  # Should fetch
    ]
    
    # Mock SEDIA to track which topicIds are fetched
    mock_sedia.search.return_value = {"results": []}
    
    # Run main logic...
    # Verify only T2 was fetched, T1 was skipped
```

---

### Task 18: Integration test end-to-end

**File:** `tests/integration/test_projects_fetcher.py`

```python
def test_end_to_end_fetch_and_enrich(tmp_path, mock_sedia, mock_cordis):
    """End-to-end: closed calls → SEDIA fetch → CORDIS enrich → projects.json"""
    
    # Setup
    calls_path = tmp_path / "calls.closed.json"
    output_path = tmp_path / "projects.json"
    
    # Write test closed calls
    with open(calls_path, 'w') as f:
        json.dump([
            {"topicId": "T1", "deadline": "2026-07-01"},
        ], f)
    
    # Mock API responses
    mock_sedia.search.return_value = {"results": [{
        "projectId": "P1",
        "title": "Project 1",
    }]}
    mock_cordis.get.return_value = {
        "objective": "...",
        "grantDoi": "10.3030/...",
    }
    
    # Run
    fetcher = ProjectsFetcher(sedia_client=mock_sedia)
    fetcher.main(output_path=output_path, calls_path=calls_path)
    
    # Verify
    with open(output_path) as f:
        projects = json.load(f)
    
    assert len(projects) == 1
    assert projects[0]["topicId"] == "T1"
    assert projects[0]["objective"] == "..."
    assert projects[0]["grantDoi"] == "10.3030/..."
```

---

### Task 19: Idempotency test

**File:** `tests/integration/test_projects_fetcher.py`

```python
def test_idempotent_run_twice(tmp_path, mock_sedia, mock_cordis):
    """Running twice produces same projects.json + same count."""
    
    # Setup (same as task 18)
    # ...
    
    # Run 1
    fetcher = ProjectsFetcher(sedia_client=mock_sedia)
    fetcher.main(output_path=output_path, calls_path=calls_path)
    
    with open(output_path) as f:
        projects_run1 = json.load(f)
    
    # Run 2
    fetcher.main(output_path=output_path, calls_path=calls_path)
    
    with open(output_path) as f:
        projects_run2 = json.load(f)
    
    # Verify: same projects, same count
    assert len(projects_run1) == len(projects_run2)
    assert projects_run1 == projects_run2
```

---

### Task 20-25: Quality & Workflow

- Task 20: `flake8 src/ tests/` → 0 errors
- Task 21: `pyright src/ tests/` → 0 errors
- Task 22: `mypy src/ tests/` → 0 errors
- Task 23: `pytest --cov` → 100% of new code
- Task 24: Update `.github/workflows/fetch-calls.yml` to add:
  ```yaml
  - name: Discover projects from closed calls
    run: cordis-data fetch-projects
  ```
- Task 25: Verify workflow runs successfully (manual or dry-run)
