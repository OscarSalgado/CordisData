## Context

EU comitology documents are published via `https://ec.europa.eu/transparency/comitology-register/` with a REST API (discovered during exploration). Documents have metadata (dates, types, committee codes) and downloadable PDFs. Users need to monitor specific committees for new documents and receive alerts when changes occur.

Current state: CordisData fetches calls (SEDIA API) and projects (CORDIS API) but has no comitology monitoring capability. Users must manually check the EU portal.

## Goals / Non-Goals

**Goals:**
- Enable configuration of monitored committees (list of committee codes)
- Detect new and updated documents from configured committees
- Generate alerts via Slack, email, or GitHub Issues
- Store document metadata and changelog (following calls/projects pattern)
- Run as GitHub Actions workflow on schedule (daily recommended)
- Provide CLI interface for configuration management

**Non-Goals:**
- Full document parsing or content extraction
- Real-time monitoring (daily schedule acceptable)
- Integration with comité-specific workflows (e.g., voting procedures)
- Documents older than 3 months (rolling window, older documents are purged)

## Decisions

### 1. Configuration Storage
**Decision**: User-level JSON config in `~/.cordis-data/committees-config.json`
- **Why**: Persistent across sessions, user-specific, no repo pollution, matches common CLI patterns
- **Alternatives**: 
  - Repo-checked config → pollutes git history, less flexible for multiple users
  - Environment variables → unwieldy for lists of committees
  - Database → overkill for this use case
- **Structure**:
  ```json
  {
    "committees": [
      {"code": "C70408", "name": "Digital, Industry and Space", "enabled": true},
      {"code": "C70409", "name": "Health", "enabled": false}
    ],
    "alerts": {
      "enabled": true,
      "slack_webhook": "https://hooks.slack.com/...",
      "email": "researcher@example.com",
      "github_issues": true,
      "issue_repo": "owner/repo"
    },
    "last_check": "2026-08-09T12:00:00Z"
  }
  ```

### 2. Data Storage
**Decision**: Follow calls/projects pattern: `data/committees/documents.json` + daily changelog
- **Why**: Consistency with existing architecture, familiar to users, enables change tracking
- **Structure**: Same as calls/projects:
  - `data/committees/documents.json`: Full document list
  - `data/committees/changelog/YYYY-MM-DD.json`: Daily change events

### 3. Rolling 3-Month Window
**Decision**: Fetch documents from `now() - 90 days` to `now()`
- **Why**: 3 months captures most active committee discussions without excessive historical data
- **Calculation**: `start_date = datetime.now(UTC) - timedelta(days=90)`
- **Purge**: Documents older than 90 days are removed from documents.json on each fetch
- **API filter**: Pass `documentStartDate` to comitology API to limit results

### 4. Change Detection
**Decision**: Compare `documentReference` (unique per document, not version-specific)
- **NEW**: documentReference not in previous snapshot → trigger alert
- **UPDATED**: documentReference exists but version/updateDate changed → log only (no alert)
- **UNCHANGED**: No change in documentReference, version, updateDate → skip
- **Changelog events**: All events logged (NEW, UPDATED, UNCHANGED) for audit trail

### 4. Alert Mechanism - Automatic on New Documents
**Decision**: Multi-channel: Slack webhook (primary) + email (fallback) + GitHub Issues (optional)
- **When to alert**: ONLY when NEW documents are detected (not on updates)
- **Why new docs trigger alerts**: Users need to know immediately about new committee decisions/agenda items
- **Why not on updates**: Document updates (version increments) are less critical; tracked in changelog
- **Implementation**: 
  - Detect NEW documents via: documentReference not in previous snapshot
  - Slack: Webhook POST with document title, committee, download link, file list
  - Email: SMTP via environment variables (optional)
  - GitHub Issues: Create issue for each new document with summary

### 5. Alert Triggers Only on NEW Documents
**Decision**: Generate alerts ONLY for NEW documents, not for updates
- **Why**: New documents represent new committee activity requiring immediate attention
- **Updates**: Document version changes are tracked in changelog but don't trigger alerts
- **Alert content**: NEW events include documentReference, title, committee, all file links
- **Non-blocking**: Alert failures don't stop the fetch or changelog generation

### 6. GitHub Actions Workflow
**Decision**: Scheduled workflow (cron daily at 06:00 UTC) + manual trigger
- **Why**: Daily is sufficient granularity, 06:00 UTC catches EU business hours updates, manual trigger for testing
- **Workflow**: 
  ```
  1. Fetch committee documents from API
  2. Detect changes vs stored snapshot
  3. Generate alerts if NEW/UPDATED
  4. Commit updates to repo (if changes detected)
  5. Push changes
  ```
- **No blocking on alert failures**: Fetch completes even if Slack/email is down

### 7. CLI Architecture
**Decision**: New subcommand group `cordis-data monitor` with sub-commands
```
cordis-data monitor add-committee C70408 "Digital, Industry and Space"
cordis-data monitor list-committees
cordis-data monitor remove-committee C70408
cordis-data monitor config show
cordis-data monitor config set alerts.slack_webhook "..."
cordis-data monitor fetch          # Immediate fetch (useful for testing)
```
- **Why**: Clear, discoverable, follows Click conventions
- **Config file updates**: Commands modify `~/.cordis-data/committees-config.json`

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| API endpoint changes without notice | Version endpoint discovery regularly; document current pattern (2026-08-09) |
| Rate limiting from EU servers | Implement exponential backoff + cache (store etag/modification time) |
| Slack/email outage blocks workflow | Alerts are non-blocking; fetch completes regardless |
| User misconfigures committee codes | Validate codes against `GET /committees` endpoint before save |
| Duplicate alerts on re-runs | Store `last_check` timestamp, only process docs newer than that |
| Large changelog files | Auto-archive changelog files older than 90 days (same as calls) |

## Migration Plan

**Phase 1 (Initial Launch)**:
1. User installs/updates CordisData
2. First run: `cordis-data monitor add-committee C70408`
   - Validates committee exists
   - Saves to `~/.cordis-data/committees-config.json`
3. Optionally configure alerts: `cordis-data monitor config set alerts.slack_webhook "..."`

**Phase 2 (Workflow Setup)**:
1. User or admin adds `.github/workflows/monitor-committees.yml` to repo
2. Sets GitHub secrets: `CORDIS_SLACK_WEBHOOK`, `CORDIS_EMAIL`, etc. (if needed)
3. Workflow runs daily; commits changes to repo

**Rollback**: Delete workflow, config stays locally (user can disable via `monitor remove-committee`)

## Open Questions

1. **Email alerts**: Should we require SMTP setup or only support Slack/GitHub?
   - *Decision pending*: Slack is sufficient for v1; email can be Phase 2
2. **Backfill documents**: Should `monitor fetch` download all docs or only new?
   - *Proposed*: Only new (`documentStartDate >= last_check`); full history via CLI flag `--history`
3. **Document text extraction**: Should we extract text from PDFs or just metadata?
   - *Proposed*: Metadata only; PDF available for download via link in alert
4. **Cross-committee deduplication**: If same document appears in multiple committees, alert once or per committee?
   - *Proposed*: Alert per committee (users may monitor different committees)
