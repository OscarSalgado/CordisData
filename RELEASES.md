# Releases

## [Unreleased]

### Major Changes

#### Deprecated CallsFetcher Removed
- **BREAKING**: `CallsFetcher` class removed from `cordis_data.data` module
  - Marked as DEPRECATED, now fully removed
  - Functionality split: use `OpenCallsFetcher` for active calls, `ClosedCallsFetcher` for closed calls
  - CLI command `cordis-data fetch-calls` now orchestrates both fetchers sequentially

- **Migration**: Update code to use new fetchers
  ```python
  # Old (no longer works)
  from cordis_data.data import CallsFetcher
  fetcher = CallsFetcher()
  
  # New
  from cordis_data.data.open_calls import OpenCallsFetcher
  from cordis_data.data.closed_calls import ClosedCallsFetcher
  
  open_fetcher = OpenCallsFetcher()
  closed_fetcher = ClosedCallsFetcher()
  open_fetcher.main()
  closed_fetcher.main()
  ```

- **CLI Behavior Change**: `cordis-data fetch-calls` now outputs to separate files
  - Output paths: `data/calls/open.jsonl.gz` and `data/calls/closed.jsonl.gz`
  - Changelog paths: `data/calls/changelog/open/YYYY-MM-DD.json` and `data/calls/changelog/closed/YYYY-MM-DD.json`
  - Metadata keys updated: `calls_open_fetched_at`, `calls_closed_fetched_at` (was `calls_fetched_at`)

#### Data Format Reorganization & JSONL.GZ Compression
- **BREAKING**: Data file paths have changed
  - `data/calls.open.json` → `data/calls/open.jsonl.gz`
  - `data/calls.closed.json` → `data/calls/closed.jsonl.gz`
  - `data/committees/documents.json` → `data/committees/documents.jsonl.gz`
  - `data/changelog/open/` → `data/calls/changelog/open/`
  - `data/changelog/closed/` → `data/calls/changelog/closed/`

- **Compression**: All call and document data is now stored in JSONL.GZ format
  - 85% reduction in file size (55MB → ~8MB for closed calls)
  - One JSON record per line, compressed with gzip
  - ~17ms decompression time
  - UTF-8 normalized to NFC canonical form

- **Migration**: Automatic on first fetch
  - Old `*.json` files are automatically converted to new format
  - Old files are archived as `*.json.bak` for safety
  - Can be deleted after verification (keep for 1-2 fetch cycles)

### Features

- New compression utilities: `JSONLGzipWriter`, `JSONLGzipReader`
  - Stream reading support (memory-efficient for large files)
  - UTF-8 NFC normalization
  - Compression ratio tracking

### Updates

- **OpenCallsFetcher**: Write to `data/calls/open.jsonl.gz`
  - Add `_migrate_old_format()` method for automatic migration
  - Path: `data/calls/open.jsonl.gz` (default)

- **ClosedCallsFetcher**: Write to `data/calls/closed.jsonl.gz`
  - Add `_migrate_old_format()` method for automatic migration
  - Path: `data/calls/closed.jsonl.gz` (default)

- **CommitteeDocumentsFetcher**: Write to `data/committees/documents.jsonl.gz`
  - Path: `data/committees/documents.jsonl.gz` (default)

- **ProjectsFetcher**: Read from new paths
  - Updated to read closed calls from `data/calls/closed.jsonl.gz`
  - No API changes

- **Documentation**:
  - Updated README.md with new data structure
  - Added comprehensive migration guide (`docs/migration-jsonl-gz.md`)
  - Examples for reading JSONL.GZ in Python, CLI, and other languages

### Migration Guide

See [Migration Guide](./docs/migration-jsonl-gz.md) for:
- Automatic migration details
- How to read the new format
- Cleanup instructions
- Rollback procedures

### Breaking Changes

Applications reading from old paths will break. Update to:

```python
# Old (no longer works)
with open('data/calls.open.json') as f:
    calls = json.load(f)

# New
from cordis_data.utils.compression import JSONLGzipReader
reader = JSONLGzipReader('data/calls/open.jsonl.gz')
calls = reader.read_all()
```

### Technical Details

- All UTF-8 strings normalized to NFC form
- Data integrity preserved (round-trip tested)
- Changelog files remain JSON (uncompressed) for easier inspection
- Backward compatibility: `.bak` files available if rollback needed
