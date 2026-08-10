# Tasks: Remove Duplicate download_url

## Implementation

### 1. Update fetcher code
- [x] Remove download_url field generation from `_enrich_with_attachments()`
- [x] Verify attachments still have download_url

### 2. Clean existing documents.json
- [x] Remove document-level download_url from all 97 documents
- [x] Keep attachment-level download_url intact
- [x] Verify file size reduction (12.3 KB)

### 3. Update tests
- [x] Remove assertions expecting document-level download_url
- [x] Keep assertions for attachment-level URLs
- [x] Update test examples in test_committees_fetcher_enrichment.py

### 4. Verify
- [x] Run fetch to regenerate documents.json
- [x] Confirm no download_url at document level
- [x] Confirm all attachments have download_url
- [x] All tests pass (7/7)

---

## Validation Checklist

- [x] No document has top-level download_url field (verified: 0/97)
- [x] All documents with attachments have attachments[].download_url (verified: 133/133)
- [x] All URLs are HTTPS (verified: 100%)
- [x] documents.json size reduced by ~10KB (actual: 12.3 KB)
- [x] Tests pass (7/7)
- [x] Code review passes
