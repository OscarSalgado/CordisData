## Context

Currently, `CallsFetcher._transform_record()` extracts ~15 fields from SEDIA API responses. The API provides 40+ metadata fields per record, including descriptions (HTML), strategic objectives, submission procedures, and call-level details. These are available in the API response but not captured, requiring users to navigate the portal for context.

The SEDIA API does not return Q&A or Updates in bulk queries, but they are accessible via portal URLs with predictable patterns.

## Goals / Non-Goals

**Goals:**
- Capture 9 additional metadata fields from SEDIA API (descriptions, objectives, submission details)
- Add 3 convenience URLs for Q&A, Updates, Documents (always available)
- Prepare infrastructure for Phase 2 Q&A/Updates scraping (Phase 2 work, gated by callStatus)
- Increase call record richness without breaking existing data contracts
- Enable future Phase 2 scraping with minimal refactor

**Non-Goals:**
- Do NOT implement Q&A/Updates scraping in Phase 1 (Phase 2 work)
- Do NOT make scraping non-optional (Phase 2 will cache and background-run)
- Do NOT change existing field names or remove fields
- Do NOT require external scraping libraries in Phase 1

## Decisions

### 1. Capture 9 Fields from Existing API Response (No Extra Calls)

**Decision:** Extract `descriptionByte`, `destinationDescription`, `destinationDetails`, `submissionProcedure`, `callTitle`, `deadlineModel`, `crossCuttingPriorities`, `typesOfAction`, `topicConditions`, `supportInfo` directly from SEDIA metadata in `_transform_record()`.

**Rationale:**
- Data is already in the API response; zero cost to extract
- No additional network requests
- Direct from source, no external dependencies
- Future-proofs for Phase 2 scraping infra

**Alternatives considered:**
- Scrape portal HTML for all data: rejected (slow, fragile, extra HTTP calls)
- Lazy-load fields on-demand: rejected (over-engineering)
- Store only URLs: works but loses richness benefit

### 2. Clean HTML Content (use stdlib only)

**Decision:** For HTML fields (descriptions, conditions, support info), use Python's `html` module to unescape entities. Store as plaintext (strip `<p>`, `<ul>`, preserve text content).

**Rationale:**
- HTML is noisy for analytics/search (tags pollute results)
- stdlib `html.unescape()` has no dependencies
- Plaintext is sufficient for context; users can visit portal for formatted view
- Reduces JSON size vs. storing raw HTML

**Alternatives considered:**
- Store raw HTML: requires BeautifulSoup (extra dependency)
- Full HTML-to-Markdown: overkill, too much complexity

### 3. URLs for Q&A/Updates (Constructible, Not Scraped)

**Decision:** Add 3 computed URL fields for convenience:
- `qnaUrl`: `https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/questions-answers/{topicId}`
- `updatesUrl`: `https://ec.europa.eu/.../topic-updates/{topicId}`
- `documentsUrl`: `https://ec.europa.eu/.../documents/{topicId}`

Always populate these (not conditional on callStatus).

**Rationale:**
- Constructible from existing topicId (no extra API calls)
- Enables "click to portal" from app without URL construction logic downstream
- Zero cost, low maintenance
- Phase 2 can scrape from same URLs

**Alternatives considered:**
- Scrape content now: no (complexity, performance, brittleness)
- Skip URLs entirely: no (loses discoverability)
- Scrape conditionally (callStatus=="open"): defer to Phase 2

### 4. Phase 2 Scraping Gate: callStatus == "open"

**Decision:** Design Phase 2 scraping so it ONLY attempts to scrape Q&A/Updates when `callStatus == "open"`.

**Rationale:**
- Open calls have active Q&A and updates
- Closed calls have stale information (historical, less valuable)
- Avoids wasted scrape requests on 70%+ of records (closed/expired)
- Easy to implement: one conditional check

**Implementation (Phase 2):**
- Background job iterates over calls where `callStatus == "open"`
- Scrape and cache results (not in main fetch)
- Update cached data every X days
- Non-blocking if scraper fails

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| JSON size grows 20-30% | Acceptable. Descriptions are valuable context. Can be omitted in light-weight exports later. |
| HTML parsing loses formatting | Acceptable. Portal has formatted HTML; plaintext sufficient for analysis. |
| Phase 2 scraping brittle if portal HTML changes | Acceptable. Phase 2 is optional, non-blocking. Can be disabled/retired. |
| Some fields may be empty for older calls | Acceptable. Graceful fallback (field is null/empty). No error. |
| topicConditions/supportInfo may be very long | Acceptable. No field size limit. Can truncate in UI layer if needed. |

## Migration Plan

**Phase 1 (this change):**
1. Add 9 fields to `_transform_record()` extraction logic
2. Add HTML cleaning helper (plaintext extraction)
3. Add 3 URL computation fields
4. Tests for field extraction + HTML cleaning
5. No database or data contract changes (JSON structure only)
6. Deploy: new `calls.json` contains enriched records alongside old ones

**Phase 2 (future):**
1. Design Q&A/Updates scraper module
2. Background job to scrape open calls on schedule
3. Cache in new `data/qna/{topicId}.json` and `data/updates/{topicId}.json`
4. Integrate links in API endpoints (if public API exists)

**No rollback needed** — Phase 1 is backwards compatible (additions only)

## Open Questions

1. **Which 9 fields are highest priority if we hit token limits in JSON export?**
   - `description` (critical), `objectives` (important), `submissionProcedure` (reference), others (nice-to-have)
   - Decision: capture all now, optimize export layer later

2. **How long should Phase 2 cache Q&A/Updates?**
   - Proposal: 3-7 days (balance freshness vs. scraping load)
   - To decide in Phase 2 design

3. **Should Phase 2 scraper retry failed calls or log and move on?**
   - Proposal: log, move on (non-blocking philosophy)
   - To decide in Phase 2 design
