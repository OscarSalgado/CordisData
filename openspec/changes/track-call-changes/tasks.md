## 1. Change Detection Logic

- [x] 1.1 Create `ChangeEvent` class in `src/cordis_data/data/changelog.py` to represent single events (NEW, STATUS_CHANGED, FIELD_CHANGED, AUTO_CLOSED, METADATA_UPDATED)
- [x] 1.2 Implement `detect_changes()` function that compares existing_calls vs merged_calls and returns list of ChangeEvent objects
- [x] 1.3 Define RELEVANT_FIELDS constant (callStatus, deadline, title, budgetMin/Max, expectedGrants, keywords, actionType, programme, cluster)
- [x] 1.4 Handle edge cases: None values, whitespace changes, missing fields

## 2. Changelog Generation

- [x] 2.1 Create `generate_changelog()` function that takes existing_calls, merged_calls, marked_closed count and returns changelog dict
- [x] 2.2 Implement changelog structure with fetch_date, summary (total, new, changed, auto_closed), and events list
- [x] 2.3 For each event type, include only relevant snapshot fields in snapshot_after
- [x] 2.4 Add fetch_timestamp (ISO 8601 format) to changelog metadata

## 3. Integration with CallsFetcher

- [x] 3.1 Modify `CallsFetcher.main()` to call `generate_changelog()` after merge but before save
- [x] 3.2 Write changelog to `data/changelog/YYYY-MM-DD.json` alongside calls.json
- [x] 3.3 Create `data/changelog/` directory if it doesn't exist
- [x] 3.4 Add print statements documenting changelog creation (e.g., "Changelog: 12 new, 8 changed → data/changelog/2026-08-09.json")

## 4. Git Commit Integration

- [x] 4.1 Modify `.github/workflows/fetch-calls.yml` to include `data/changelog/*.json` in git add before commit
- [x] 4.2 Update commit message to include changelog stats (e.g., "Fetch calls: 12 new, 8 changed, 3 auto-closed")
- [x] 4.3 Verify that both calls.json and changelog file are committed in same commit

## 5. Archival & Cleanup

- [x] 5.1 Create `src/cordis_data/data/archival.py` with `cleanup_old_changelogs()` function
- [x] 5.2 Implement 90-day cutoff logic (delete files where date < today - 90 days)
- [x] 5.3 Add cleanup call to workflow (run after fetch succeeds) or as separate scheduled task
- [x] 5.4 Log which files were deleted (for audit)

## 6. Testing

- [x] 6.1 Write unit tests for `detect_changes()` with existing=[] (all new), merged has same calls (no change), mixed (some new, some changed)
- [x] 6.2 Test `detect_changes()` with actual field changes (status, budget, keywords) including old/new values
- [x] 6.3 Test `generate_changelog()` structure: check JSON keys, snapshot_after has only relevant fields
- [x] 6.4 Test workflow integration: mock CallsFetcher, verify changelog file exists and is valid JSON
- [x] 6.5 Test archival: create dummy changelog files with dates, run cleanup, verify >90-day files deleted

## 7. Documentation

- [x] 7.1 Add CHANGELOG.md section describing changelog format (event types, fields, examples)
- [x] 7.2 Add CLI help text for `fetch-calls` mentioning changelog generation
- [x] 7.3 Update README with note about `data/changelog/` directory and 90-day retention
- [x] 7.4 Add example queries (how to grep for NEW events, how to extract field changes)

## 8. Final Validation

- [x] 8.1 Run full test suite: pytest --cov to ensure no regressions
- [x] 8.2 Verify flake8 and pyright pass
- [x] 8.3 Manual test: run `python -m cordis_data.cli fetch-calls --force` locally, inspect generated changelog
- [x] 8.4 Verify changelog commits to git with correct message
- [x] 8.5 Test cleanup: wait for >90-day scenario or mock date to verify archival works
