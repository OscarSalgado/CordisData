# Changelog Format

Each daily fetch of `cordis-data fetch-calls` writes a changelog file to
`data/changelog/YYYY-MM-DD.json` recording every meaningful change to calls
detected during that fetch. Files are plain JSON, one per fetch date, and are
automatically deleted after 90 days.

## File Structure

```json
{
  "fetch_date": "2026-08-09",
  "fetch_timestamp": "2026-08-09T02:00:14.123Z",
  "total_calls": 842,
  "summary": {
    "total_calls": 842,
    "new": 12,
    "changed": 8,
    "auto_closed": 3
  },
  "events": [ ... ]
}
```

## Event Types

Each entry in `events` has an `event_type` and only includes non-null fields:

- **`NEW`** — a call not previously seen. Includes `snapshot` (relevant fields at
  time of detection).
- **`STATUS_CHANGED`** — only `callStatus` changed. Includes `field`,
  `old_value`, `new_value`, `snapshot_after`.
- **`FIELD_CHANGED`** — exactly one non-status relevant field changed. Includes
  `field`, `old_value`, `new_value`, `snapshot_after`.
- **`METADATA_UPDATED`** — two or more relevant fields changed in the same
  fetch. Includes `changed_fields` (list) and `changes` (map of field ->
  `{old_value, new_value}`), plus `snapshot_after`.

Every event also has `reference`, `topicId`, and `detected_at` (ISO 8601 UTC).

### Relevant fields

Only these fields are tracked for changes (others, like `portalUrl` or
`programmeId`, are ignored as noise):

`callStatus`, `deadline`, `title`, `budgetMin`, `budgetMax`, `expectedGrants`,
`keywords`, `actionType`, `programme`, `cluster`

## Example Events

```json
{
  "reference": "HORIZON-CL4-2026-DIGITAL-01",
  "topicId": "HORIZON-CL4-2026-DIGITAL-01-42",
  "event_type": "STATUS_CHANGED",
  "detected_at": "2026-08-09T02:00:14.123Z",
  "field": "callStatus",
  "old_value": "forthcoming",
  "new_value": "open",
  "snapshot_after": {"callStatus": "open", "deadline": "2026-11-15"}
}
```

## Example Queries

Count NEW calls in a given day:
```bash
jq '[.events[] | select(.event_type == "NEW")] | length' data/changelog/2026-08-09.json
```

List all calls that transitioned to "open":
```bash
jq -r '.events[] | select(.event_type == "STATUS_CHANGED" and .new_value == "open") | .reference' \
  data/changelog/2026-08-09.json
```

Find every budget change across all changelog history:
```bash
jq -r '.events[] | select(.event_type == "FIELD_CHANGED" and .field == "budgetMax")
  | "\(.reference): \(.old_value) -> \(.new_value)"' data/changelog/*.json
```

Grep for a specific call's history across all files:
```bash
grep -l "HORIZON-CL4-2026-DIGITAL-01" data/changelog/*.json
```
