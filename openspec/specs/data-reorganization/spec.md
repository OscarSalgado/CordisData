# Data Reorganization Specification

## Purpose

Define the new directory structure for organizing data files by dataset type, improving clarity and maintainability of the data ecosystem.

## Requirements

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

## Data Structure

### Root Data Directory

```
data/
├── calls/                          # Calls data (open and closed)
│   ├── open.jsonl.gz             # Open/forthcoming calls (compressed)
│   ├── closed.jsonl.gz            # Closed/expired calls (compressed)
│   └── changelog/
│       ├── open/                  # Open calls changelog
│       │   ├── 2026-08-10.json
│       │   └── 2026-08-11.json
│       └── closed/                # Closed calls changelog
│           ├── 2026-08-10.json
│           └── 2026-08-11.json
├── committees/                    # Committee data
│   ├── documents.jsonl.gz         # Committee documents (compressed)
│   ├── config.json                # Configuration (uncompressed)
│   └── changelog/                 # Committee changelog
│       ├── 2026-08-10.json
│       └── 2026-08-11.json
└── projects.jsonl.gz              # Awarded projects (compressed)
```

### Legacy Paths (Deprecated)

```
data/
├── calls.open.json               # DEPRECATED → data/calls/open.jsonl.gz
├── calls.closed.json             # DEPRECATED → data/calls/closed.jsonl.gz
└── calls.open.json.bak           # Archive from migration
```

## Constraints

- Old files are preserved in `.bak` format during migration
- New paths are always `.jsonl.gz` for calls and committees data
- Old paths fail with clear deprecation message
- Migration is automatic on first run

## Success Criteria

- ✓ Data is organized into dataset-specific directories
- ✓ Old data is automatically migrated to new structure
- ✓ Web app can discover datasets by reading directory structure
- ✓ No data loss during migration
- ✓ Deprecation messages guide users to new paths
