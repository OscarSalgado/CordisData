## Context

Currently, `data/calls.open.json` (8.5 MB) and `data/calls.closed.json` (55 MB) sit in the data root with no organizational structure. Large JSON files require loading entire datasets into memory. Changelog files are scattered across `data/changelog/`, `data/changelog/open/`, `data/changelog/closed/`, and `data/committees/changelog/` with unclear ownership. UTF-8 characters from EU Commission documents (commas, dashes, accents) sometimes render as corrupted sequences when viewed in ASCII-limited tools.

The web app consumes these JSON files for visualization and management, but the large file sizes increase network bandwidth and client-side memory usage.

## Goals / Non-Goals

**Goals:**
- Reduce on-disk footprint of main datasets by 85% (55MB → ~8MB for closed calls) via JSONL.GZ compression
- Reorganize data directory by dataset type (calls, committees) for clarity and future scalability
- Normalize UTF-8 to canonical NFC form to prevent rendering issues across platforms
- Enable line-by-line reading of data without loading entire file to memory
- Maintain data integrity and compatibility with existing internal tools (ProjectsFetcher)
- Provide clear migration path from old to new structure

**Non-Goals:**
- Database migration (SQLite); remain with file-based format for simplicity
- Implement async streaming for web app (keep decompression simple and fast)
- Change API contracts or data model (internal structure, field names, values unchanged)
- Compress or reorganize other datasets (projects, unless explicitly added later)

## Decisions

### Decision 1: JSONL.GZ vs alternatives
**Choice**: Use JSONL.GZ (one record per line, gzip compressed) instead of single-file binary formats (Parquet, MessagePack) or database (SQLite).

**Rationale**: 
- JSONL preserves JSON format, keeping compatibility with existing tooling
- Gzip provides 85% compression comparable to Parquet but simpler to implement
- Human-readable (gunzip -c still produces readable JSON)
- Web app can decompress with standard libraries

**Alternatives considered**:
- Parquet: Smaller (~500KB), but requires pyarrow/pandas, columnar format not suited for calls (wide variety of fields per record)
- SQLite: Excellent for queries, but adds database infrastructure, migrating 55MB would require initialization
- MessagePack: Smaller binary, but less transparent than JSONL

### Decision 2: Directory organization - Dataset-based (Option 1)
**Choice**: Organize by dataset type: `data/calls/`, `data/committees/`, with changelog under each.

**Rationale**:
- Matches domain concepts: "calls" and "committees" are distinct datasets
- Scalable: adding "projects" becomes `data/projects/` with same pattern
- Clear ownership: each folder is self-contained

**Alternatives considered**:
- Temporal separation (data/current/, data/history/): Less clear for incremental discovery tasks
- Output vs internal: Adds complexity (two copies of same data)

### Decision 3: UTF-8 Normalization - NFC canonical form
**Choice**: Use Python's `unicodedata.normalize('NFC', string)` on all text fields before serialization.

**Rationale**:
- NFC is the W3C recommended form for web content
- Fixes rendering issues without losing semantic meaning
- Accented characters (é, à) stored as single codepoint instead of base + combining mark
- Most compatible with browsers and text editors

**Alternatives considered**:
- No normalization: Leaves rendering artifacts ("M-bM-^@M-^Y")
- ASCII-only stripping: Loses data (European Commission titles often contain accents)

### Decision 4: Compression strategy - Gzip vs brotli
**Choice**: Use gzip (Python's built-in `gzip` module).

**Rationale**:
- Standard library, no dependencies
- Decompression built into most HTTP clients (Content-Encoding: gzip)
- 17ms decompression time is fast enough
- Good compression ratio (85%)

**Alternatives considered**:
- Brotli: Slightly better compression (~80% of gzip), but requires additional library

### Decision 5: Migration strategy - In-place conversion on first fetch
**Choice**: When OpenCallsFetcher/ClosedCallsFetcher runs, detect old paths and convert to new format. Archive old files.

**Rationale**:
- Automatic, non-disruptive
- Preserves any existing data
- CLI fetch command does the work naturally

**Implementation**:
- Add method `_migrate_old_format()` to fetchers
- Before writing, check if `data/calls.open.json` exists but `data/calls/open.jsonl.gz` doesn't
- If so, read old JSON, convert to JSONL.GZ, write to new location, archive old file
- Add warning log: "Migrating calls.open.json to data/calls/open.jsonl.gz (old file moved to .bak)"

## Risks / Trade-offs

**[Risk] Breaking change for web app** 
→ Mitigation: Web app must be updated to read from `data/calls/open.jsonl.gz` instead of `data/calls.open.json`. Coordinate deployment: CLI writes new format, web app updated to read it.

**[Risk] Decompression overhead on every read**
→ Mitigation: 17ms is negligible. JSONL allows streaming (read one record at a time). Web app can cache decompressed data in localStorage or IndexedDB if needed.

**[Risk] UTF-8 normalization changes existing data byte representation**
→ Mitigation: Semantic meaning preserved (accents still render correctly). Document in changelog that this is normalization, not modification.

**[Risk] Migration from old format fails midway**
→ Mitigation: Use atomic writes (write to temp file, rename). If conversion fails, old file remains untouched, error is logged clearly.

**[Risk] Internal tools (ProjectsFetcher) break if paths not updated**
→ Mitigation: Update ProjectsFetcher._load_closed_calls() at same time as fetchers write to new location. Add unit tests to verify round-trip.

## Migration Plan

1. **Phase 1 (Develop & Test)**
   - Implement JSONL.GZ writing in OpenCallsFetcher and ClosedCallsFetcher
   - Implement JSONL.GZ reading in ProjectsFetcher
   - Add UTF-8 normalization to all fetchers
   - Test: verify compression ratio, decompression speed, data integrity
   - Test: ProjectsFetcher reads new format and extracts topic IDs correctly

2. **Phase 2 (Deploy CLI)**
   - Merge changes to main
   - Next CLI run will auto-migrate old files and write new format
   - Old `data/calls.open.json` → `data/calls.open.json.bak`

3. **Phase 3 (Update Web App)**
   - Update web app to read from `data/calls/open.jsonl.gz` (decompress + parse JSONL)
   - Test: verify data loads correctly, performance is acceptable
   - Deploy web app

4. **Phase 4 (Cleanup)**
   - After 1-2 fetch cycles and web app confirmed stable, remove `.bak` files
   - Update documentation to reference new paths

**Rollback**:
- If web app breaks: Fetch new data with CLI (creates .bak backup), restore `.bak`, revert web app
- If fetcher breaks: Restore `data/calls.*.bak`, fix code, retry

## Open Questions

1. **Should we compress with `calls.jsonl.gz` or keep `.json` filename?**
   - Current proposal: rename to `.jsonl.gz` for clarity
   - Alternative: keep `.json` but files are gzip compressed (less clear)
   - Recommendation: `.jsonl.gz` is clearer for downstream systems

2. **Should we also create uncompressed `.jsonl` files for debugging?**
   - Current proposal: only `.jsonl.gz`
   - Alternative: write both (doubles disk space)
   - Recommendation: Start with `.jsonl.gz` only; add uncompressed on demand if needed

3. **When to clean up old `.bak` files?**
   - Current proposal: after 1-2 successful fetch cycles
   - Recommendation: set a policy (e.g., clean up if new file exists and is valid for >1 day)
