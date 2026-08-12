## Why

The data directory is disorganized with large files (55MB, 8.5MB) in the root, consuming significant storage and bandwidth when served to the web app. Additionally, UTF-8 characters from European Commission documents render as corrupted sequences ("M-bM-^@M-^Y") in some contexts. Reorganizing into logical dataset folders and compressing to JSONL.GZ reduces file size by 85% (55MB→~8MB), improves web app loading performance, and normalizes UTF-8 for better compatibility.

## What Changes

- **Structure reorganization**: Group calls and committees into dedicated `data/calls/` and `data/committees/` folders
- **Compression**: Convert JSON files to JSONL.GZ format (629 records/lines, gzip compressed)
  - `calls.open.json` (8.5 MB) → `calls/open.jsonl.gz` (1.3 MB)
  - `calls.closed.json` (55 MB) → `calls/closed.jsonl.gz` (~8 MB estimated)
  - `committees/documents.json` → `committees/documents.jsonl.gz`
- **UTF-8 normalization**: Canonical NFC form to prevent rendering issues
- **Changelog organization**: Move changelog under each dataset folder (`calls/changelog/`, `committees/changelog/`)
- **Internal reader updates**: ProjectsFetcher and other internal tools read from new paths

## Capabilities

### New Capabilities
- `data-compression`: Convert large JSON datasets to JSONL.GZ format with gzip compression
- `data-reorganization`: Reorganize data directory by dataset type for clarity and maintainability
- `utf8-normalization`: Normalize UTF-8 characters to canonical NFC form

### Modified Capabilities
- `open-calls-fetcher`: Write to compressed `calls/open.jsonl.gz` instead of `calls.open.json`
- `closed-calls-fetcher`: Write to compressed `calls/closed.jsonl.gz` instead of `calls.closed.json`
- `projects-fetcher`: Read closed calls from new path `calls/closed.jsonl.gz`

## Impact

- **Files affected**: 
  - `src/cordis_data/data/open_calls.py` (OpenCallsFetcher.main)
  - `src/cordis_data/data/closed_calls.py` (ClosedCallsFetcher.main)
  - `src/cordis_data/data/projects.py` (ProjectsFetcher._load_closed_calls)
  - `src/cordis_data/cli/__init__.py` (CLI path references)

- **Breaking changes**: 
  - Web app must consume from new `data/calls/` paths and handle JSONL.GZ format
  - Internal tools must read from reorganized structure
  - Old `data/calls.open.json` and `data/calls.closed.json` paths deprecated

- **Benefits**: 
  - 85% reduction in file size for web app delivery
  - Faster decompression (~17ms)
  - Clearer data organization, easier to add new datasets
  - UTF-8 compatibility improvements
