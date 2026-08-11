## MODIFIED Requirements

### Requirement: Write open calls to JSONL.GZ file
OpenCallsFetcher SHALL write merged call records to `data/calls/open.jsonl.gz` in JSONL format (one JSON record per line) with gzip compression, with UTF-8 normalized to NFC form.

#### Scenario: Fetch and write open calls
- **WHEN** OpenCallsFetcher.main() runs
- **THEN** it fetches open/forthcoming calls from SEDIA API
- **AND** transforms and merges records as before
- **AND** writes to `data/calls/open.jsonl.gz` (not `data/calls.open.json`)
- **AND** each record is one line of JSON, gzip compressed

#### Scenario: UTF-8 normalization in output
- **WHEN** records contain special characters from API (smart quotes, dashes, accents)
- **THEN** system normalizes all strings to NFC form before writing
- **AND** JSON output is valid UTF-8 with no rendering artifacts

#### Scenario: Changelog organization
- **WHEN** changelog is generated
- **THEN** it is written to `data/calls/changelog/open/YYYY-MM-DD.json` (not `data/changelog/open/`)
- **AND** old changelog location is retired
