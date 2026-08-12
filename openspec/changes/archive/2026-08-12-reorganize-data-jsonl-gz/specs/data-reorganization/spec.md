## ADDED Requirements

### Requirement: Organize data by dataset type
The system SHALL organize all data files into dataset-specific directories (`calls/`, `committees/`, etc.) with consistent internal structure, making it clear which datasets exist and improving maintainability.

#### Scenario: Calls dataset structure
- **WHEN** system writes calls data
- **THEN** files are written to `data/calls/` directory with subdirectories:
  - `data/calls/open.jsonl.gz` (open/forthcoming calls)
  - `data/calls/closed.jsonl.gz` (closed/expired calls)
  - `data/calls/changelog/open/` (open calls changelog history)
  - `data/calls/changelog/closed/` (closed calls changelog history)

#### Scenario: Committees dataset structure
- **WHEN** system writes committees data
- **THEN** files are written to `data/committees/` directory:
  - `data/committees/documents.jsonl.gz` (committee documents)
  - `data/committees/config.json` (configuration, uncompressed)
  - `data/committees/changelog/` (changelog history)

#### Scenario: Web app discovers datasets
- **WHEN** web app initializes
- **THEN** it reads from `data/calls/` and `data/committees/` with no ambiguity about which files are current vs. historical

### Requirement: Migrate existing data to new structure
The system SHALL provide a clear migration path for existing `calls.open.json` and `calls.closed.json` files to new organization, either via automated conversion or documented manual steps.

#### Scenario: Automated migration on first run
- **WHEN** fetcher detects old `calls.open.json` exists but `calls/open.jsonl.gz` does not
- **THEN** system converts old file to new location and format
- **AND** old file is archived or removed after successful conversion

#### Scenario: Backwards compatibility notice
- **WHEN** old paths are accessed
- **THEN** system logs a deprecation notice directing to new paths
- **AND** eventually old paths fail with clear error message
