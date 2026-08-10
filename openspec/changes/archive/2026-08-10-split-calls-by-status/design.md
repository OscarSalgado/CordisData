# Split Calls Fetch - Design Document

## Architecture Overview

```
SEDIA API (one request)
        │
        ├─ All calls with status metadata
        │
        ├─────────────┬─────────────┐
        │             │             │
        ▼             ▼             ▼
    [Parse]      [Parse]      [Parse]
        │             │             │
        ├─ Filter: open|forthcoming
        │  startDate >= (today-9mo)
        │
        ├─ Filter: closed
        │  startDate <= (today-3mo)
        │
    ┌───┴──────┬─────────────┐
    │          │             │
    ▼          ▼             ▼
 calls.open   calls.closed   [unused]
 changelog    changelog
 (open/)      (closed/)
```

## Class Structure

### OpenCallsFetcher

```python
class OpenCallsFetcher:
    """Fetch and store active (open/forthcoming) EU calls."""
    
    def main(
        self,
        output_path: Optional[Path] = None,
        metadata_path: Optional[Path] = None,
        years: Optional[int] = None
    ) -> None:
        """
        Fetch open and forthcoming calls from last 9 months.
        
        Args:
            output_path: Path to write calls.open.json (default: data/calls.open.json)
            metadata_path: Path to metadata (default: project_root/.metadata.json)
            years: If set, limit to calls with deadline within N years
        
        Flow:
        1. Fetch all calls with status in ["open", "forthcoming"]
        2. Filter by startDate >= (today - 9 months)
        3. Merge with existing calls.open.json
        4. Detect changes (NEW, UPDATED, UNCHANGED)
        5. Write calls.open.json
        6. Generate changelog/open/YYYY-MM-DD.json
        7. Update metadata.calls_open_fetched_at
        """
```

### ClosedCallsFetcher

```python
class ClosedCallsFetcher:
    """Fetch and store closed EU calls (for project discovery)."""
    
    def main(
        self,
        output_path: Optional[Path] = None,
        metadata_path: Optional[Path] = None
    ) -> None:
        """
        Fetch closed calls from dataset start to 3 months ago.
        
        Args:
            output_path: Path to write calls.closed.json (default: data/calls.closed.json)
            metadata_path: Path to metadata (default: project_root/.metadata.json)
        
        Flow:
        1. Fetch all calls with status="closed"
        2. Filter by startDate <= (today - 3 months)
        3. Merge with existing calls.closed.json
        4. Detect changes (NEW, UPDATED, UNCHANGED)
        5. Write calls.closed.json
        6. Generate changelog/closed/YYYY-MM-DD.json
        7. Update metadata.calls_closed_fetched_at
        """
```

## Data Storage

### calls.open.json

```json
[
  {
    "reference": "...",
    "topicId": "HORIZON-CL5-2026-D1-01-01",
    "callStatus": "open",
    "deadline": "2026-09-15",
    "programme": "Horizon Europe",
    ...
  }
]
```

Location: `data/calls.open.json`
Retention: Rolling 9-month window (older calls fade out naturally)

### calls.closed.json

```json
[
  {
    "reference": "...",
    "topicId": "HORIZON-2024-CL5-01-01",
    "callStatus": "closed",
    "deadline": "2024-06-15",
    "programme": "Horizon Europe",
    ...
  }
]
```

Location: `data/calls.closed.json`
Retention: Historical (from dataset start to today - 3 months)

### Changelog Structure

Both use same structure as current calls changelog:

```json
{
  "summary": {
    "new": 5,
    "changed": 2,
    "unchanged": 15
  },
  "events": [
    {
      "type": "NEW",
      "topicId": "...",
      "reference": "...",
      "title": "..."
    }
  ]
}
```

Locations:
- `data/changelog/open/YYYY-MM-DD.json`
- `data/changelog/closed/YYYY-MM-DD.json`

## Metadata Updates

```json
{
  "calls_open_fetched_at": "2026-08-10T12:00:00Z",
  "calls_open_freshness_ttl_days": 3,
  "calls_closed_fetched_at": "2026-08-10T12:05:00Z",
  "calls_closed_freshness_ttl_days": 7,
  ...
}
```

Each stream has independent freshness tracking.

## Error Handling

Both fetchers handle errors identically:
- API errors: Retry with exponential backoff (max 3 attempts)
- Fetch failure: Log error, don't update metadata (allows retry on next run)
- Write failure: Fail fast (data integrity > resumption)

## CLI Updates

New commands:
```bash
cordis-data fetch-open-calls [--force]
cordis-data fetch-closed-calls [--force]
cordis-data status calls
```

The `status` command shows:
```
Calls Status
════════════════════════════════════════════════════
Open Calls:
  Last fetched: 2026-08-10T12:00:00Z
  Count: 342
  Window: Last 9 months
  
Closed Calls:
  Last fetched: 2026-08-10T12:05:00Z
  Count: 5847
  Window: Start of dataset to 3 months ago
```

## GitHub Actions Workflow

The existing `fetch-calls.yml` is refactored to run both:

```yaml
jobs:
  fetch-calls:
    steps:
      - name: Fetch open calls
        run: cordis-data fetch-open-calls
      
      - name: Fetch closed calls
        run: cordis-data fetch-closed-calls
      
      - name: Commit and push
        if: always()
        run: git add data/calls.* data/changelog/* && git commit ...
```

Both run in the same job (same schedule), but independently.

## Migration Path (Future)

When ProjectsFetcher is implemented:
```python
class ProjectsFetcher:
    def main(self, calls_closed_path: Optional[Path] = None):
        if calls_closed_path is None:
            calls_closed_path = project_root / "data" / "calls.closed.json"
        
        # Extract topicIds from calls.closed.json
        with open(calls_closed_path) as f:
            closed_calls = json.load(f)
        
        topic_ids = [c["topicId"] for c in closed_calls]
        # Fetch projects for these topicIds...
```

No change to this design needed — calls.closed.json is already available.
