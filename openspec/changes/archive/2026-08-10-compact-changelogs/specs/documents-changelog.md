# Spec: Compact Documents Changelog

## Format

Daily changelog for committee documents, minimal redundancy.

```json
{
  "date": "2026-08-10",
  "summary": {
    "new": number,
    "changed": number
  },
  "events": [
    {
      "type": "NEW" | "ATTACHMENT_ADDED" | "METADATA_UPDATED",
      "documentReference": "115416",
      "title": "Commission Implementing Decision amending...",
      "committee": "C70407",
      "filename": "...",          // only if type=ATTACHMENT_ADDED
      "attachment_id": 12345,     // only if type=ATTACHMENT_ADDED
      "changed_fields": [...]     // only if type=METADATA_UPDATED
    }
  ]
}
```

## Field Rules

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| date | string (YYYY-MM-DD) | yes | One per daily file |
| summary | object | yes | Aggregate counts |
| summary.new | int | yes | Count of NEW events |
| summary.changed | int | yes | Count of changed (non-NEW) events |
| events | array | yes | Can be empty if no changes |
| events[].type | enum | yes | NEW, ATTACHMENT_ADDED, METADATA_UPDATED |
| events[].documentReference | string | yes | Unique document identifier |
| events[].title | string | yes | Document title (for reference) |
| events[].committee | string | yes | Committee code (e.g., C70407) |
| events[].filename | string | conditional | Present if type=ATTACHMENT_ADDED |
| events[].attachment_id | int | conditional | Present if type=ATTACHMENT_ADDED |
| events[].changed_fields | array[string] | conditional | Present if type=METADATA_UPDATED |

## Access Pattern

```python
# Get all new documents from today
changelog = json.load(open("2026-08-10.json"))
new_docs = [e for e in changelog["events"] if e["type"] == "NEW"]
for event in new_docs:
    doc_ref = event["documentReference"]
    # Fetch full details from documents.json
    full_doc = docs_by_ref[doc_ref]
```

## No Snapshots

The full document record lives in `documents.json` keyed by `documentReference`. Changelog only tracks *that* a change happened, not *what* all the fields are.
