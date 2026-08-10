# Split Calls Fetch by Status

## Problem

Currently, CallsFetcher fetches **all calls** (open, forthcoming, and closed) in a single operation and writes them to a unified `calls.json` file. This couples two independent concerns:

1. **Active call monitoring** (open/forthcoming) - for immediate alerting and tracking current opportunities
2. **Project discovery preparation** (closed calls) - for locating funded projects by topicId

These serve different purposes, have different retention policies, and will feed into different downstream workflows:
- Open calls → monitoring alerts (9-month rolling window)
- Closed calls → projects discovery (historical, from dataset start to 3 months ago)

## Proposed Solution

**Split the calls fetch into two independent streams** with separate output files and changelogs:

- `calls.open.json` - active calls (open + forthcoming, last 9 months)
- `calls.closed.json` - closed calls (from dataset start to 3 months ago)

Each maintains its own changelog directory and metadata tracking.

## Benefits

- **Clear separation of concerns**: Open and closed calls are truly independent
- **Resilience**: Failure in one stream doesn't block the other
- **Ready for projects discovery**: Closed calls are pre-filtered and available for topicId extraction (upcoming ProjectsFetcher enhancement)
- **Simpler scheduling**: Each can have its own schedule/trigger if needed in future
- **Better analytics**: Separate changelogs let us track changes to each stream distinctly

## Scope

### In Scope
- Refactor CallsFetcher into two independent fetchers (OpenCallsFetcher, ClosedCallsFetcher)
- Update metadata tracking for both streams
- Generate separate changelogs for each stream
- Update CLI to provide visibility into both streams
- Update GitHub Actions workflow to run both fetchers

### Out of Scope
- ProjectsFetcher integration (will be done in separate change)
- Deprecation of `calls.json` (can be done later if needed)
- Window-based fetching for resilience (fetch all closed calls in single request)

## Key Design Decisions

1. **Single-fetch approach**: Both streams fetch all matching data in one request (no windowing)
   - Closed calls: filter by status="closed" AND startDate >= dataset_start AND startDate <= (today - 3 months)
   - Open calls: filter by status in ["open", "forthcoming"] AND startDate >= (today - 9 months)

2. **Independent metadata**: Each stream tracks its own `*_fetched_at` timestamp
   ```json
   {
     "calls_closed_fetched_at": "2026-08-10T12:00:00Z",
     "calls_open_fetched_at": "2026-08-10T12:05:00Z"
   }
   ```

3. **Separate changelogs**: `changelog/closed/YYYY-MM-DD.json` and `changelog/open/YYYY-MM-DD.json`

4. **No filtering of historical open calls**: Open calls that close naturally fall out of the 9-month window

## Dependencies

- None (this is foundational work)

## Success Criteria

- ✓ calls.open.json and calls.closed.json both present and correctly populated
- ✓ Separate changelogs generated for each stream
- ✓ Metadata tracks both streams independently
- ✓ All existing tests updated and passing
- ✓ No data loss compared to current calls.json
