# Proposal: Remove Duplicate download_url Field

## Problem

Each document in `documents.json` has a redundant `download_url` field at the document level that duplicates `attachments[0].download_url`.

**Example:**
```json
{
  "documentReference": "115864",
  "attachments": [
    {
      "id": 531972,
      "filename": "V115864-1.pdf",
      "download_url": "https://ec.europa.eu/.../531972/115864/1/attachment"
    }
  ],
  "download_url": "https://ec.europa.eu/.../531972/115864/1/attachment"  // IDENTICAL
}
```

**Impact:**
- Data redundancy: ~10KB extra per 97 documents
- Ambiguity when document has 2+ attachments
- Maintenance burden: two places to update if URLs change
- Violates DRY principle

## Solution

Remove the document-level `download_url` field entirely. Clients access the primary PDF via `attachments[0].download_url`.

**Verification:** 36/97 documents have multiple attachments, and in ALL cases the document-level URL equals the first attachment's URL. No data loss.

## Scope

- **In**: Remove `download_url` field from all documents
- **In**: Update fetcher to not add this field
- **In**: Update documentation
- **Out**: Change API/contract (purely internal cleanup)

## Success Criteria

- [ ] All 97 documents in documents.json have no `download_url` at document level
- [ ] `attachments[0].download_url` present for all documents with attachments
- [ ] Fetcher code updated to remove field generation
- [ ] Tests updated to not expect document-level URL
- [ ] ~10KB data reduction in documents.json
