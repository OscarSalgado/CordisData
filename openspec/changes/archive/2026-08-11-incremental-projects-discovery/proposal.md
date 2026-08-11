# ProjectsFetcher: Incremental Project Discovery from Closed Calls

## Problem

Currently, ProjectsFetcher:
1. Loads all closed calls from `calls.json` (deprecated)
2. Extracts all topicIds and fetches projects from SEDIA
3. Enriches all projects with CORDIS data
4. Writes entire projects.json (replace mode)

**Issues:**
- Not all closed calls have awarded projects (some closed without funding)
- Full re-fetch on every run wastes API quota and time
- No resumption: interruption = restart from topic 1
- No tracking of "already visited" topics
- Risk of data loss if enrichment fails mid-batch

## Proposed Solution

**Rolling window project discovery from closed calls:**

1. Source: `calls.closed.json` (6305 closed calls, pre-filtered)
2. Iterate topic by topic
3. For each topicId:
   - Check if call deadline >= (today - 1 year)
   - If too old (>1 year): skip (no new activity expected)
   - If recent: fetch projects from SEDIA (always, may have new projects)
   - Append new projects to projects.json (no overwrites)
4. Track in metadata:
   - topics_processed_count (how many topics processed this cycle)
   - projects_fetched_at (when this fetch cycle started)

**Result:** projects.json grows with new projects; old calls (>1 year) not refetched (optimization).

## Benefits

- **API efficiency:** Each topicId visited exactly once (or skipped if already visited)
- **Resilience:** Checkpoint after every N topics → can resume on failure
- **Graceful degradation:** Missing projects don't block the fetch
- **Clear data source:** calls.closed.json is the source of truth (pre-filtered)
- **Incremental growth:** projects.json is append-only for new topics
- **Observability:** Metadata shows exactly where we are in the discovery process

## Scope

### In Scope
- Refactor ProjectsFetcher to iterate by topicId (always fetch)
- Change source from calls.json → calls.closed.json (only source now)
- Implement rolling window by deadline (skip calls >1 year old)
- Add deduplication at (topicId, projectId) level in projects.json
- Keep CORDIS enrichment per-topic (2 req/s rate limit)
- Update CLI to use --calls-closed instead of --calls
- Remove calls.json from being generated (no longer used)

### Out of Scope
- Checkpointing/resumption (fetch all recent calls each run)
- Parallel topic fetching (keep sequential for rate limiting)
- Real-time monitoring of fetch progress (can add later)
- Syncing with calls.open.json (they are independent)

## Key Design Decisions

1. **Rolling window by call deadline, not by visit state:**
   - Only fetch projects for calls closed within last 1 year
   - Rationale: New projects may appear for recent calls; old calls unlikely to change
   - Optimization: Skip calls >1 year old (no new activity expected)

2. **Always fetch (no dedup by topic):**
   - Each topicId is refetched on every run (may have new projects)
   - Deduplication happens at (topicId, projectId) level in projects.json
   - Projects are append-only, never overwritten

3. **Metadata tracking:**
   ```json
   {
     "projects_topics_processed_count": 2140,
     "projects_fetched_at": "2026-08-10T12:00:00Z",
     "projects_freshness_ttl_days": 30,
     "projects_rolling_window_days": 365
   }
   ```

4. **Graceful "not found":**
   - Some topicIds have 0 awarded projects (closed calls without funding)
   - Don't fail, just log and continue
   - Metadata tracks this: "topics_without_projects": 1234

5. **No checkpointing (simplified):**
   - Fetch all recent calls in one pass
   - Write projects.json once at end
   - Rationale: Simpler, no resumption state to manage

## Dependencies

- Requires: calls.closed.json (output of ClosedCallsFetcher)
- Requires: metadata.json for tracking visited state

## Success Criteria

- ✓ ProjectsFetcher reads from calls.closed.json (not calls.json)
- ✓ Metadata tracks topics_processed_count and rolling_window_days (365)
- ✓ Only fetches projects for calls closed within last 1 year (optimization)
- ✓ No duplicate (topicId, projectId) pairs in projects.json
- ✓ New projects appear for recent calls on each run
- ✓ All tests passing, 100% coverage of new/changed code
- ✓ No data loss compared to current implementation
- ✓ CORDIS enrichment respects 2 req/s rate limit
- ✓ CLI uses --calls-closed (--calls removed/deprecated)
- ✓ Always runs (not conditional on freshness)
