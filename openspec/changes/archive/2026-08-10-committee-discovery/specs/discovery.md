# Committee Discovery Specification

## Feature: Discovery Job

### Description
Daily automated job to discover new committees in the EU comitology register that are not yet monitored locally.

### API Contract

**Endpoint:** `GET /committees/codes` (existing)
**Response:**
```json
[
  {
    "code": "C70408",
    "title": "Digital Committee"
  }
]
```

### Discovery Logic

**Input:**
- List of ALL committees from API
- Local config with monitored committees

**Process:**
```
for each committee in api_list:
  if committee.code NOT IN local_config.committees:
    if committee.code NOT IN discovery_log:
      mark as NEW
```

**Output:**
- List of new committees
- Updated discovery.json

### Discovery Log

**File:** `~/.cordis-data/discovery.json`

**Schema:**
```json
{
  "metadata": {
    "version": "1.0",
    "last_run": "2026-08-10T07:00:00Z"
  },
  "discoveries": [
    {
      "code": "CODE",
      "title": "Committee Title",
      "discovered_at": "2026-08-10T07:00:00Z",
      "reported": true/false
    }
  ],
  "history": {
    "total_discovered": 15,
    "issues_created": [
      {
        "date": "2026-08-10",
        "issue_number": 42,
        "count": 3
      }
    ]
  }
}
```

### Retention Policy

- Keep all discoveries in log indefinitely
- Mark as `reported: true` once GitHub issue created
- Only report each committee ONCE per issue
- If user adds committee to monitoring, discovery can be removed

### De-duplication Rules

1. Don't include committee in discovery if it's already in discovery.json
2. Create one GitHub issue per discovery run (batch multiple new committees)
3. Only create issue if new committees > 0
4. Mark discoveries as `reported: true` after issue creation

---

## Feature: GitHub Issue Creation

### Trigger
- Discovery job finds ≥1 new committee
- AND discovery.json updated
- AND not already reported for this batch

### Issue Format

**Title:**
```
New EU committees discovered [DATE]
```

**Body:**
```markdown
# New Committees Discovered

Found 3 new committees in the EU comitology register:

| Code    | Title                      | Links                              |
|---------|----------------------------|-----------------------------------|
| C70409  | Digital Governance Council | [Register](url) [Documents](url)   |
| C70410  | Innovation Coordination    | [Register](url) [Documents](url)   |
| C70411  | Research Partnership       | [Register](url) [Documents](url)   |

## Next Steps

To start monitoring a committee, use:

\`\`\`bash
cordis-data monitor add-committee C70409 "Digital Governance Council"
\`\`\`

Or use the CLI menu:

\`\`\`bash
cordis-data monitor add-committee
\`\`\`

---

*Discovered: 2026-08-10 at 07:00 UTC*
```

### Labels
- `discovery`
- `committees`
- `automated`

### Assignment
- None (open for user review)

### Auto-close Rules
- Don't auto-close; user closes manually after reviewing

---

## Feature: CLI Command

### Command: `cordis-data monitor discover`

**Purpose:** Manual trigger for committee discovery

**Behavior:**
```bash
$ cordis-data monitor discover

Connecting to EU API...
Fetching all committees...
Comparing with local config...

Results:
  Total committees: 243
  Currently monitored: 5
  New committees: 3

New committees found:
  C70409: Digital Governance Council
  C70410: Innovation Coordination  
  C70411: Research Partnership

Discovery log updated.

Next steps:
  1. Review new committees
  2. Add relevant ones: cordis-data monitor add-committee <code> "<title>"

Exit code: 1 (to signal GitHub Actions to create issue)
```

**Exit Codes:**
- 0: No new committees
- 1: New committees found (creation proceeded)
- 2: Error (API failure, file I/O error)

**Options:**
```
--dry-run       Show what would happen, don't update log
--create-issue  Force issue creation even if already reported
--clear-log     Reset discovery log before running
```

---

## Error Handling

### API Errors
| Scenario | Response |
|----------|----------|
| 5xx error | Retry 3x with backoff, then fail |
| Timeout | Fail after 30s, log error |
| 404 | Fail, endpoint might have changed |

### File Errors
| Scenario | Response |
|----------|----------|
| Log file corrupted | Rebuild from empty |
| Permission denied | Fail, ask user for permissions |
| Disk full | Fail, ask user to free space |

### GitHub Errors
| Scenario | Response |
|----------|----------|
| Token invalid | Fail, log to console |
| Repo not found | Fail, verify repo setting |
| Rate limited | Wait and retry once |

---

## Constraints

1. **Must not auto-add committees** - Only suggest via GitHub issue
2. **Must deduplicate** - Report each new committee only once
3. **Must be async** - Run independently from document monitoring
4. **Must be reversible** - User can delete/ignore discoveries
5. **Must preserve history** - Keep discovery log for audit trail

---

## Success Metrics

- ✅ Discovery job runs daily without manual intervention
- ✅ GitHub issues created within 5 minutes of job completion
- ✅ No duplicate issues for same committee
- ✅ 100% accuracy in detecting new committees (no false positives/negatives)
- ✅ User can add discovered committees in < 1 minute
