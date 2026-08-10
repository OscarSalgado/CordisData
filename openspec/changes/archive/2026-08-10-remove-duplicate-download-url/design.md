# Design: Remove Duplicate URL Field

## Changes Required

### 1. Update `CommitteeDocumentsFetcher._enrich_with_attachments()`

**Current:**
```python
# Add convenience field: download_url to primary PDF
if document["attachments"]:
    document["download_url"] = document["attachments"][0]["download_url"]
```

**New:**
Remove those lines entirely. Only keep `attachments` array.

### 2. Update existing documents.json

Remove `download_url` field from all 97 documents. Since this field only appears at document level (not in attachments), a simple JSON filter removes all instances:

```python
for doc in documents:
    if "download_url" in doc and not any(key == "download_url" for key in doc.get("attachments", [{}])[0]):
        del doc["download_url"]
```

Or more simply: iterate documents, delete top-level `download_url`, keep attachment-level ones.

### 3. Update Tests

**Remove assertions expecting document-level URL:**
```python
# Delete lines like:
# assert "download_url" in doc
# assert doc["download_url"] == doc["attachments"][0]["download_url"]
```

**Keep assertions for attachment URLs:**
```python
# Keep:
# assert doc["attachments"][0]["download_url"].startswith("https://")
```

## Impact Assessment

- **Breaking change:** No - this is internal-only data restructuring
- **Data loss:** No - URL is still accessible via `attachments[0]`
- **File size:** Reduction of ~10KB (small but cleaner)
- **Backwards compatibility:** Old documents in documents.json will be rewritten; no API change

## Implementation Order

1. Update fetcher code (remove URL addition)
2. Update existing documents.json (remove field)
3. Update tests
4. Verify with fetch run
