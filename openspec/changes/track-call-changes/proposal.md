## Why

Currently, the data fetching system updates `calls.json` daily but only captures aggregate change counts (added/changed/unchanged). This loses **visibility into what specifically changed**—which calls are new, which changed status, which had budget updates. For researchers and stakeholders, understanding the evolution of funding opportunities is valuable: detecting new calls early, tracking status transitions, spotting budget revisions.

This change introduces a **daily changelog** that records every meaningful change with before/after values, creating an audit trail and enabling later analytics and alerting.

## What Changes

- **New daily changelog files** (`data/changelog/YYYY-MM-DD.json`) are generated during each fetch
- Each changelog captures **events with full context**: NEW calls, STATUS_CHANGED, FIELD_CHANGED, AUTO_CLOSED with old/new values
- **Only relevant fields** are recorded (callStatus, deadline, budget, title, keywords, etc.)—noise is filtered out
- Changelog is committed to git alongside updated `calls.json`, creating a versioned history
- Old changelogs (>90 days) are automatically archived/deleted to keep the directory manageable
- JSON format is flat and queryable: grep/jq-friendly for analysis

## Capabilities

### New Capabilities
- `changelog-generation`: Generate detailed event logs for each fetch showing what calls changed (new, status, budget, metadata updates)
- `changelog-archival`: Automated cleanup—archive or delete changelogs older than 90 days to prevent unbounded growth
- `change-detection`: Detect and classify specific types of changes (NEW, STATUS_CHANGED, FIELD_CHANGED, AUTO_CLOSED, METADATA_UPDATED)

### Modified Capabilities
- `call-fetching`: Enhanced—now also generates and commits changelog alongside calls.json

## Impact

- **Fetch workflow** (`.github/workflows/fetch-calls.yml`): Add changelog generation + commit step
- **CallsFetcher** (`src/cordis_data/data/calls.py`): Compute change events and write `data/changelog/YYYY-MM-DD.json`
- **Data directory**: New `data/changelog/` subdirectory, ~50-200KB per file, ~90 files at steady state
- **Git history**: New commit entries with changelog files—enables `git log data/changelog/` for audit
- **No breaking changes**: calls.json format unchanged, metadata.json unchanged
