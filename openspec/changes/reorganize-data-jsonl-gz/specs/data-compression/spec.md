## ADDED Requirements

### Requirement: Convert JSON to JSONL.GZ format
The system SHALL convert multi-line JSON arrays into JSONL (one JSON record per line) format and compress with gzip, reducing file size by approximately 85% while maintaining data integrity and enabling fast decompression (~17ms).

#### Scenario: Compress calls dataset
- **WHEN** fetcher writes calls data (open or closed)
- **THEN** system writes to `.jsonl.gz` file with one record per line, gzip compressed
- **AND** file size reduction is verified (original to compressed ratio)

#### Scenario: Verify decompression
- **WHEN** reader loads a `.jsonl.gz` file
- **THEN** system decompresses and parses each line as JSON record
- **AND** decompression completes in under 50ms for 8.5MB dataset

#### Scenario: Preserve data integrity
- **WHEN** data is compressed and decompressed
- **THEN** all 629+ records match original dataset exactly
- **AND** all UTF-8 characters remain valid after round-trip

### Requirement: Support JSONL format in readers
The system SHALL read JSONL.GZ files line-by-line, parsing each line as a separate JSON record without requiring the entire file to be loaded into memory.

#### Scenario: Stream JSONL records
- **WHEN** reader opens a `.jsonl.gz` file
- **THEN** system iterates records one per line without loading entire file to memory
- **AND** supports both gzip-compressed and uncompressed JSONL variants
