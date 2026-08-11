## Context

The `CallsFetcher` class (in `src/cordis_data/data/calls.py`) is marked DEPRECATED and duplicates functionality that is now provided by `OpenCallsFetcher` and `ClosedCallsFetcher`. The recent JSONL.GZ data reorganization moved the authoritative data to `data/calls/{open,closed}.jsonl.gz`, but `CallsFetcher` still writes to the legacy monolithic path (`data/calls.json`), creating architectural inconsistency.

The CLI command `cordis-data fetch-calls` currently relies on `CallsFetcher`, and its behavior must be preserved while aligning with the new data organization.

## Goals / Non-Goals

**Goals:**
- Remove deprecated `CallsFetcher` class and all references to it
- Refactor `cordis-data fetch-calls` to orchestrate both `OpenCallsFetcher` and `ClosedCallsFetcher` sequentially
- Preserve fetch logic, changelog generation, metadata tracking, rate limiting, and HTML transformations
- Align CLI output with new JSONL.GZ paths (`data/calls/{open,closed}.jsonl.gz`)
- Clean up all associated tests and update tests to use new fetchers
- Reduce code duplication and maintenance burden

**Non-Goals:**
- Changing the underlying fetch logic for open or closed calls
- Modifying rate limiting or transformation behavior
- Creating a migration path for existing `data/calls.json` files (breaking change)
- Adding new fetch capabilities

## Decisions

**Decision 1: Sequential Orchestration in CLI**
- The CLI command will call `OpenCallsFetcher().fetch()` followed by `ClosedCallsFetcher().fetch()`
- **Rationale**: Maintains fetch semantics while leveraging existing, tested components. Each fetcher already handles JSONL.GZ format and metadata tracking.
- **Alternative Considered**: Create a shared base class or composition pattern — rejected as unnecessary given the simple orchestration needed.

**Decision 2: Data Output Location**
- `cordis-data fetch-calls` will write directly to `data/calls/{open,closed}.jsonl.gz` (matching `OpenCallsFetcher` and `ClosedCallsFetcher`)
- **Rationale**: Eliminates special handling and aligns with the canonical data location established by the JSONL.GZ refactor.
- **Alternative Considered**: Write to legacy path and provide migration script — rejected as introduces inconsistency and defers the breaking change.

**Decision 3: Test Strategy**
- Delete `tests/unit/test_data_calls.py` (CallsFetcher unit tests) entirely
- Update `tests/unit/test_cli.py` to mock `OpenCallsFetcher` and `ClosedCallsFetcher` instead of the removed `CallsFetcher`
- Update `tests/integration/test_end_to_end.py` to verify the new output paths and combined fetch behavior
- **Rationale**: Unit tests for the deprecated class are no longer relevant; CLI tests should verify orchestration.

## Risks / Trade-offs

**[Risk] Breaking Change to Public API**
- Removing `CallsFetcher` from `cordis_data.data` is a breaking change for downstream code that imports it
- **Mitigation**: Document clearly in release notes and CHANGELOG. Recommend downstream users use `OpenCallsFetcher` and `ClosedCallsFetcher` directly.

**[Risk] CLI Output Path Change**
- Scripts expecting `data/calls.json` will break
- **Mitigation**: Document the new output location in release notes and CLI help text. This is intentional — aligning with the JSONL.GZ refactor.

**[Risk] Loss of Merged Data**
- If `CallsFetcher` was merging open and closed data in-memory, that capability is removed
- **Mitigation**: The proposal and specs should clarify that open and closed calls are now separate files — consumers can re-merge if needed, but storage is now normalized.

## Migration Plan

1. Update CLI command to orchestrate new fetchers (see tasks for details)
2. Run updated CLI to generate new output files
3. Verify both `data/calls/open.jsonl.gz` and `data/calls/closed.jsonl.gz` are created correctly
4. Delete `src/cordis_data/data/calls.py` and test file
5. Update public API exports
6. Update integration tests to verify new behavior
7. Tag as breaking change in release notes

## Open Questions

- Should the CLI output a status message when writing to the new paths, or silently overwrite?
- Are there known downstream consumers of `CallsFetcher` that need migration guidance?
