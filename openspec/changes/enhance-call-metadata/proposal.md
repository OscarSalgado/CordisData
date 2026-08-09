## Why

Current call records from SEDIA API capture essential fields (title, deadline, budget, status) but miss rich contextual information available in the API response: detailed descriptions, strategic objectives, submission procedures, and call-level metadata. Researchers and analysts need this context to understand call scope, eligibility, and strategic priorities without navigating the portal separately.

This change enriches the call dataset to reduce context-switching and enable better analysis, discovery, and decision-making within the data application.

## What Changes

- **9 new metadata fields** added to each call record from SEDIA API responses
- **3 convenience URLs** for Q&A, Updates, and Documents (unconditional, always available)
- **Conditional scraping infrastructure** prepared for future Q&A/Updates capture (Phase 2, only for open calls)
- **HTML content handling** for descriptions and objectives (cleaned text extraction)
- No breaking changes to existing fields; all new fields are additions

## Capabilities

### New Capabilities
- `enhanced-call-metadata`: Capture rich call context from SEDIA API including descriptions, objectives, submission procedures, and strategic metadata. Prepare infrastructure for Phase 2 Q&A/Updates scraping (gated by callStatus).

### Modified Capabilities
(none — this is a pure addition)

## Impact

**Data Files:**
- `data/calls.json`: +20-30% size (new fields with HTML content)

**Code Changes:**
- `CallsFetcher._transform_record()`: Extract 9 new fields
- `calls.py`: Helpers for HTML cleaning, submission procedure parsing
- `changelog.py`: Include new fields in change tracking

**Dependencies:**
- Adds `html` stdlib (HTML entity decoding)
- No external dependencies for Phase 1

**Performance:**
- Phase 1 (API enrichment): No additional network requests
- Phase 2 (scraping, future): Conditional per call, cached, non-blocking

**API / Contracts:**
- No public API changes (internal data enrichment)
- Call record schema gains 12 optional fields

**Testing:**
- Unit tests for HTML cleaning, field extraction
- Integration tests for enriched metadata in calls.json
