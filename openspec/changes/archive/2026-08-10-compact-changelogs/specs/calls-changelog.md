# Spec: Compact Calls Changelog

## Format

Daily changelog for calls, minimal redundancy.

```json
{
  "date": "2026-08-10",
  "summary": {
    "new": number,
    "changed": number,
    "auto_closed": number
  },
  "events": [
    {
      "type": "NEW" | "STATUS_CHANGED" | "FIELD_CHANGED" | "METADATA_UPDATED",
      "topicId": "HORIZON-...",
      "name": "Human-readable call name",
      "old_value": "...",      // only if type is STATUS_CHANGED
      "new_value": "...",      // only if type is STATUS_CHANGED
      "changed_fields": [...]  // only if type is METADATA_UPDATED
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
| summary.auto_closed | int | yes | Count auto-closed by deadline |
| events | array | yes | Can be empty if no changes |
| events[].type | enum | yes | NEW, STATUS_CHANGED, FIELD_CHANGED, METADATA_UPDATED |
| events[].topicId | string | yes | Unique call identifier |
| events[].name | string | yes | Call title (for reference) |
| events[].old_value | any | conditional | Present only if type=STATUS_CHANGED |
| events[].new_value | any | conditional | Present only if type=STATUS_CHANGED |
| events[].changed_fields | array[string] | conditional | Present only if type=METADATA_UPDATED |

## Access Pattern

```python
# Get all new calls from today
changelog = json.load(open("2026-08-10.json"))
new_calls = [e for e in changelog["events"] if e["type"] == "NEW"]
for event in new_calls:
    topic_id = event["topicId"]
    # Fetch full details from calls.json
    full_call = calls_by_id[topic_id]
```

## No Snapshots

The full call snapshot lives in `calls.json` keyed by `topicId`. Changelog only tracks *that* a change happened, not *what* all the fields are.
