## ADDED Requirements

### Requirement: CLI provides command-line interface
The package SHALL expose a CLI tool (`cordis-data`) that can be invoked from the terminal to trigger data fetching and status operations.

#### Scenario: fetch-calls command exists
- **WHEN** user runs `cordis-data fetch-calls`
- **THEN** the CLI executes the calls fetcher with default settings

#### Scenario: fetch-projects command exists
- **WHEN** user runs `cordis-data fetch-projects`
- **THEN** the CLI executes the projects fetcher with default settings

#### Scenario: status command exists
- **WHEN** user runs `cordis-data status`
- **THEN** the CLI displays metadata about the data (last fetch timestamps, total records, freshness)

### Requirement: CLI accepts options
The CLI SHALL accept command-line options to customize behavior (e.g., full history, filter by years).

#### Scenario: fetch-calls accepts --full-history
- **WHEN** user runs `cordis-data fetch-calls --full-history`
- **THEN** the CLI fetches all available data instead of the last 90 days

#### Scenario: fetch-projects accepts --years
- **WHEN** user runs `cordis-data fetch-projects --years=2`
- **THEN** the CLI fetches projects only for calls closed in the last 2 years

### Requirement: CLI is discoverable
The CLI tool entry point SHALL be registered in `pyproject.toml` so it is available system-wide after installation.

#### Scenario: cordis-data command is in PATH
- **WHEN** `cordis-data --help` is run from any directory
- **THEN** help text is displayed (command is found in PATH)

### Requirement: CLI output is clear and informative
CLI commands SHALL produce clear progress messages and summaries to stdout/stderr.

#### Scenario: Fetch command logs progress
- **WHEN** `cordis-data fetch-calls` runs
- **THEN** progress messages are printed (total calls, page counts, changes summary, final file size)
