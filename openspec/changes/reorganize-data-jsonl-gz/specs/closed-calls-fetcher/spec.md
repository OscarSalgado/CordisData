## MODIFIED Requirements

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
