# Tasks: Enriched Document Downloads

## Implementation Tasks

### 1. Add `_enrich_with_attachments()` method to `CommitteeDocumentsFetcher`
- [x] Create method that takes a document dict
- [x] Call `self.client.fetch_document_detail(documentReference, version)`
- [x] Extract `documentsAttached[]` from response
- [x] For each attachment, construct download URL
- [x] Add `attachments` array to document
- [x] Add `download_url` to document if attachments exist
- [x] Handle errors gracefully (missing attachments, API failures)

### 2. Modify `_fetch_all_pages()` to enrich documents
- [x] Call `_enrich_with_attachments()` for each fetched document
- [x] Maintain pagination (enrich after each page)
- [x] Verify rate limiting still works (detail calls respect limiter)
- [x] Test with 100+ documents to ensure no timeouts

### 3. Update merge logic to prefer fresh data
- [x] Ensure fetched (enriched) documents override existing ones
- [x] Verify old documents get overwritten with new enriched versions
- [x] Test merge with documents that have/don't have attachments

### 4. Add encoding fix to fetcher
- [x] Update file writes to use `encoding='utf-8'`
- [x] Ensure JSON serialization handles special characters

### 5. Write unit tests
- [x] Test `_enrich_with_attachments()` with mock detail response
- [x] Test URL construction correctness
- [x] Test error handling (missing attachments, API failure)
- [x] Test documents without attachments get empty array
- [x] Created 7 comprehensive tests in test_committees_fetcher_enrichment.py
- [x] All tests passing

### 6. Write integration test
- [x] Fetch documents from 1-2 real committees
- [x] Verify documents have valid download URLs
- [x] Verify attachment count matches API response
- [x] Verify documents.json has correct schema

### 7. Update docs
- [x] Document the new `attachments` and `download_url` fields
- [x] Add example document structure to monitoring guide
- [x] Note about rate limiting impact (N+1 API calls)

### 8. Verify backwards compatibility
- [x] Load existing documents.json without attachments
- [x] Run fetch, verify old docs get enriched
- [x] Check no data loss in merge

---

## Validation Checklist

Before marking complete:
- [x] All documents have `attachments: []` (even if empty)
- [x] Documents with attachments have `download_url`
- [x] No documents have `download_url` without attachments
- [x] All URLs are HTTPS
- [x] All URLs follow format: `/core/api/integration/ers/{id}/{ref}/{version}/attachment`
- [x] No encoding errors when saving
- [x] Rate limiting respected (2 req/sec)
- [x] Tests pass (7 unit tests + integration with real data)
