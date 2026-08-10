# Committee Discovery - Proposal

## Problem

The committee monitoring system is currently **reactive**: it only monitors committees the user has explicitly configured. This means:
- Users miss new relevant committees that appear in the EU comitology register
- Manual discovery of committees is labor-intensive
- There's no systematic way to surface potentially interesting committees

## Solution

Implement a **daily committee discovery job** that:
1. Fetches all available committees from the EU API: `GET /committees/codes`
2. Compares with locally monitored committees
3. Detects **new committees** (ones that weren't tracked before)
4. Retrieves metadata (title) for each new committee
5. Creates a **GitHub issue** with the list for **manual review**
6. User decides which to add to monitoring based on relevance

This keeps the system **simple and manual** - no ML, no auto-additions, just discovery with human decision-making.

## User Experience

**Before:** User manually searches the EU comitology register for new committees

**After:** 
- Daily job discovers new committees
- GitHub issue appears: "Found 3 new committees this week"
- User reviews titles and decides which to add
- One-click addition to monitoring list

## Technical Approach

```
Daily Cron Job (separate from document monitoring):
  1. GET /committees/codes → list ALL committees
  2. Load local config → get currently monitored codes
  3. DIFF: which are new?
  4. For each new:
     ├─ Fetch metadata from API (title)
     ├─ Store in discovery log (to avoid duplicates)
     └─ Add to issue body
  5. Create GitHub issue with:
     - List of new committees (code + title)
     - Link to EU register for each
     - User instructions
```

## Scope

**In Scope:**
- New GitHub Actions workflow for discovery job
- CLI command to manually trigger discovery
- Discovery log storage (JSON file)
- GitHub issue creation with committee list
- De-duplication (don't alert on same committee twice)

**Out of Scope:**
- Auto-adding committees to monitoring
- ML/semantic relevance filtering
- Slack notifications (GitHub issue is the alert)
- Tracking historical committee changes

## Success Criteria

✅ Daily discovery job runs without errors  
✅ Detects new committees not in local config  
✅ Creates GitHub issue with correct format  
✅ Issue includes committee codes and titles  
✅ De-duplication works (no duplicate issues for same committee)  
✅ User can manually add discovered committees to monitoring  

## Risks & Open Questions

- **API Availability**: What if `/committees/codes` endpoint is slow/down?
  - Mitigation: Use existing rate limiter + retry logic
  
- **Discovery Log Growth**: How long to keep history?
  - Proposal: Keep 90 days, archive older

- **Issue Volume**: If many new committees appear, issues will be large
  - Proposal: Paginate if list > 20 committees, create multiple issues

- **Committee Metadata Freshness**: Titles might change
  - Proposal: Not a concern, user sees current titles in issue
