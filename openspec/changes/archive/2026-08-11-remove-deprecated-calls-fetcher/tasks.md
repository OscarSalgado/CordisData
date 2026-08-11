## 1. Update CLI Command

- [x] 1.1 Refactor `cordis_data/cli/__init__.py` `fetch_calls()` to orchestrate `OpenCallsFetcher` and `ClosedCallsFetcher` sequentially
- [x] 1.2 Verify new command writes to `data/calls/open.jsonl.gz` and `data/calls/closed.jsonl.gz`
- [x] 1.3 Update CLI help text to document new output paths
- [x] 1.4 Test CLI command with real API calls to verify metadata and changelog generation

## 2. Remove Deprecated Code

- [x] 2.1 Delete `src/cordis_data/data/calls.py` entirely
- [x] 2.2 Remove `CallsFetcher` from `src/cordis_data/data/__init__.py` exports
- [x] 2.3 Delete `tests/unit/test_data_calls.py` (all CallsFetcher unit tests)
- [x] 2.4 Verify no other files import `CallsFetcher` directly

## 3. Update Unit Tests

- [x] 3.1 Update `tests/unit/test_cli.py` to mock `OpenCallsFetcher` and `ClosedCallsFetcher`
- [x] 3.2 Remove all tests that specifically test `CallsFetcher` behavior
- [x] 3.3 Add tests verifying sequential orchestration of open/closed fetchers
- [x] 3.4 Verify rate limiting and metadata tracking tests still pass

## 4. Update Integration Tests

- [x] 4.1 Update `tests/integration/test_end_to_end.py` to verify new output paths
- [x] 4.2 Add assertion that both `data/calls/open.jsonl.gz` and `data/calls/closed.jsonl.gz` exist after fetch
- [x] 4.3 Verify JSONL.GZ format and content structure match expected schema
- [x] 4.4 Test error handling when one fetcher fails

## 5. Code Quality and Documentation

- [x] 5.1 Run flake8/linters on modified files to ensure code quality
- [x] 5.2 Update CHANGELOG.md with breaking change notice and migration guidance
- [x] 5.3 Add docstring to refactored `fetch_calls()` command explaining new behavior
- [x] 5.4 Verify all tests pass: `pytest tests/`
