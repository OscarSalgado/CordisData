# Committee Monitoring - Changelog

All notable changes to committee monitoring system are documented here.

## Format

Each daily changelog entry (YYYY-MM-DD.json) records:

```json
{
  "fetch_date": "2026-08-01",
  "fetch_timestamp": "2026-08-01T12:00:00Z",
  "summary": {
    "new": 5,
    "updated": 2,
    "total_events": 7
  },
  "events": [
    {
      "event_type": "NEW|UPDATED|UNCHANGED",
      "reference": "...",
      "topicId": "document_reference",
      "detected_at": "...",
      "field": "updateDate",  // For UPDATED events
      "old_value": "...",     // For UPDATED events
      "new_value": "...",     // For UPDATED events
      "snapshot": {...}       // Full document data
    }
  ]
}
```

## Event Types

- **NEW**: Document not present in previous fetch
  - Triggers alerts (Slack, GitHub Issues)
  - Full document in `snapshot`

- **UPDATED**: Document exists but metadata changed (version, updateDate, etc.)
  - Logged only, no alert
  - Change details in `field`, `old_value`, `new_value`
  - Full document in `snapshot_after`

- **UNCHANGED**: Document exists with no changes
  - Logged for completeness
  - Useful for audit trails

## Retention Policy

- **Active dataset** (`data/committees/documents.json`): Rolling 90-day window
  - Documents older than 90 days are purged
  - Reduces file size and keeps data fresh

- **Changelog** (`data/committees/changelog/YYYY-MM-DD.json`): 90 days
  - Automatically pruned on fetch (deletes files older than 90 days)
  - Provides complete audit trail
  - Can be archived separately for long-term retention

## Integration with CORDIS Data System

This changelog follows the same structure as:
- `data/calls/changelog/YYYY-MM-DD.json` - Funding calls changes
- `data/projects/changelog/YYYY-MM-DD.json` - Project data changes

All changelogs use:
- ISO-8601 timestamps with UTC timezone (Z suffix)
- `ChangeEvent` objects for consistency
- Event-based change tracking instead of snapshots

## Analysis Examples

### Find all NEW documents for a committee in a week

```python
import json
from pathlib import Path
from datetime import datetime, timedelta

changelog_dir = Path("data/committees/changelog")
start_date = datetime(2026, 8, 1)
end_date = start_date + timedelta(days=7)

new_docs = []
for changelog_file in sorted(changelog_dir.glob("*.json")):
    file_date = datetime.strptime(changelog_file.stem, "%Y-%m-%d")
    if start_date <= file_date <= end_date:
        with open(changelog_file) as f:
            data = json.load(f)
        for event in data.get("events", []):
            if event["event_type"] == "NEW":
                new_docs.append(event)

print(f"Found {len(new_docs)} new documents")
```

### Track update frequency for a document

```python
import json
from pathlib import Path

document_ref = "116169"
changelog_dir = Path("data/committees/changelog")

updates = []
for changelog_file in sorted(changelog_dir.glob("*.json")):
    with open(changelog_file) as f:
        data = json.load(f)
    for event in data.get("events", []):
        if event["topicId"] == document_ref:
            updates.append({
                "date": changelog_file.stem,
                "type": event["event_type"],
                "timestamp": event.get("detected_at")
            })

print(f"Document {document_ref}: {len(updates)} changes")
for update in updates:
    print(f"  {update['date']}: {update['type']}")
```

## Performance Metrics

Typical performance for committee monitoring:

| Operation | Time | Details |
|-----------|------|---------|
| Single committee fetch | < 1s | Includes API call + change detection |
| 100 committees | < 5s | Sequential API calls with 2 req/sec limit |
| 624 committees | < 5m | Full EU committee register (~3120 docs) |
| Change detection | < 100ms | For 1000+ documents |
| Changelog generation | < 50ms | JSON serialization + write |

### Rate Limiting

- **Client-side limit**: 2 requests/second (hard limit)
- **API timeout**: 10 seconds per request
- **Retry policy**: 3 attempts with exponential backoff

For 624 committees with ~5 docs/committee average:
- Total requests: ~624 (paginated)
- Time estimate: ~5 minutes
- Must complete within GitHub Actions timeout (standard: 6 hours)

## Monitoring Dashboard

Recommended metrics to track:

1. **Document velocity**: NEW documents per day
2. **Update frequency**: UPDATED vs UNCHANGED ratio
3. **API health**: 429 errors, timeouts, retries
4. **Storage usage**: Size of documents.json and changelog

Example query:
```python
import json
from pathlib import Path
from datetime import datetime, timedelta

def analyze_week(days=7):
    changelog_dir = Path("data/committees/changelog")
    now = datetime.utcnow()
    
    summary = {
        "new": 0,
        "updated": 0,
        "unchanged": 0,
        "days_scanned": 0
    }
    
    for i in range(days):
        date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        f = changelog_dir / f"{date}.json"
        if f.exists():
            data = json.loads(f.read_text())
            summary["days_scanned"] += 1
            for event in data.get("events", []):
                type_ = event["event_type"]
                summary[type_.lower()] = summary.get(type_.lower(), 0) + 1
    
    return summary

# Run: python -c "from analysis import analyze_week; print(analyze_week())"
```

## Long-term Data Retention

For keeping changelogs beyond 90 days:

```bash
# Archive old changelogs
mkdir -p data/committees/archive
find data/committees/changelog -mtime +90 -exec mv {} data/committees/archive/ \;

# Analyze archived data
python3 <<'EOF'
import json
from pathlib import Path

archive = Path("data/committees/archive")
for f in sorted(archive.glob("*.json")):
    data = json.loads(f.read_text())
    print(f"{f.stem}: {data['summary']}")
EOF
```

## API Changes

If the EU comitology-register API changes:

1. **Breaking changes**: Update `CommitteeDocumentsClient` endpoints
2. **Field changes**: Update `ChangeEvent` schema
3. **Rate limits**: Adjust `TokenBucket` parameters
4. **URL patterns**: Update PDF download endpoint in alerts

Current API version: comitology-register (2026-08 snapshot)
