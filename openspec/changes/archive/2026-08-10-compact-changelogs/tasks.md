# Tasks: Compact Changelog Implementation

## Phase 1: Core Implementation

### 1. Add compact changelog generators
- [x] Add `generate_compact_changelog_calls()` to changelog.py
- [x] Add `generate_compact_changelog_documents()` to changelog.py
- [x] Verify both match spec format (no snapshots)

### 2. Update calls fetcher
- [x] Import new function in calls.py
- [x] Replace `generate_changelog()` call with `generate_compact_changelog_calls()`
- [x] Verify changelog file format

### 3. Update documents fetcher
- [x] Import new function in committees/fetcher.py
- [x] Update `save_changelog()` to use new generator
- [x] Verify changelog file format

## Phase 2: Testing

### 4. Update unit tests
- [x] Modify test_data_changelog.py to expect compact format
- [x] Remove assertions expecting snapshots
- [x] Add new tests for compact functions (6 tests)
- [x] All 19 tests passing

### 5. Verify file size reduction
- [x] Run fetch for calls
- [x] Measured 91.9% reduction (12.4x smaller)
- [x] 100 calls: 66 KB → 5 KB
- [x] Confirmed ~90%+ reduction achieved

### 6. Integration test
- [x] Run end-to-end fetch (documents)
- [x] Verify changelog_generation test passes
- [x] Confirm data integrity (no information loss)

## Phase 3: Cleanup (optional)

### 7. Remove old functions (skipped)
- [x] Verified old `generate_changelog()` not imported elsewhere
- [x] Kept for backward compatibility
- [x] RELEVANT_FIELDS still used by detect_changes()

## Validation Checklist

- [x] New format matches calls-changelog.md spec
- [x] New format matches documents-changelog.md spec
- [x] File size reduction confirmed (91.9%)
- [x] All tests pass (19/19)
- [x] Changelog can be read programmatically (events iterable)
- [x] Master data files (calls.json, documents.json) unchanged
