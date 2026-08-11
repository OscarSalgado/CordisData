## 1. Core Infrastructure: Compression & UTF-8 Utilities

- [x] 1.1 Create `src/cordis_data/utils/compression.py` with `JSONLGzipWriter` class
  - Write JSONL.GZ files (one record per line, gzip compressed)
  - Normalize UTF-8 to NFC form before serialization
  - Include compression ratio tracking

- [x] 1.2 Create `src/cordis_data/utils/compression.py` with `JSONLGzipReader` class
  - Read JSONL.GZ files line-by-line
  - Support both compressed (.gz) and uncompressed (.jsonl) variants
  - Handle encoding errors gracefully

- [x] 1.3 Add unit tests for compression utilities
  - Test: Round-trip integrity (write → read produces same data)
  - Test: Compression ratio is ~85% for calls data
  - Test: Decompression time < 50ms for 8.5MB
  - Test: UTF-8 normalization preserves all 43+ special characters

## 2. OpenCallsFetcher: Migration & JSONL.GZ Output

- [x] 2.1 Add migration method `_migrate_old_format()` to OpenCallsFetcher
  - Detect old `data/calls.open.json` exists
  - Read, convert to JSONL.GZ, write to `data/calls/open.jsonl.gz`
  - Archive old file to `data/calls.open.json.bak`
  - Log clear migration message

- [x] 2.2 Update `OpenCallsFetcher.main()` to write JSONL.GZ
  - Replace `json.dump()` with JSONLGzipWriter
  - Normalize UTF-8 (NFC) for all text fields before writing
  - Update output path: `data/calls/open.jsonl.gz`
  - Create `data/calls/` directory if doesn't exist

- [x] 2.3 Update changelog path in OpenCallsFetcher
  - Change from `data/changelog/open/` to `data/calls/changelog/open/`
  - Ensure parent directories are created

- [x] 2.4 Update CLI help text and docstrings
  - Change default output path in `--output` help
  - Document new .jsonl.gz format

- [ ] 2.5 Add unit tests for OpenCallsFetcher
  - Test: Output file is at `data/calls/open.jsonl.gz`
  - Test: Records can be read back with JSONLGzipReader
  - Test: UTF-8 special characters are preserved
  - Test: Migration from old format works correctly

## 3. ClosedCallsFetcher: Migration & JSONL.GZ Output

- [x] 3.1 Add migration method `_migrate_old_format()` to ClosedCallsFetcher
  - Detect old `data/calls.closed.json` exists
  - Read, convert to JSONL.GZ, write to `data/calls/closed.jsonl.gz`
  - Archive old file to `data/calls.closed.json.bak`
  - Log clear migration message

- [x] 3.2 Update `ClosedCallsFetcher.main()` to write JSONL.GZ
  - Replace `json.dump()` with JSONLGzipWriter
  - Normalize UTF-8 (NFC) for all text fields before writing
  - Update output path: `data/calls/closed.jsonl.gz`
  - Create `data/calls/` directory if doesn't exist

- [x] 3.3 Update changelog path in ClosedCallsFetcher
  - Change from `data/changelog/closed/` to `data/calls/changelog/closed/`
  - Ensure parent directories are created

- [x] 3.4 Update CLI help text and docstrings
  - Change default output path in `--output` help
  - Document new .jsonl.gz format

- [ ] 3.5 Add unit tests for ClosedCallsFetcher
  - Test: Output file is at `data/calls/closed.jsonl.gz`
  - Test: Records can be read back with JSONLGzipReader
  - Test: File size reduction is ~85% (55MB → ~8MB)
  - Test: Migration from old format works correctly

## 4. CommitteeDocumentsFetcher: Reorganize & Compress

- [ ] 4.1 Update CommitteeDocumentsFetcher to write JSONL.GZ
  - Currently writes to `data/committees/documents.json`
  - Update to write to `data/committees/documents.jsonl.gz`
  - Normalize UTF-8 (NFC) for all text fields
  - Create `data/committees/` directory if doesn't exist

- [ ] 4.2 Update changelog path in CommitteeDocumentsFetcher
  - Change from `data/committees/changelog/` to `data/committees/changelog/`
  - (Already organized, just ensure it's under committees/)

- [ ] 4.3 Add unit tests for CommitteeDocumentsFetcher
  - Test: Output file is at `data/committees/documents.jsonl.gz`
  - Test: Records can be read back

## 5. ProjectsFetcher: Read from New Path

- [x] 5.1 Update `ProjectsFetcher._load_closed_calls()` to read JSONL.GZ
  - Change from: `open("data/calls.closed.json")`
  - Change to: `gzip.open("data/calls/closed.jsonl.gz", "rt")`
  - Parse each line as JSON record: `[json.loads(line) for line in f]`
  - Handle file not found with clear error message

- [x] 5.2 Update default path constant
  - Change from: `project_root / "data" / "calls.closed.json"`
  - Change to: `project_root / "data" / "calls" / "closed.jsonl.gz"`

- [ ] 5.3 Add unit tests for ProjectsFetcher
  - Test: Loads closed calls from new path
  - Test: Extracts topic IDs correctly for project fetching
  - Test: Behavior is identical to before (same topic lists)

## 6. CLI Integration & Documentation

- [x] 6.1 Update all CLI references to old paths
  - `src/cordis_data/cli/__init__.py`: update help texts, docstrings
  - Search for hardcoded `calls.open.json`, `calls.closed.json` references

- [ ] 6.2 Update `README.md` and docs
  - Document new data structure (calls/, committees/)
  - Show example of reading JSONL.GZ files
  - Note UTF-8 normalization

- [ ] 6.3 Add migration guide
  - Explain old vs new paths
  - Note `.bak` files are safe to delete after verification

## 7. Integration Testing & Validation

- [ ] 7.1 Run full test suite
  - All unit tests pass
  - Integration tests: fetch calls, verify structure, verify ProjectsFetcher can read

- [ ] 7.2 Manual validation
  - Run: `cordis-data calls open --force` (writes calls/open.jsonl.gz)
  - Run: `cordis-data calls closed --force` (writes calls/closed.jsonl.gz)
  - Verify: files exist at correct paths
  - Verify: file sizes are ~85% smaller than originals
  - Verify: projects fetch works (reads closed calls from new path)

- [ ] 7.3 Verify UTF-8 normalization
  - Decompress a sample file: `gunzip -c data/calls/open.jsonl.gz | head -1 | jq .`
  - Check for special characters (é, °, –) render correctly
  - Verify no "M-bM-^@M-^Y" corruption artifacts

- [ ] 7.4 Verify backward compatibility
  - If old files present, migration runs automatically
  - `.bak` files are created and old data is preserved
  - Migration is logged clearly

## 8. Cleanup & Release

- [ ] 8.1 Verify old `.bak` files can be safely deleted
  - Run fetch cycles 2-3 times
  - Confirm new format is stable
  - Document policy (delete after 1 week / 2 fetches)

- [x] 8.2 Commit and create PR
  - Clear commit message: "refactor: reorganize data to JSONL.GZ and normalize UTF-8"
  - Reference proposal, design, specs

- [ ] 8.3 Update CHANGELOG
  - Document breaking changes (new paths)
  - Document benefits (85% compression, UTF-8 normalization)
  - Note migration is automatic

- [ ] 8.4 Mark change complete in OpenSpec
  - After PR merged, archive this change: `openspec archive --change "reorganize-data-jsonl-gz"`
