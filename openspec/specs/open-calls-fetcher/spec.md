# OpenCallsFetcher Specification

## Purpose

Define the behavior of OpenCallsFetcher for incrementally fetching open/forthcoming calls from the SEDIA API and writing them to compressed JSONL.GZ format with UTF-8 normalization.

## Requirements

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

## Data Schema

### Open Calls Record Format (JSONL)

```json
{
  "id": "H2020-EIC-2021-SMEInstrument-01",
  "title": "EIC Pathfinder Open 2021",
  "status": "open",
  "publishDate": "2021-10-12T00:00:00Z",
  "deadline": "2021-11-25T17:00:00Z",
  "programme": "Horizon Europe",
  "budget": 5000000
}
```

**One record per line, gzip compressed in .jsonl.gz file**

## Constraints

- Output path: `data/calls/open.jsonl.gz` (required, no override)
- Format: JSONL (one record per line)
- Compression: gzip
- UTF-8: All strings normalized to NFC form
- Changelog path: `data/calls/changelog/open/YYYY-MM-DD.json`

## Success Criteria

- ✓ Output file is created at `data/calls/open.jsonl.gz`
- ✓ Each record is on a single line
- ✓ File is gzip compressed (~85% size reduction)
- ✓ UTF-8 special characters are preserved
- ✓ Changelog is written to new location
- ✓ Round-trip integrity verified (read back produces identical records)
