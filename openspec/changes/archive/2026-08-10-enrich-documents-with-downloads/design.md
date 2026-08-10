# Design: Document Enrichment Implementation

## Architecture

```
Current Flow (incomplete):
  fetch_documents()        →  [document summary]
       ↓
  save to documents.json   →  no attachment info

New Flow (complete):
  fetch_documents()        →  [document summary]
       ↓ (for each doc)
  fetch_document_detail()  →  [document + attachments[]]
       ↓
  enrich()                 →  add download_url + attachments
       ↓
  save to documents.json   →  complete document with URLs
```

## Implementation Strategy

### 1. Add Enrichment Method to `CommitteeDocumentsFetcher`

**Method signature:**
```python
def _enrich_with_attachments(self, document: dict) -> dict:
    """
    Enrich a document with attachment details and download URLs.
    
    Args:
        document: Document dict from fetch_documents()
    
    Returns:
        Same document with added:
        - attachments[]: list of attachments from API
        - download_url: URL to primary PDF (if attachments exist)
    """
```

**Logic:**
1. Extract `documentReference` and `version` from document
2. Call `self.client.fetch_document_detail(ref, version)`
3. Extract `documentsAttached[]` from response
4. For each attachment:
   - Construct URL: `BASE_URL/documents/{id}/{ref}/{version}/attachment`
   - Create attachment object with id, filename, download_url
5. Add to document:
   ```python
   document["attachments"] = [... enriched attachments ...]
   if attachments:
       document["download_url"] = attachments[0]["download_url"]
   ```
6. Return enriched document

**Error handling:**
- If `fetch_document_detail` fails: log warning, return document with `attachments: []`
- If no `documentsAttached` in response: set `attachments: []`
- If URL construction fails: skip that attachment, continue with others

### 2. Modify `CommitteeDocumentsFetcher._fetch_all_pages()`

**Current:**
```python
def _fetch_all_pages(self, ...):
    all_docs = []
    for each page:
        resp = self.client.fetch_documents(...)
        all_docs.extend(resp.get("content", []))
    return all_docs
```

**New:**
```python
def _fetch_all_pages(self, ...):
    all_docs = []
    for each page:
        resp = self.client.fetch_documents(...)
        docs = resp.get("content", [])
        
        # Enrich each document
        enriched_docs = [
            self._enrich_with_attachments(doc)
            for doc in docs
        ]
        all_docs.extend(enriched_docs)
    return all_docs
```

**Rate limiting:** Each `_enrich_with_attachments()` calls `fetch_document_detail()` which acquires a token from `rate_limiter`.

### 3. Merge Strategy for Existing Documents

When merging existing documents with newly fetched:

```python
# Load existing documents
existing_by_ref = {doc["documentReference"]: doc for doc in existing}

# Fetch new (these are now enriched)
fetched = self._fetch_all_pages(...)  # <-- returns enriched docs

# Merge: prefer newly fetched (they have latest attachment info)
for doc in fetched:
    existing_by_ref[doc["documentReference"]] = doc
```

This ensures:
- New documents get attachments on first fetch
- Existing documents get attachments on next fetch (auto-enriched)
- Updated versions of documents get fresh attachment info

## Performance Considerations

**API calls ratio:**
- Current: 1 call per 100 documents (fetch_documents with pagination)
- New: 1 + N calls (1 search + N detail calls, where N = number of documents)

**With rate limit of 2 req/sec:**
- 94 documents = 94 detail calls ≈ 47 seconds
- Acceptable for scheduled daily job

**Optimization option** (not in scope):
- Could batch detail calls or use parallel fetcher
- Current sequential approach is safe and predictable

## Backwards Compatibility

- Existing documents in documents.json have no `attachments` field
- On next fetch, they get enriched (added to merge)
- Old documents without `attachments` can be handled:
  ```python
  download_url = doc.get("download_url")  # safe, may be None
  attachments = doc.get("attachments", [])  # safe, defaults to []
  ```

## URL Construction

API endpoint: `/documents/{attachment_id}/{documentReference}/{version}/attachment`

Example:
```
Base: https://ec.europa.eu/transparency/comitology-register/core/api/integration/ers
Attachment ID: 12345
Document Reference: 108662
Version: 6

Result: https://ec.europa.eu/transparency/comitology-register/core/api/integration/ers/12345/108662/6/attachment
```

Client method already exists: `download_attachment(attachment_id, doc_ref, version)`
- Can be used to verify URL construction works
- Not called by fetcher (fetcher only stores URLs, doesn't download)
