# Proposal: Enrich Committee Documents with Download URLs

## Problem

Committee documents stored in `data/committees/documents.json` currently lack download URLs. The system fetches document summaries from the comitology-register API but never enriches them with attachment details and downloadable PDF URLs.

**Current state:**
- 94 documents saved with metadata (reference, title, date, committee info)
- **No** attachment information
- **No** download URLs
- Makes documents inaccessible without reconstructing URLs manually

**Impact:** Users cannot directly access PDF documents from the stored data.

## Solution

Enrich the document fetcher to:
1. Call `fetch_document_detail()` for each document to retrieve attachments
2. Extract attachment metadata (id, filename)
3. Construct download URLs for each attachment
4. Store both:
   - `download_url`: URL to primary/first attachment (quick access)
   - `attachments`: Array with all attachments + their URLs (full detail)

## Scope

- **In**: Modify `CommitteeDocumentsFetcher` to enrich documents with attachment data
- **In**: Store structured attachment information in documents.json
- **In**: Maintain backwards compatibility with existing documents
- **Out**: Actual PDF download/caching (only URLs)
- **Out**: Attachment visualization UI

## Success Criteria

- [ ] Each document has `download_url` pointing to primary PDF
- [ ] Each document has `attachments[]` array with all PDFs and their URLs
- [ ] Fetcher gracefully handles documents with no attachments
- [ ] Rate limiting respected for detail API calls
- [ ] All 94 documents successfully enriched on next fetch
