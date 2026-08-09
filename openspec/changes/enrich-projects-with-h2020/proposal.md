## Why

Horizon Europe projects need historical context to understand research trajectories and team evolution. CORDIS H2020 (2014-2020) contains rich metadata about predecessor projects and teams that can illuminate Horizon opportunities. Currently, project records lack this lineage information, limiting researchers' ability to discover related work and track funding patterns across program cycles.

## What Changes

- **New H2020 enrichment layer** added to project fetching workflow
- **Multi-strategy matching** connects Horizon projects to H2020 antecedents (by projectId, acronym, team, similarity)
- **H2020 metadata** (organisations with roles, publications, datasets, keywords) merged into project records
- **Optional field** `h2020_related` added to projects.json when match found
- **Match confidence score** included to help users filter reliability

## Capabilities

### New Capabilities
- `h2020-enrichment`: Enrich Horizon projects with H2020 metadata and establish project lineage through multi-strategy matching (direct lookup, acronym, team overlap, title similarity, keyword matching)

### Modified Capabilities
- `project-fetching`: Workflow modified to include H2020 enrichment stage after CORDIS base enrichment

## Impact

**Code Changes:**
- New class `H2020Enricher` in `cordis_data/data/h2020.py`
- Updated `ProjectsFetcher.main()` to call H2020 enrichment
- New CORDIS H2020 API client method

**Data Changes:**
- `projects.json` adds optional field `h2020_related` (only when match found)
- New schema for project records with H2020 lineage

**Dependencies:**
- No new external dependencies (uses existing CORDIS client)
- Performance: pre-loads H2020 project index for efficient matching

**Testing:**
- Unit tests for matching strategies
- Integration tests with ProjectsFetcher
