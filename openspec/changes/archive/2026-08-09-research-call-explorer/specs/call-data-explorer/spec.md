## ADDED Requirements

### Requirement: Search calls by multiple criteria

The system SHALL allow researchers to filter calls using independent search parameters (cluster, keywords, status, budget, deadline) and return matching results.

#### Scenario: Search by cluster and keyword
- **WHEN** researcher executes `cordis-data search-calls --cluster CL1 --keyword quantum`
- **THEN** system returns all calls in Cluster 1 with "quantum" in title/keywords/description

#### Scenario: Search by status
- **WHEN** researcher executes `cordis-data search-calls --status open`
- **THEN** system returns only open calls with valid deadlines

#### Scenario: Search with budget constraint
- **WHEN** researcher executes `cordis-data search-calls --budget-min 5000000`
- **THEN** system returns calls with budgetMax >= 5M

#### Scenario: Combined filters (AND logic)
- **WHEN** multiple filters are specified: `--cluster CL1 --keyword quantum --status open`
- **THEN** system returns only calls matching ALL criteria

### Requirement: View call details with enriched metadata

The system SHALL display complete call information including H2020 lineage and related project winners.

#### Scenario: View single call
- **WHEN** researcher executes `cordis-data view-call HORIZON-CL1-2024-001`
- **THEN** system displays: call metadata, deadline, budget, H2020 related calls, winning projects, committee info

#### Scenario: H2020 ancestry shown with confidence
- **WHEN** viewing a call that has H2020 ancestors
- **THEN** system shows projectId, acronym, match confidence, and matching strategy

#### Scenario: Show related winners
- **WHEN** viewing a call
- **THEN** system lists projects that won this call + their H2020 predecessors

### Requirement: Search projects with lineage

The system SHALL allow researchers to find projects and understand their H2020 ancestry.

#### Scenario: Search projects by team
- **WHEN** researcher executes `cordis-data search-projects --team "University of Example"`
- **THEN** system returns projects with that team, including H2020 ancestors

#### Scenario: Show H2020 lineage for project
- **WHEN** viewing a project with `--lineage` flag
- **THEN** system shows related H2020 projects with confidence scores

### Requirement: Export data in multiple formats

The system SHALL support exporting filtered data in JSON and CSV formats.

#### Scenario: Export filtered calls as JSON
- **WHEN** researcher executes `cordis-data export --calls --cluster CL1 --format json --output results.json`
- **THEN** system writes filtered calls to file in valid JSON format

#### Scenario: Export projects with H2020 lineage as CSV
- **WHEN** researcher executes `cordis-data export --projects --format csv --output projects.csv`
- **THEN** system writes projects with H2020 ancestors to CSV file

### Requirement: Output formatting

The system SHALL support both human-readable tables and machine-readable JSON output.

#### Scenario: Default table output
- **WHEN** researcher runs search command without format flag
- **THEN** system displays results in aligned table format (cluster, title, deadline, budget, status)

#### Scenario: JSON output for integration
- **WHEN** researcher specifies `--format json`
- **THEN** system returns full metadata JSON (for piping to other tools or web dashboard)

#### Scenario: Pagination for large results
- **WHEN** search returns >50 results
- **THEN** system displays first 50 with note "Run with --limit 1000 for more"
