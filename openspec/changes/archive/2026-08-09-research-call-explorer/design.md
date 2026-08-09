## Context

Currently, researchers access funding data by loading JSON files directly or requesting reports. The data exists in `data/calls.json` and `data/projects.json` with rich enrichment (H2020 lineage, committee context). There is no dedicated UI or CLI for exploration — researchers are underserved by the current system.

A separate frontend team is building a web dashboard, so this explorer is complementary: a lightweight CLI for data inspection, not a visual tool.

## Goals / Non-Goals

**Goals:**
- Enable researchers to search calls by cluster, keywords, status, dates, budget
- Show enriched metadata (H2020 lineage, winning teams, committee context)
- Export results for downstream analysis
- Fast, zero-friction command-line interface
- Minimal dependencies (use stdlib + existing `click`)

**Non-Goals:**
- Beautiful visualization (web dashboard does this)
- Real-time sync or API webhooks
- User authentication or access control
- Data modification (read-only)
- Scraping or crawling (we load static files)

## Decisions

### 1. CLI Framework: Click

**Decision:** Use `click` library for CLI (already in project dependencies).

**Rationale:**
- Lightweight, clean syntax
- Excellent for parameter handling and help text
- Already used elsewhere in codebase
- Minimal learning curve

**Alternative:** Typer (rejected — adds dependency, overkill for this scope)

### 2. Data Loading: In-Memory Indices

**Decision:** Load calls.json and projects.json into memory at CLI startup. Build indices (by cluster, acronym, keywords, H2020 lineage) for fast filtering.

**Rationale:**
- Data is small (~10-100MB JSON)
- No need for database
- Startup cost minimal (< 1s)
- Enables instant search

**Alternative:** Query from files on-demand (rejected — slower, more I/O)

### 3. Search Granularity: Progressive Filtering

**Decision:** Support multiple independent filters (AND logic):
- `--cluster CL1`
- `--keyword quantum`
- `--status open`
- `--budget-min 1000000`
- `--deadline-after 2024-06-01`
Results = calls matching ALL filters.

**Rationale:**
- Researchers often have multiple constraints
- AND logic is intuitive (narrow down)
- Easy to implement and compose

**Alternative:** Complex query language (rejected — overkill, hard to use)

### 4. Output Format: Table + JSON

**Decision:** Two output modes:
- `--format table` (default): Pretty-printed table for humans
- `--format json`: Full JSON for programmatic use

**Rationale:**
- Table: readable, good for spot checks
- JSON: feeds to web dashboard or analysis scripts
- Both serve different audiences

**Alternative:** CSV only (rejected — table better for CLI, JSON for integration)

### 5. Command Structure

**Decision:** Separate top-level commands:
- `cordis-data search-calls` — find opportunities
- `cordis-data view-call <id>` — deep dive
- `cordis-data search-projects` — find winners
- `cordis-data view-project <id>` — project details with H2020 ancestors
- `cordis-data export` — batch export filtered data

**Rationale:**
- Clear separation: search ≠ view
- Discoverable: `cordis-data --help` shows all
- Composable: chain outputs to files or scripts

**Alternative:** Single `explore` command with subcommands (rejected — less discoverable)

### 6. H2020 Lineage Visualization

**Decision:** When viewing a Horizon project, show H2020 ancestors with confidence scores.

**Rationale:**
- Researchers want to know "who won before?"
- H2020 enrichment already done
- Confidence scores indicate reliability

**Implementation:**
```
Project: HORIZON-CL1-2024-ABC
├─ H2020 ancestors:
│  ├─ H2020-001 (confidence: 0.99, projectId_exact)
│  ├─ H2020-002 (confidence: 0.92, team_overlap)
│  └─ H2020-003 (confidence: 0.75, title_similarity)
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Large JSON files cause slow startup | Load time is typically <1s; document in help. Cache if needed later. |
| Researchers expect GUI, not CLI | Position as "data explorer"; web dashboard is the visual tool. |
| Complex query needs (nested AND/OR) | Start with simple AND filters; add complexity only if requested. |
| Data goes stale | CLI reads from disk; regenerate when fetch-calls runs. Document refresh cadence. |
| Committee data missing (future) | Skip committee integration in Phase 1; add hooks for Phase 2. |

## Migration Plan

**Phase 1 (this change):**
1. Implement CLI commands for calls/projects
2. Test with calls.json + projects.json (no committees)
3. Deploy: new CLI entry points available

**Phase 2 (future):**
- Add committee integration when data available
- Caching layer if performance needs scaling
- Shell completion (`bash-complete`, etc.)

**No rollback needed** — Pure addition, existing functionality unchanged.

## Open Questions

1. **Should we support regex or just exact/substring matching?**
   - Proposal: Start with substring (simpler); add regex if requested

2. **What about saved filters or queries?**
   - Proposal: Not in Phase 1; can add shell aliases

3. **Should we implement pagination for large result sets?**
   - Proposal: Not needed initially (<10K calls); add if needed

4. **How do we handle data staleness (when was this refreshed)?**
   - Proposal: Show metadata timestamp in output
