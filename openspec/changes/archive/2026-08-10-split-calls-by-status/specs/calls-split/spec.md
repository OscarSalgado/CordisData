# Calls Split by Status - Specification

## Overview

Two independent fetchers for EU research funding calls, separated by status to support distinct use cases:
- **OpenCallsFetcher**: Active opportunities (open, forthcoming) - for immediate monitoring
- **ClosedCallsFetcher**: Closed opportunities - for project discovery and historical analysis

## API Contract

### OpenCallsFetcher.main()

```python
def main(
    self,
    output_path: Optional[Path] = None,
    metadata_path: Optional[Path] = None,
    years: Optional[int] = None
) -> None:
    """
    Fetch and store active EU calls (open/forthcoming) from last 9 months.
    
    Args:
        output_path: Path to calls.open.json (default: data/calls.open.json)
        metadata_path: Path to metadata file (default: .metadata.json)
        years: Limit to calls with deadline within N years (optional)
    
    Flow:
    1. Query SEDIA: status in ["open", "forthcoming"]
    2. Filter: startDate >= (today - 9 months)
    3. Load existing calls.open.json (if exists)
    4. Merge by reference (update existing, add new)
    5. Detect changes (NEW, UPDATED, UNCHANGED)
    6. Write calls.open.json
    7. Generate changelog/open/YYYY-MM-DD.json
    8. Update metadata.calls_open_fetched_at
    
    Raises:
        APIError: If SEDIA fetch fails after retries
        IOError: If write fails
    """
```

### ClosedCallsFetcher.main()

```python
def main(
    self,
    output_path: Optional[Path] = None,
    metadata_path: Optional[Path] = None
) -> None:
    """
    Fetch and store closed EU calls (from dataset start to 3 months ago).
    
    Args:
        output_path: Path to calls.closed.json (default: data/calls.closed.json)
        metadata_path: Path to metadata file (default: .metadata.json)
    
    Flow:
    1. Query SEDIA: status="closed"
    2. Filter: startDate >= DATASET_START AND startDate <= (today - 3 months)
    3. Load existing calls.closed.json (if exists)
    4. Merge by reference (update existing, add new)
    5. Detect changes (NEW, UPDATED, UNCHANGED)
    6. Write calls.closed.json
    7. Generate changelog/closed/YYYY-MM-DD.json
    8. Update metadata.calls_closed_fetched_at
    
    Raises:
        APIError: If SEDIA fetch fails after retries
        IOError: If write fails
    """
```

## Data Contracts

### calls.open.json

**Schema**: Array of call objects

```json
{
  "reference": "UNIQUE-REF-001",
  "topicId": "HORIZON-CL5-2026-D1-01-01",
  "title": "Call Title",
  "programme": "Horizon Europe",
  "programmeId": "H2020",
  "cluster": "CL5",
  "callStatus": "open",
  "deadline": "2026-09-15",
  "stage": "single|two-stage",
  "budgetMin": 5000000,
  "budgetMax": 15000000,
  "expectedGrants": 10,
  "keywords": "...",
  "portalUrl": "https://...",
  "description": "...",
  "objectives": "...",
  "qnaUrl": "https://...",
  "updatesUrl": "https://...",
  "documentsUrl": "https://..."
}
```

**Location**: `data/calls.open.json`
**Size**: ~500-700KB (typically ~300-400 active calls)
**Retention**: Rolling 9-month window (older calls fade out naturally)
**Update frequency**: Every 3 days (default window)

### calls.closed.json

**Schema**: Same as calls.open.json, but with status="closed"

**Location**: `data/calls.closed.json`
**Size**: ~3-5MB (typically ~3000-4000 historical closed calls)
**Retention**: Full history (from dataset start to today - 3 months)
**Update frequency**: Every 7 days (recommended, can be slower)

### changelog/open/YYYY-MM-DD.json

```json
{
  "summary": {
    "new": 5,
    "changed": 2,
    "unchanged": 293
  },
  "events": [
    {
      "type": "NEW",
      "reference": "...",
      "topicId": "...",
      "title": "..."
    },
    {
      "type": "UPDATED",
      "reference": "...",
      "topicId": "...",
      "title": "...",
      "field": "deadline",
      "old_value": "2026-09-15",
      "new_value": "2026-09-20"
    }
  ]
}
```

**Location**: `data/changelog/open/YYYY-MM-DD.json`
**Retention**: Rolling (follows calls.open.json retention)

### changelog/closed/YYYY-MM-DD.json

Same structure as open changelog.

**Location**: `data/changelog/closed/YYYY-MM-DD.json`
**Retention**: Perpetual (mirrors calls.closed.json retention)

## Metadata Updates

```json
{
  "calls_open_fetched_at": "ISO-8601 timestamp",
  "calls_open_freshness_ttl_days": 3,
  "calls_closed_fetched_at": "ISO-8601 timestamp",
  "calls_closed_freshness_ttl_days": 7
}
```

Each stream tracks independently.

## Error Handling

### Fetch Failures
- SEDIA API error → Retry with exponential backoff (max 3 attempts)
- Timeout → Retry (with backoff)
- Connection refused → Retry (with backoff)
- After max retries → Log error, exit (don't update metadata, allow retry next cycle)

### Write Failures
- Permission denied → Fail immediately (data integrity > resumption)
- Disk full → Fail immediately
- Parent directory missing → Create recursively, then write

### Partial Failures
- Open fails, closed succeeds → Both marked independent; open can retry next cycle
- Closed fails, open succeeds → Both marked independent; closed can retry next cycle

## Constraints

- **SEDIA Rate Limit**: Max 2 requests/sec (shared across all fetchers)
- **Page Size**: Max 100 results per request (pagination automatic)
- **Time Window**:
  - Open: Last 9 months from today
  - Closed: From first value in dataset to 3 months ago
- **File Size**:
  - calls.open.json: < 1 MB (soft limit)
  - calls.closed.json: < 10 MB (soft limit)

## CLI Interface

```bash
# Fetch active calls (open + forthcoming)
cordis-data fetch-open-calls [--force]

# Fetch closed calls
cordis-data fetch-closed-calls [--force]

# Show status of both streams
cordis-data status calls
```

## Integration Points

### Downstream: ProjectsFetcher (Future)

ProjectsFetcher will read `calls.closed.json` to extract topicIds for project discovery:

```python
# In ProjectsFetcher.main()
calls_closed_path = project_root / "data" / "calls.closed.json"
with open(calls_closed_path) as f:
    closed_calls = json.load(f)

topic_ids = [c["topicId"] for c in closed_calls if c["topicId"]]
# ... use topic_ids to fetch projects ...
```

No changes to this spec needed - calls.closed.json is already available.

## Success Criteria

- ✓ calls.open.json contains only open/forthcoming calls from last 9 months
- ✓ calls.closed.json contains only closed calls from dataset start to 3 months ago
- ✓ Both files updated on each fetch
- ✓ Separate changelogs generated for each stream
- ✓ Metadata tracks both streams independently
- ✓ All existing data preserved (no calls lost in migration)
- ✓ Freshness checks work for each stream
- ✓ Error in one stream doesn't affect the other
