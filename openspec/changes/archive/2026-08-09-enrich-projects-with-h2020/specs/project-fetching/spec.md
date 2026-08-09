## MODIFIED Requirements

### Requirement: Project fetching and enrichment workflow

The project fetching workflow SHALL include H2020 enrichment as an additional enrichment stage after CORDIS enrichment.

**Previous behavior:** Projects were fetched from SEDIA, enriched with CORDIS metadata (objective, grantDoi), and written to projects.json.

**New behavior:** Projects are fetched from SEDIA, enriched with CORDIS metadata (objective, grantDoi), enriched with H2020 metadata (organisations, publications, datasets, keywords), and written to projects.json.

#### Scenario: H2020 enrichment stage executes after CORDIS
- **WHEN** ProjectsFetcher.main() completes CORDIS enrichment for all projects
- **THEN** H2020Enricher is invoked to enrich the full project list before writing to projects.json

#### Scenario: Projects are written with optional h2020_related field
- **WHEN** H2020 enrichment completes
- **THEN** projects with H2020 matches include `h2020_related` field in the output; projects without matches do not include the field

#### Scenario: H2020 enrichment failure does not block project fetch
- **WHEN** H2020 enrichment encounters an error (index load failure, matching timeout)
- **THEN** the system logs the error and continues writing projects.json without h2020_related fields (graceful degradation)

#### Scenario: Enrichment does not affect project merge logic
- **WHEN** writing projects.json with existing projects
- **THEN** merging by projectId continues unchanged; h2020_related is an optional field that does not affect uniqueness or ordering
