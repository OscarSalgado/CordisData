## Why

EU comitology decisions affect Horizon funding priorities and project selection. Currently, researchers and administrators have no automated way to detect when new committee documents (agendas, decisions, reports) are published. Manual monitoring is labor-intensive and error-prone. This module enables continuous monitoring of committee documents from the past 3 months, automatically detecting new documents and alerting users of changes to keep stakeholders informed of relevant developments.

## What Changes

- **New CLI command**: `cordis-data monitor committees` to set up and manage committee monitoring
- **Configuration file**: `~/.cordis-data/committees-config.json` for persistent committee selection and notification preferences
- **New data storage**: `data/committees/` with `documents.json` (rolling 3-month window) and `changelog/YYYY-MM-DD.json` for all changes
- **GitHub Actions workflow**: Daily scheduled check for new committee documents with automatic alerts when documents are detected
- **Automatic alerts**: NEW documents trigger notifications via Slack/email/GitHub Issues
- **Change tracking**: Full changelog of all document changes with timestamps
- **Download integration**: Direct PDF access via discovered endpoint (`/core/api/integration/ers/...`)

## Capabilities

### New Capabilities

- `committee-monitoring`: Periodic fetch and change detection for EU comitology documents
- `committee-alerts`: Notification system for new/updated committee documents (Slack, email, GitHub Issues)
- `committee-config`: User configuration of monitored committees and alert preferences

## Impact

- **New module**: `src/cordis_data/data/committees/` (~400 lines)
- **New CLI subcommand**: `cordis-data monitor` group
- **New workflow**: `.github/workflows/monitor-committees.yml` for scheduled execution
- **Configuration**: User-level config in `~/.cordis-data/committees-config.json`
- **No breaking changes** to existing calls/projects functionality
- **No new external dependencies** (uses existing requests, click, etc.)
- **Data files**: `data/committees/documents.json` + changelog (same pattern as calls/projects)
