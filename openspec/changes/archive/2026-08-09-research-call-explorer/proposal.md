## Why

Researchers need fast, exploratory access to funding calls and project data to identify opportunities and understand competitive landscape. Currently, data exploration requires loading JSON files or writing ad-hoc scripts. A CLI explorer tool reduces friction and enables researchers to discover patterns (calls by cluster, team history, H2020 lineage) without technical barriers.

## What Changes

- **New CLI commands** for searching and viewing calls, projects, and relationships
- **Search capabilities** across clusters, keywords, status, budget, dates
- **Data export** in JSON/CSV for downstream analysis
- **H2020 lineage discovery** — show Horizon projects with their H2020 predecessors
- **Committee integration** — correlate calls with governance bodies (when data available)
- No changes to existing data pipelines or schemas

## Capabilities

### New Capabilities
- `call-data-explorer`: CLI tool for researchers to search, filter, and view EU funding calls with enriched metadata (H2020 lineage, committee context, and historical winners)

### Modified Capabilities
(none)

## Impact

**Code Changes:**
- New module `cordis_data/cli/explorer.py` with search/filter/view/export functions
- Update CLI entry point to register new commands
- Dependency: may use libraries like `click` (already in project) and `tabulate` for pretty output

**Data Files:**
- Reads existing: `data/calls.json`, `data/projects.json`
- Optional: `data/committees/` if committees data exists (future integration)

**User Experience:**
- Researchers get self-service data exploration
- No new data entry required
- Complementary to planned web dashboard (other team)

**Testing:**
- Unit tests for search/filter logic
- Integration tests with sample data files
