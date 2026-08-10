# Design: Compact Changelog Implementation

## Changes Required

### 1. Update `src/cordis_data/data/changelog.py`

**Current structure:**
- `ChangeEvent` dataclass with snapshot, snapshot_after, all optional fields
- `generate_changelog()` returns full event dicts with snapshots
- RELEVANT_FIELDS filtering (still includes 28 fields)

**New structure:**

```python
@dataclass
class ChangeEvent:
    """Minimal audit event - no snapshots."""
    type: str              # NEW, CHANGED, STATUS_CHANGED, etc.
    reference: str         # topicId (calls) or documentReference (docs)
    name: str              # title (for human reference)
    old_value: Any = None  # only if status change
    new_value: Any = None  # only if status change
    changed_fields: list[str] = None  # only if multi-field change

def generate_compact_changelog_calls(
    existing_calls: list[dict],
    merged_calls: dict[str, dict],
    marked_closed: int
) -> dict[str, Any]:
    """Generate compact changelog (no snapshots)."""
    # Return minimal event dicts
    
def generate_compact_changelog_documents(
    existing_docs: list[dict],
    merged_docs: dict[str, dict]
) -> dict[str, Any]:
    """Generate compact changelog for documents."""
    # Return minimal event dicts
```

**Remove:**
- Snapshot extraction logic
- RELEVANT_FIELDS set (no field filtering needed)
- _get_snapshot_subset()
- snapshot/snapshot_after fields

### 2. Update `src/cordis_data/data/calls.py`

**In CallsFetcher.main():**

Change from:
```python
changelog = generate_changelog(existing_calls, merged_by_id, marked_closed)
```

To:
```python
from cordis_data.data.changelog import generate_compact_changelog_calls
changelog = generate_compact_changelog_calls(existing_calls, merged_by_id, marked_closed)
```

### 3. Update `src/cordis_data/data/committees/fetcher.py`

**In CommitteeDocumentsFetcher.save_changelog():**

Change from manually building changelog dict to:
```python
from cordis_data.data.changelog import generate_compact_changelog_documents
changelog = generate_compact_changelog_documents(existing_docs, fetched_docs)
changelog_file.write_text(json.dumps(changelog, indent=2, ensure_ascii=False))
```

### 4. Update tests

- `tests/unit/test_data_changelog.py`: Update assertions to not expect snapshots
- `tests/integration/test_committees_e2e.py`: Verify compact format
- Add new tests for compact format verification

## Implementation Order

1. Add new compact changelog functions to `changelog.py` (keep old ones for now)
2. Update calls.py to use new function
3. Update committees/fetcher.py to use new function
4. Update/add tests
5. Verify file size reduction
6. (Cleanup: optionally remove old generate_changelog function)

## Impact Assessment

- **File size**: 90% reduction expected
- **Breaking change**: No (old files coexist, new format forward-only)
- **Backward compat**: Readers must handle both old and new formats
- **Performance**: Slightly faster (less data to process)
- **Data loss**: No (all reference data stays in master files)

## Risk: Lost Historical Context

**Mitigation**: Old changelogs in archive have full snapshots. New format is audit-only. If someone needs full historical state, they reconstruct from old snapshots + changelog events.
