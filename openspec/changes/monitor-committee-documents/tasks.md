# Implementation Tasks

## Phase 1: Core Monitoring (15 tasks)

### API Client (3 tasks)
- [x] Create `src/cordis_data/data/committees/client.py` with `CommitteeDocumentsClient` class
  - Implement `fetch_documents()` with pagination support
  - Implement `fetch_document_detail()` for metadata + attachments
  - Implement `download_attachment()` with retry logic
  - Add rate limiting (max 2 req/sec)

- [x] Add error handling and retry logic
  - Exponential backoff for 429/500 errors
  - Connection timeout handling
  - Validate response structure

- [x] Add unit tests for CommitteeDocumentsClient
  - Test fetch_documents with mock API responses
  - Test pagination logic
  - Test error scenarios (404, timeout, rate limit)

### Data Processing (4 tasks)
- [x] Create `src/cordis_data/data/committees/fetcher.py` with `CommitteeDocumentsFetcher`
  - Implement `fetch()` method with rolling 3-month window
    - Calculate start_date = now() - 90 days
    - Pass to API as documentStartDate filter
  - Implement pagination loop + merge logic
  - Implement `detect_changes()` method using documentReference as key

- [ ] Implement change detection with alert trigger
  - Track documentReference as unique key (across all versions)
  - Detect NEW (documentReference not in previous) → trigger alert
  - Detect UPDATED (version/date changed) → log only, no alert
  - Generate ChangeEvent objects
  - Return list of NEW documents for alert system

- [ ] Implement rolling window + document purging
  - Remove documents older than 90 days from documents.json
  - Keep changelog files (for audit trail) but don't generate new entries for purged docs
  - Log purging events for debugging

- [ ] Implement changelog generation
  - Create `data/committees/changelog/YYYY-MM-DD.json`
  - Follow calls/projects changelog structure
  - Record ALL events (NEW, UPDATED, UNCHANGED) for complete audit trail

- [ ] Add unit tests for CommitteeDocumentsFetcher
  - Test change detection logic
  - Test merge with existing data
  - Test changelog generation
  - Test archival of old files

### Configuration (3 tasks)
- [ ] Create config file management module `src/cordis_data/data/committees/config.py`
  - Load/save `~/.cordis-data/committees-config.json`
  - Validate committee codes against API
  - Handle missing config file (create with defaults)

- [ ] Implement config validation
  - Verify committee codes exist in `/committees` endpoint
  - Validate alert configuration (slack webhook format, etc.)
  - Provide helpful error messages

- [ ] Add unit tests for config management
  - Test load/save operations
  - Test validation logic
  - Test default creation

### CLI (3 tasks)
- [ ] Create `src/cordis_data/cli/monitor.py` with Click command group
  - Implement `add-committee` command
  - Implement `list-committees` command
  - Implement `remove-committee` command
  - Implement `config show` command
  - Implement `config set` command
  - Implement `fetch` command (immediate fetch)

- [ ] Register monitor CLI group with main CLI
  - Add to `src/cordis_data/cli/__init__.py`
  - Test command discovery

- [ ] Add integration tests for CLI commands
  - Test add-committee with valid/invalid codes
  - Test list output format
  - Test config persistence across commands

### Integration (2 tasks)
- [ ] Update metadata tracking
  - Add `committees_fetched_at` and `committees_freshness_ttl_days` to metadata
  - Update `src/cordis_data/data/metadata.py`

- [ ] Create initial unit test suite
  - Mock API responses
  - Test end-to-end fetch + changelog flow

---

## Phase 2: Notifications (8 tasks)

### Alert System (4 tasks)
- [ ] Create `src/cordis_data/data/committees/alerts.py`
  - Implement `SlackAlertSender` class
  - Implement `EmailAlertSender` class (stub for Phase 2)
  - Implement `GitHubIssueAlertSender` class
  - Base `AlertSender` interface
  - Accept list of NEW documents to alert on

- [ ] Implement Slack notifications for NEW documents
  - Triggered automatically when NEW documents detected
  - Format message: Document title, committee, document type, file list with download URLs
  - Include metadata (committee code, creation date, language)
  - Handle webhook failures gracefully (non-blocking)

- [ ] Implement GitHub Issues integration for NEW documents
  - Create one issue per new document
  - Title: "[COMMITTEE] Document Type: Document Title"
  - Body: Committee info, document metadata, file list with download links
  - Non-blocking: Alert failures don't prevent fetch completion

- [ ] Add unit tests for alert senders
  - Mock HTTP requests
  - Test message formatting (NEW document format)
  - Test error handling (webhook down, invalid token)
  - Test non-blocking behavior

### GitHub Actions Workflow (3 tasks)
- [ ] Create `.github/workflows/monitor-committees.yml`
  - Scheduled run: Daily at 06:00 UTC
  - Manual trigger option
  - Install dependencies, run `cordis-data monitor fetch`
  - Commit + push changes if documents changed
  - Send alerts (Slack, GitHub Issues)

- [ ] Add workflow secrets configuration docs
  - Document required secrets: `CORDIS_SLACK_WEBHOOK`, `GH_TOKEN`
  - Provide setup instructions

- [ ] Add GitHub Actions integration tests
  - Test workflow trigger
  - Test commit logic (only on changes)

### User Documentation (1 task)
- [ ] Write user guide: `docs/committee-monitoring.md`
  - Quick start: Add first committee
  - Configure Slack webhook
  - Configure GitHub Issues
  - Manual fetch vs scheduled
  - Troubleshooting

---

## Phase 3: Polish & Optimization (5 tasks)

### Testing & Quality (3 tasks)
- [ ] Add integration tests
  - End-to-end test with real API calls (with VCR cassettes)
  - Test real GitHub workflow flow

- [ ] Performance testing
  - Benchmark with 624 committees (doesn't filter, just counts)
  - Ensure fetch completes within 5 minutes

- [ ] Add GitHub Actions workflow tests
  - Dry-run workflow
  - Validate secrets handling

### Documentation (2 tasks)
- [ ] Update main README.md
  - Add committee monitoring section
  - Link to detailed guide

- [ ] Write troubleshooting guide
  - Common issues: Invalid committee code, webhook errors, rate limits
  - Debug mode: `CORDIS_DEBUG=1`

---

## Summary

- **Total tasks**: 29
- **Phase 1 (Core)**: 16 tasks (required for functionality)
- **Phase 2 (Alerts)**: 8 tasks (required for notifications)
- **Phase 3 (Polish)**: 5 tasks (recommended for production)

**Key Features Implemented**:
- Rolling 3-month window (documents older than 90 days purged)
- Automatic alerts on NEW documents only (not on updates)
- Complete changelog with all events (audit trail)
- Multi-channel notifications (Slack, Email, GitHub Issues)
- Non-blocking alert failures

**Estimated effort**:
- Phase 1: 22 hours (API client, 3-month window, change detection, CLI)
- Phase 2: 10 hours (Automatic alerts, GitHub workflow)
- Phase 3: 5 hours (Documentation, testing, optimization)
- **Total**: ~37 hours for complete implementation
