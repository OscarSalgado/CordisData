## Context

Daily fetch workflows update `calls.json` with the latest calls from SEDIA. The system currently computes summary metrics (X added, Y changed, Z unchanged) but discards the details of what specifically changed. This proposal adds a persistent changelog so researchers can track call evolution over time.

The CordisData codebase already has:
- `merge_calls()` and `summarize_changes()` that detect added/changed/unchanged
- `CallsFetcher.main()` that orchestrates fetch → transform → merge → save
- GitHub Actions workflow that runs daily and commits changes
- No external dependencies beyond standard library

## Goals / Non-Goals

**Goals:**
- Generate a daily changelog capturing meaningful changes to calls
- Store as JSON files by date (`data/changelog/YYYY-MM-DD.json`) for queryability
- Record event type, affected fields, old/new values (Level 3 detail)
- Include only relevant fields (status, deadline, budget, title, keywords, etc.)
- Automatically cleanup changelogs older than 90 days
- Commit changelog to git alongside `calls.json` for full audit trail

**Non-Goals:**
- Real-time alerting (will be added later if needed)
- Web UI or dashboard (focus on data persistence first)
- Compression—store as plain JSON initially
- Merging into a single cumulative file—daily snapshots are the model
- Tracking every metadata field—filter to relevant fields only

## Decisions

### 1. File Structure: Daily snapshots vs. cumulative log
**Decision**: Use daily snapshots (`data/changelog/YYYY-MM-DD.json`), one file per fetch date.

**Rationale**:
- Each fetch is independent and immutable → easy to reason about
- Simpler to archive/delete old entries (delete by date)
- Git history is natural (each file = one commit)
- Queryable: grep/jq work on a single file at a time
- No risk of unbounded growth in a single file

**Alternative considered**: Cumulative `changelog.json` appending daily entries. **Rejected**: harder to manage size, less clean git diffs, trickier to archive.

### 2. Event Schema: What information per event?
**Decision**: Capture event_type, reference, field names, old_value, new_value, and snapshot_after (only relevant fields).

**Rationale**:
- old/new values enable precise change detection (not just "it changed")
- snapshot_after provides context (status, deadline, budget at time of change)
- Only relevant fields (status, deadline, budget, etc.) to avoid bloat
- Sufficient for future alerting ("NEW call detected", "status changed to open")

**Alternative considered**: Store full before/after snapshots. **Rejected**: too much data, hard to diff, low signal-to-noise.

### 3. Relevant Fields Definition
**Decision**: Include callStatus, deadline, title, budgetMin/Max, expectedGrants, keywords, actionType, programme, cluster.

**Rationale**: These fields drive user interest (when can I apply? how much money? what's the scope?). Exclude portalUrl, programmeId (stable/derived).

### 4. Integration Point: When to generate changelog?
**Decision**: In `CallsFetcher.main()`, after merge but before saving `calls.json`.

**Rationale**:
- Changelog and calls.json are generated together—always in sync
- CallsFetcher already has `existing_by_key` and `merged_by_key` for comparison
- Same fetch instance has all needed context
- Can compute in one pass without reloading data

### 5. Git Commit Strategy
**Decision**: Commit changelog alongside `calls.json` in the same workflow step.

**Rationale**:
- Changelog and calls.json versions are paired
- Single git message documents the day's changes
- Preserves full history (git log data/changelog/ = timeline of changes)
- Simple workflow modification

### 6. Archival: Delete vs. compress
**Decision**: Delete changelogs older than 90 days (no compression initially).

**Rationale**:
- Simplicity: no gzip setup, no archive directory
- JSON is human-readable (helpful for debugging)
- 90 days = ~27MB at steady state on disk
- If archive needed later, can be added without breaking existing setup

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Changelog grows unbounded | Automated cleanup job deletes files >90 days old |
| Git repo size increases | ~50-200KB per file × 90 days ≈ 5-15MB—acceptable |
| Merge comparison is expensive | Only done once per fetch (not a bottleneck) |
| What counts as "changed"? | Exact equality check (old != new); whitespace/None handling in code |
| Different from calls.json timing | Both generated in same fetch instance → guaranteed in sync |

## Archival Implementation

```python
# Runs daily as part of fetch workflow or separate cron
import datetime
from pathlib import Path

changelog_dir = Path("data/changelog")
today = datetime.date.today()
cutoff = today - datetime.timedelta(days=90)

for log_file in changelog_dir.glob("*.json"):
    file_date = datetime.date.fromisoformat(log_file.stem)
    if file_date < cutoff:
        log_file.unlink()  # Delete old changelog
```

## Open Questions

1. **Event deduplication**: If the same field changes twice in one fetch (unlikely), should it be one event or two?
   - *Proposal*: Record both—let downstream code dedup if needed
2. **Whitespace in fields**: Should "AI, ML" vs "AI,ML" count as a change?
   - *Proposal*: Python `!=` is sensitive to whitespace; accept it as a change
3. **Alerting later**: When alerts are added, should they query git history or the changelog files?
   - *Proposal*: Query changelog files directly (no git dependency)
