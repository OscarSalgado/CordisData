# Committee Discovery Guide

Discover new EU committees automatically and stay updated with the latest additions to the comitology register.

## Overview

The committee discovery system automatically identifies new committees from the EU comitology register that are not yet in your monitoring list. A daily job runs at **07:00 UTC** to detect new committees and creates a GitHub issue with the findings.

## How It Works

```
Daily at 07:00 UTC:
  1. Fetch all committees from EU API
  2. Compare with your local monitoring list
  3. Detect new committees
  4. Create GitHub issue (if new found)
  5. Track discoveries to avoid duplicates
```

## Using Discovery

### Automatic Discovery (Daily)

The system automatically discovers new committees and creates GitHub issues:

1. Wake up to a GitHub issue titled "New EU committees discovered [DATE]"
2. Review the list of new committees
3. Add interesting ones to your monitoring list

### Manual Discovery

Run discovery anytime to see the latest:

```bash
cordis-data monitor discover
```

**Output example:**
```
Connecting to EU API...
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
```

### Dry-Run Mode

Preview what discovery would find without updating the log:

```bash
cordis-data monitor discover --dry-run
```

### Clear Discovery Log

Start fresh by resetting the discovery history:

```bash
cordis-data monitor discover --clear-log
```

## Adding Discovered Committees

Once you identify a committee to monitor:

```bash
cordis-data monitor add-committee C70409 "Digital Governance Council"
```

Verify it was added:

```bash
cordis-data monitor list-committees
```

Then the daily fetch will include documents from this committee.

## GitHub Issue Format

Discovery issues include:

| Field | Content |
|-------|---------|
| **Title** | `New EU committees discovered [YYYY-MM-DD]` |
| **Body** | Markdown table with committee codes, titles, and register links |
| **Labels** | `discovery`, `committees`, `automated` |
| **Assignee** | Unassigned (for your review) |

Example table:

| Code | Title | EU Register |
|------|-------|-------------|
| C70409 | Digital Governance | [Link](https://ec.europa.eu/transparency/comitology-register/...) |
| C70410 | Innovation | [Link](https://ec.europa.eu/transparency/comitology-register/...) |

## Discovery Log

The system tracks all discoveries in `~/.cordis-data/discovery.json`:

```json
{
  "metadata": {
    "version": "1.0",
    "last_run": "2026-08-10T07:00:00Z"
  },
  "discoveries": [
    {
      "code": "C70409",
      "title": "Digital Governance Council",
      "discovered_at": "2026-08-10T07:00:00Z",
      "reported": true
    }
  ],
  "history": {
    "total_discovered": 42,
    "issues_created": [
      {
        "date": "2026-08-10",
        "count": 3,
        "timestamp": "2026-08-10T07:00:00Z"
      }
    ]
  }
}
```

**Key fields:**
- `discoveries`: List of all discovered committees
- `reported`: Whether a GitHub issue was created
- `history`: Tracks issues created and discovery counts

## Frequently Asked Questions

### Q: Why wasn't a committee already in my list?

A: Discovery only tracks committees added via the monitoring system. Newly added committees to the EU register won't appear in this list.

### Q: How often does discovery run?

A: Daily at 07:00 UTC. You can also run it manually anytime with `cordis-data monitor discover`.

### Q: Can I get Slack alerts for new committees?

A: Currently, discoveries are reported via GitHub issues only. You can receive notifications if you watch the repository or have GitHub Slack integration enabled.

### Q: What if I miss a discovery issue?

A: The discovery log keeps all discoveries, so you can run `cordis-data monitor discover` anytime to see what's new. You won't be double-notified about the same committee.

### Q: How long are discoveries kept?

A: The system keeps 90 days of discovery history by default. Older entries are automatically archived.

### Q: Can I disable discovery?

A: The daily GitHub Actions workflow can be disabled, but there's no system-wide toggle. Manually run `cordis-data monitor discover` as needed.

## Workflow Status

To check discovery workflow runs:

1. Go to **Actions** tab on GitHub
2. Select **Discover Committees** workflow
3. View run history and logs

## Integration with Monitoring

**Discovery flow:**
```
discover → review in issue → add-committee → fetch monitors it
   ↓
 logs discovery
   ↓
 prevents duplicate reports
```

The two systems work together:
- **Discovery**: Finds new committees
- **Monitoring**: Tracks documents from committees you care about

## Troubleshooting

### Discovery job fails

Check workflow logs in GitHub Actions:
1. Go to **Actions** → **Discover Committees**
2. Click the failed run
3. Expand step logs to see error details

**Common issues:**
- API timeout: Retry runs automatically
- Permission denied: Check `~/.cordis-data/` directory permissions
- File I/O error: Ensure sufficient disk space

### No new committees found

This is normal! It means:
- You're tracking all actively developing committees
- The EU hasn't added new committees to the register recently

Run `cordis-data monitor discover --dry-run` to verify the system is working.

### Too many discovery issues

If the list gets long, you can:
1. Review and close resolved issues
2. Run `cordis-data monitor discover --clear-log` to reset
3. Re-subscribe to new discoveries starting fresh

## See Also

- [Committee Monitoring Guide](./committee-monitoring.md) - Full monitoring setup
- [Setup Secrets](./committee-monitoring-secrets.md) - GitHub Actions configuration
- [EU Comitology Register](https://ec.europa.eu/transparency/comitology-register) - Official register
