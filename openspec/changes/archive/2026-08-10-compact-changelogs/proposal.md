# Proposal: Compact Changelog Format

## Problem

Current changelog files are oversized and redundant:
- Full snapshots of 28+ call fields in every event
- Timestamps on every event (redundant with daily file)
- Reference + topicId duplicated for every change
- Result: ~150-200 KB per daily changelog × 90 days = ~15 MB storage

The authoritative data lives in `calls.json` and `documents.json` — changelog is for audit/reference only.

## Solution

Simplify changelog structure to include only essential identifiers + type:

### For Calls

```json
{
  "date": "2026-08-10",
  "summary": { "new": 9, "changed": 411, "closed": 1 },
  "events": [
    { "type": "NEW", "topicId": "HORIZON-WIDERA-2024-TALENTS-01", "name": "..." },
    { "type": "STATUS_CHANGED", "topicId": "...", "name": "...", "from": "open", "to": "closed" }
  ]
}
```

### For Committees (Documents)

```json
{
  "date": "2026-08-10",
  "summary": { "new": 3, "changed": 5 },
  "events": [
    { "type": "NEW", "documentReference": "108662", "title": "...", "committee": "C70407" },
    { "type": "ATTACHMENT_ADDED", "documentReference": "115416", "filename": "..." }
  ]
}
```

## Impact

- **Storage**: ~90% reduction (15 MB → 1.5 MB for 90-day history)
- **Readability**: Focused event log, not full snapshots
- **Maintainability**: Simpler schema, less coupling to master data
- **Backward compat**: Old files can coexist; viewers handle both

## Scope

- **In**: Rewrite changelog generation for calls and documents
- **In**: Update retention cleanup (still 90 days)
- **Out**: Retroactive rewrite of existing changelogs (too old, low value)
- **Out**: Change master data schemas (calls.json, documents.json)

## Success Criteria

- New changelog format matches spec
- All change types (NEW, CHANGED, CLOSED, etc.) captured
- Calls + Committees both simplified
- 90% file size reduction verified
- Tests pass
- Old format still parseable (no breaking API)
