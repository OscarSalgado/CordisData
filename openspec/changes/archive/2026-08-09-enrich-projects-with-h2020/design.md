## Context

Current `ProjectsFetcher` workflow:
1. Fetches awarded projects from SEDIA (NONH2020_PROD) filtered by topic IDs
2. Enriches with CORDIS API (objective, grantDoi) using rate-limited concurrent requests
3. Writes to `data/projects.json` with merge/dedup by projectId

H2020 is a separate historical dataset (2014-2020, now closed) with richer metadata per project including organisation details, publications, datasets. The goal is to enhance Horizon project records by connecting them to predecessor H2020 projects where relationships exist.

## Goals / Non-Goals

**Goals:**
- Connect Horizon projects to related H2020 projects via multi-strategy matching
- Enrich project records with H2020 metadata (organisations, publications, datasets, keywords)
- Provide match confidence scores so users can filter by reliability
- Keep enrichment optional (graceful if no H2020 match found)
- Maintain separation of concerns (new H2020Enricher class, not inline in ProjectsFetcher)

**Non-Goals:**
- Do NOT implement Phase 2 features (scraping, real-time updates, web portals)
- Do NOT modify existing SEDIA/CORDIS fetching logic
- Do NOT require additional external API keys
- Do NOT handle H2020 projects that have no Horizon equivalent (this is historical data only)

## Decisions

### 1. Separate H2020Enricher Class

**Decision:** Create new class `H2020Enricher` in `cordis_data/data/h2020.py`, not inline in ProjectsFetcher.

**Rationale:**
- Single responsibility: H2020 matching/enrichment logic isolated
- Testable in isolation
- Pluggable: can be enabled/disabled, reused in other contexts
- Cleaner separation from existing project fetching

**Alternative:** Inline in ProjectsFetcher methods (rejected — too complex, harder to test)

### 2. Multi-Strategy Matching (Aggressive)

**Decision:** Try multiple matching strategies in order, return best match (highest confidence):
1. Direct projectId match (confidence: 0.99)
2. Acronym exact match (confidence: 0.95)
3. Team overlap (3+ organisations common, confidence: 0.75–0.85)
4. Title similarity (Levenshtein + team context, confidence: 0.70–0.80)
5. Keywords/subject overlap (confidence: 0.60–0.75)

**Rationale:**
- Aggressive matching maximizes coverage while tracking confidence
- Users can filter by confidence threshold to avoid false positives
- Progressive degradation: exact matches first, fuzzy fallback
- Early exit once high-confidence match found (performance)

**Alternative:** Conservative (only exact matches, rejected — too narrow, misses lineage)

### 3. Pre-loaded H2020 Index

**Decision:** Load all H2020 projects into memory once at startup, cache for matching.

**Rationale:**
- H2020 is static (ended 2020, no live updates)
- Avoids repeated API calls; matching is instant
- Performance: ~30K projects is manageable in memory
- Simplifies error handling (no network calls during enrichment)

**Alternative:** Live lookup per project (rejected — unnecessary network overhead)

### 4. Optional h2020_related Field

**Decision:** Add `h2020_related` field only when match found; absent if no match.

**Schema:**
```json
{
  "projectId": "101...",
  "h2020_related": {
    "projectId": "987...",
    "acronym": "PREV-PROJECT",
    "matchConfidence": 0.92,
    "matchStrategy": "team_overlap + title_similarity",
    "organisations": [
      { "name": "...", "country": "DE", "role": "coordinator" }
    ],
    "publications": [...],
    "datasets": [...],
    "keywords": [...]
  }
}
```

**Rationale:**
- Backward compatible (optional field)
- Keeps projects.json size manageable (only populated when valuable)
- Clear structure for users to evaluate match quality

**Alternative:** Always include (even if null, rejected — pollutes output)

### 5. Integration Point in ProjectsFetcher.main()

**Decision:** Call H2020 enrichment AFTER CORDIS enrichment but BEFORE writing projects.json.

**Flow:**
```
1. Fetch Horizon projects (SEDIA)
2. Enrich with CORDIS (objective, grantDoi)
3. [NEW] Enrich with H2020 (organisations, publications, etc.)
4. Merge with existing projects.json
5. Write output
```

**Rationale:**
- H2020 is complementary, not blocking
- Doesn't slow down SEDIA/CORDIS fetches
- Projects are already enriched; H2020 is additive
- Clean separation: H2020Enricher called once with full project list

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| False positives (wrong H2020 matches) | Include `matchConfidence` field; users filter by threshold (recommend 0.80+) |
| Memory usage (30K H2020 projects) | Pre-load acceptable (~100-200MB); alternative would be slower |
| H2020 API unavailable | Pre-load at startup; cache in local fallback if needed |
| Performance regression in main fetch | H2020 matching is async after main fetch completes; minimal impact |
| Stale H2020 data | H2020 ended 2020; no live updates expected; refresh annually if needed |
| Title/keyword matching brittleness | Low confidence threshold; won't affect high-confidence matches |

## Migration Plan

**Phase 1 (this change):**
1. Implement H2020Enricher with matching strategies
2. Integrate into ProjectsFetcher.main() (call after CORDIS enrichment)
3. Write to projects.json with optional h2020_related field
4. Tests for matching logic and integration

**Phase 2 (future, if needed):**
- Confidence threshold tuning based on real data
- Optional web UI to show H2020 relationships
- Historical project archive with H2020 full records

**No rollback needed** — Field is optional; existing consumers unaffected if h2020_related absent.

## Open Questions

1. **What confidence threshold should we document as recommended?**
   - Proposal: 0.80+ (conservative); 0.70+ (permissive)
   - To decide in implementation/testing

2. **Should fuzzy matching be case-insensitive?**
   - Proposal: Yes, standardise to lowercase for matching
   - To confirm in implementation

3. **How many organisations in `h2020_related` to include (all or top N)?**
   - Proposal: Include all; users can filter in UI
   - To decide in tasks
