## MODIFIED Requirements

### Requirement: Read closed calls from JSONL.GZ file
ProjectsFetcher._load_closed_calls() SHALL read closed calls from `data/calls/closed.jsonl.gz`, parsing JSONL format (one record per line) and decompressing gzip, rather than reading `data/calls.closed.json`.

#### Scenario: Load closed calls from new location
- **WHEN** ProjectsFetcher._load_closed_calls() is called
- **THEN** it reads from `data/calls/closed.jsonl.gz` (not `data/calls.closed.json`)
- **AND** system decompresses gzip stream
- **AND** parses each line as a separate JSON record
- **AND** returns list of closed call dicts as before

#### Scenario: Extract topic IDs for project fetching
- **WHEN** closed calls are loaded
- **THEN** system extracts topic IDs from each record
- **AND** uses them to query SEDIA API for awarded projects
- **AND** behavior is identical to before (same topic ID extraction logic)

#### Scenario: Default path resolution
- **WHEN** no calls_path is provided to _load_closed_calls()
- **THEN** system uses default path: `data/calls/closed.jsonl.gz`
- **AND** gracefully handles missing file with clear error message
- **AND** suggests checking new data organization structure
