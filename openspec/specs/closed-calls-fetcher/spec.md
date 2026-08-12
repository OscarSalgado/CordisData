# ClosedCallsFetcher Specification

## Purpose

Define the behavior of ClosedCallsFetcher for incrementally fetching closed/expired calls from the comitology-register API and writing them to compressed JSONL.GZ format with UTF-8 normalization.

## Requirements

### Requirement: Write closed calls to JSONL.GZ file
ClosedCallsFetcher SHALL write merged call records to `data/calls/closed.jsonl.gz` in JSONL format (one JSON record per line) with gzip compression, with UTF-8 normalized to NFC form.

#### Scenario: Fetch and write closed calls
- **WHEN** ClosedCallsFetcher.main() runs
- **THEN** it fetches closed calls from comitology-register API
- **AND** transforms and merges records as before
- **AND** writes to `data/calls/closed.jsonl.gz` (not `data/calls.closed.json`)
- **AND** each record is one line of JSON, gzip compressed
- **AND** file size reduces from 55MB to approximately 8MB

#### Scenario: UTF-8 normalization in output
- **WHEN** records contain special characters from EU Commission PDFs (diacritics, smart punctuation)
- **THEN** system normalizes all strings to NFC form before writing
- **AND** JSON output is valid UTF-8 with no rendering artifacts

#### Scenario: Changelog organization
- **WHEN** changelog is generated
- **THEN** it is written to `data/calls/changelog/closed/YYYY-MM-DD.json` (not `data/changelog/closed/`)
- **AND** old changelog location is retired

### Requirement: Committee documents compression
CommitteeDocumentsFetcher SHALL also write committee documents to `data/committees/documents.jsonl.gz` with same compression and UTF-8 normalization.

#### Scenario: Write committee documents
- **WHEN** committee documents are fetched and processed
- **THEN** they are written to `data/committees/documents.jsonl.gz`
- **AND** each document reference is one line of JSON
- **AND** UTF-8 is normalized to NFC form

## Data Schema

### Closed Calls Record Format (JSONL)

```json
{
  "id": "HORIZON-CL5-2020-D1-01",
  "title": "European Green Cities",
  "status": "closed",
  "publishDate": "2020-03-15T00:00:00Z",
  "deadline": "2020-07-23T17:00:00Z",
  "programme": "Horizon Europe",
  "budget": 10000000,
  "topicId": "HORIZON-CL5-2020-D1-01-01"
}
```

### Committee Documents Record Format (JSONL)

```json
{
  "id": "doc-12345",
  "title": "Committee Meeting Minutes",
  "date": "2026-08-10T00:00:00Z",
  "type": "minutes",
  "content": "..."
}
```

**One record per line, gzip compressed in .jsonl.gz file**

## Constraints

- Output path for closed calls: `data/calls/closed.jsonl.gz` (required)
- Output path for committee documents: `data/committees/documents.jsonl.gz` (required)
- Format: JSONL (one record per line)
- Compression: gzip
- UTF-8: All strings normalized to NFC form
- File size reduction: ~85% (55MB → ~8MB for closed calls)
- Changelog path: `data/calls/changelog/closed/YYYY-MM-DD.json`

## Success Criteria

- ✓ Output file is created at `data/calls/closed.jsonl.gz`
- ✓ File size reduction is ~85% (55MB → ~8MB)
- ✓ Each record is on a single line
- ✓ File is gzip compressed
- ✓ UTF-8 special characters are preserved
- ✓ Committee documents written to `data/committees/documents.jsonl.gz`
- ✓ Changelog is written to new location
- ✓ Round-trip integrity verified (read back produces identical records)
