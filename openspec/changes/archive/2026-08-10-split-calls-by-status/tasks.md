# Implementation Tasks - Split Calls by Status

## Phase 1: Core Refactoring (8 tasks)

### CallsFetcher Refactoring (3 tasks)
- [x] Extract OpenCallsFetcher from CallsFetcher
  - Copy CallsFetcher → OpenCallsFetcher
  - Update filter logic: status in ["open", "forthcoming"], startDate >= (today - 9mo)
  - Update output_path default: data/calls.open.json
  - Update metadata keys: calls_open_fetched_at, calls_open_freshness_ttl_days

- [x] Extract ClosedCallsFetcher from CallsFetcher
  - Copy CallsFetcher → ClosedCallsFetcher
  - Update filter logic: status="closed", startDate <= (today - 3mo)
  - Update output_path default: data/calls.closed.json
  - Update metadata keys: calls_closed_fetched_at, calls_closed_freshness_ttl_days

- [x] Update CallsFetcher class documentation
  - Mark as deprecated (but keep for backward compatibility)
  - Point to OpenCallsFetcher and ClosedCallsFetcher
  - Keep main() working as before (calls both new fetchers)

### Data File Handling (2 tasks)
- [x] Update changelog generation for separate streams
  - Modify generate_compact_changelog_calls() to support stream parameter
  - Write to data/changelog/open/YYYY-MM-DD.json
  - Write to data/changelog/closed/YYYY-MM-DD.json

- [x] Ensure backward compatibility with calls.json (optional, can be skipped if deprecating)
  - Or: Document deprecation path for future removal

### Metadata Management (1 task)
- [x] Update metadata.py for dual-stream tracking
  - Add calls_open_fetched_at, calls_open_freshness_ttl_days
  - Add calls_closed_fetched_at, calls_closed_freshness_ttl_days
  - Update load_metadata() to initialize new keys
  - Update freshness check to work with stream-specific timestamps

### Merger Logic (2 tasks)
- [ ] Verify merge logic works correctly for split streams
  - Ensure calls.open.json merges correctly with new open calls
  - Ensure calls.closed.json merges correctly with new closed calls
  - Test that closed calls don't overwrite open calls in wrong file

- [ ] Update change detection for separate streams
  - Verify NEW/UPDATED/UNCHANGED detection works independently per stream

## Phase 2: CLI and Workflow Updates (4 tasks)

### CLI Commands (2 tasks)
- [x] Add fetch-open-calls command
  - Click command in src/cordis_data/cli/__init__.py
  - Calls OpenCallsFetcher.main()
  - Add --force flag

- [x] Add fetch-closed-calls command
  - Click command in src/cordis_data/cli/__init__.py
  - Calls ClosedCallsFetcher.main()
  - Add --force flag

### Status and Monitoring (1 task)
- [x] Update status command to show both streams
  - Display calls_open status (last fetch time, count, window)
  - Display calls_closed status (last fetch time, count, window)

### GitHub Actions Workflow (1 task)
- [x] Update .github/workflows/fetch-calls.yml
  - Add fetch-open-calls step
  - Add fetch-closed-calls step
  - Both run unconditionally (not skipped if one fails)
  - Commit logic handles both calls.open.json and calls.closed.json

## Phase 3: Testing (6 tasks)

### Unit Tests (3 tasks)
- [x] Test OpenCallsFetcher
  - Mock SEDIA API returning open+forthcoming calls
  - Verify filtering by status and startDate window
  - Verify merge and changelog generation
  - Test edge cases (no calls, all updated, etc.)

- [x] Test ClosedCallsFetcher
  - Mock SEDIA API returning closed calls
  - Verify filtering by status and startDate window (start <= 3mo ago)
  - Verify merge and changelog generation
  - Test edge cases (empty dataset, very old calls, etc.)

- [x] Test metadata management for dual streams
  - Verify calls_open_fetched_at updated after open fetch
  - Verify calls_closed_fetched_at updated after closed fetch
  - Verify independent freshness checks work

### Integration Tests (2 tasks)
- [x] Test end-to-end OpenCallsFetcher workflow
  - Fetch → merge → changelog → metadata
  - Verify calls.open.json is correctly populated
  - Verify changelog/open/YYYY-MM-DD.json created
  - Verify metadata updated

- [x] Test end-to-end ClosedCallsFetcher workflow
  - Fetch → merge → changelog → metadata
  - Verify calls.closed.json is correctly populated
  - Verify changelog/closed/YYYY-MM-DD.json created
  - Verify metadata updated

### CLI Tests (1 task)
- [x] Test fetch-open-calls and fetch-closed-calls CLI commands
  - Verify commands execute without error
  - Verify output files created in correct locations
  - Verify --force flag works

## Phase 4: Validation and Documentation (3 tasks)

### Data Validation (1 task)
- [ ] Verify no data loss in migration
  - Count calls in old calls.json
  - Count calls in new calls.open.json + calls.closed.json
  - Ensure totals match (may differ by window, but no loss)

### Documentation (1 task)
- [ ] Update docs and README
  - Document new fetch-open-calls and fetch-closed-calls commands
  - Explain use case for split (open for monitoring, closed for projects)
  - Update architecture diagram
  - Document deprecation of old CallsFetcher.main() (if applicable)

### Cleanup (1 task)
- [ ] Remove old calls.json from data/ directory
  - Backup to git history
  - Confirm no other code depends on it
  - Add note to CHANGELOG

---

## Summary

- **Total tasks**: 21
- **Phase 1 (Core)**: 8 tasks
- **Phase 2 (CLI)**: 4 tasks
- **Phase 3 (Testing)**: 6 tasks
- **Phase 4 (Validation)**: 3 tasks

**Estimated effort**: ~15-20 hours
