# Spec: Enriched Document Structure

## Overview

Documents in `data/committees/documents.json` must include download URLs and attachment information retrieved from the comitology-register API.

## Document Schema

Each document in the JSON array must have:

### Existing Fields (preserved from API)
```
documentReference (string): Unique document ID
version (number): Document version
title (string): Document title
meetingCode (string): Associated meeting
committeeCode (string): Committee code
committeeTitle (string): Committee name
creationDate (ISO 8601): When created
updateDate (ISO 8601): Last update
meetingStartDate (ISO 8601): Meeting start
meetingEndDate (ISO 8601): Meeting end
documentType (object): Type info
```

### New Fields (added by enrichment)

#### `download_url` (string, optional)
- URL to download primary/first PDF attachment
- Format: `https://ec.europa.eu/transparency/comitology-register/core/api/integration/ers/{attachment_id}/{documentReference}/{version}/attachment`
- **Present if**: document has at least one attachment
- **Absent if**: document has no attachments

#### `attachments` (array of objects)
- Complete list of all PDFs available for this document
- Each attachment object:
  ```json
  {
    "id": <number>,           // Attachment ID from API
    "filename": <string>,     // Original PDF filename
    "download_url": <string>  // Full download URL
  }
  ```
- **Empty array []** if no attachments
- **Always present** (even if empty)

## Examples

### Document with single attachment
```json
{
  "documentReference": "108662",
  "version": 6,
  "title": "Commission Implementing Decision...",
  "committeeCode": "C70407",
  "download_url": "https://ec.europa.eu/transparency/comitology-register/core/api/integration/ers/12345/108662/6/attachment",
  "attachments": [
    {
      "id": 12345,
      "filename": "document_108662.pdf",
      "download_url": "https://ec.europa.eu/transparency/comitology-register/core/api/integration/ers/12345/108662/6/attachment"
    }
  ]
}
```

### Document with multiple attachments
```json
{
  "documentReference": "115416",
  "version": 3,
  "title": "...",
  "download_url": "https://.../67890/115416/3/attachment",
  "attachments": [
    {
      "id": 67890,
      "filename": "main_document.pdf",
      "download_url": "https://.../67890/115416/3/attachment"
    },
    {
      "id": 67891,
      "filename": "annex.pdf",
      "download_url": "https://.../67891/115416/3/attachment"
    }
  ]
}
```

### Document with no attachments
```json
{
  "documentReference": "999999",
  "version": 1,
  "title": "Some document",
  "attachments": []
}
```
(Note: no `download_url` field when no attachments)

## Validation Rules

1. `attachments` is always an array (never null)
2. `download_url` only present when `attachments.length > 0`
3. `download_url` must match first attachment's URL
4. All URLs must use HTTPS
5. `attachment.id` must be positive integer
6. `attachment.filename` must not be empty
