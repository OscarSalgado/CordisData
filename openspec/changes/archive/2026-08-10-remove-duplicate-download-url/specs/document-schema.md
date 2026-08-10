# Spec: Cleaned Document Schema

## Overview

Documents in `documents.json` must not have duplicate `download_url` fields. The primary PDF URL is accessed via `attachments[0].download_url`.

## Document Schema (Cleaned)

```json
{
  "documentReference": "string (unique identifier)",
  "version": "number",
  "title": "string",
  "committeeCode": "string",
  "committeeTitle": "string",
  "creationDate": "ISO 8601 string",
  "updateDate": "ISO 8601 string",
  "meetingCode": "string",
  "meetingStartDate": "ISO 8601 string",
  "meetingEndDate": "ISO 8601 string",
  "documentType": { "id": number, "label": string, "letter": string },
  
  "attachments": [
    {
      "id": number,
      "filename": string,
      "download_url": "https://..."
    }
  ]
}
```

## What Changed

**Removed:**
- `download_url` at document level (convenience field)

**Kept:**
- `attachments[].download_url` - the authoritative URL

## Access Patterns

**Get primary PDF URL:**
```
document.attachments[0]?.download_url
```

**Get all PDFs:**
```
document.attachments.map(a => a.download_url)
```

## Validation Rules

1. `attachments` is always an array (never null)
2. Each attachment in `attachments` has `download_url`
3. No `download_url` field exists at document level
4. All URLs are HTTPS
