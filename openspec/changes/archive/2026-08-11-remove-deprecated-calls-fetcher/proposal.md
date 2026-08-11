## Why

`CallsFetcher` is explicitly marked DEPRECATED and duplicates functionality of `OpenCallsFetcher` + `ClosedCallsFetcher`. The recent JSONL.GZ refactor reorganized data to `data/calls/{open,closed}.jsonl.gz`, but `CallsFetcher` still writes to the old monolithic `data/calls.json` path, creating architectural inconsistency. Removing it simplifies the codebase, eliminates maintenance burden of legacy code, and aligns the CLI with the new data organization.

## What Changes

- **Removal**: Delete `src/cordis_data/data/calls.py` entirely (CallsFetcher class)
- **API Change**: Remove `CallsFetcher` from public API (`cordis_data/data/__init__.py`)
- **CLI Refactor**: Update `cordis-data fetch-calls` command to internally call both OpenCallsFetcher and ClosedCallsFetcher sequentially, writing to new paths
- **Test Cleanup**: Delete `tests/unit/test_data_calls.py` (CallsFetcher tests)
- **Test Updates**: Update `tests/unit/test_cli.py` and `tests/integration/test_end_to_end.py` to use new fetchers

## Capabilities

### New Capabilities
- `cli-unified-fetch`: CLI `fetch-calls` command that orchestrates both open and closed calls fetching with JSONL.GZ output

### Modified Capabilities
- `open-calls-fetcher`: No spec changes (already JSONL.GZ compliant)
- `closed-calls-fetcher`: No spec changes (already JSONL.GZ compliant)

## Impact

**Code Changes:**
- `src/cordis_data/data/` — Remove calls.py
- `src/cordis_data/data/__init__.py` — Remove CallsFetcher export
- `src/cordis_data/cli/__init__.py` — Refactor fetch_calls() command
- `tests/unit/test_data_calls.py` — Delete entire file
- `tests/unit/test_cli.py` — Update mocks/tests to use new fetchers
- `tests/integration/test_end_to_end.py` — Update integration tests

**APIs Affected:**
- **BREAKING**: `CallsFetcher` no longer available in `cordis_data.data` module
- **BREAKING**: `cordis-data fetch-calls` command output changes from `data/calls.json` to `data/calls/{open,closed}.jsonl.gz`

**Behavior Preserved:**
- Fetch logic (open, closed, merged)
- Changelog generation
- Metadata tracking
- Rate limiting
- HTML cleaning and transformation

**Benefits:**
- Eliminate duplicated code (CallsFetcher vs 2 new fetchers)
- Simplify architecture and reduce maintenance burden
- Full alignment with JSONL.GZ reorganization
- Cleaner CLI with clear separation of concerns (open vs closed)
