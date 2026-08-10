# Committee Document Monitoring

Monitor EU committee documents from the comitology-register in real-time. Get alerts when new documents are detected.

## Quick Start

### 1. Add a committee to monitor

```bash
cordis-data monitor add-committee C70408 "Digital, Industry and Space"
```

### 2. List your committees

```bash
cordis-data monitor list-committees
```

Output:
```
✓ C70408: Digital, Industry and Space
```

### 3. Configure alerts (optional)

#### Slack notifications
```bash
cordis-data monitor config-set --slack "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

#### GitHub Issues
Set up GitHub Actions secrets (see [Secrets Setup](./committee-monitoring-secrets.md)):
- `GH_TOKEN`: GitHub Personal Access Token
- `CORDIS_SLACK_WEBHOOK`: Slack webhook URL

### 4. Fetch documents now (manual)

```bash
cordis-data monitor fetch --window 90
```

Options:
- `--window DAYS`: Look back N days (default: 90)

## Discover New Committees

Don't know which committees to monitor? Discover new ones automatically!

### Automatic Discovery

A daily job discovers new committees from the EU register:

- **Daily run:** 07:00 UTC (after document monitoring)
- **Manual trigger:** 
  ```bash
  cordis-data monitor discover
  ```

When new committees are found, a GitHub issue is created with:
- List of new committee codes and titles
- Direct links to the EU register
- Instructions for adding to monitoring

### Manual Discovery

Run discovery anytime to see what's new:

```bash
cordis-data monitor discover
```

Output shows:
- Total committees in register
- Currently monitored
- New committees (if any)

### Adding Discovered Committees

Once you find an interesting committee in the discovery output or GitHub issue:

```bash
cordis-data monitor add-committee C70409 "Digital Governance"
```

Then it will be automatically monitored by the daily job.

## Automated Monitoring

Committee monitoring runs automatically via GitHub Actions:

- **Document monitoring:** 06:00 UTC daily
- **Committee discovery:** 07:00 UTC daily
- **Manual trigger:** Via GitHub Actions UI or CLI
- **Commit strategy:** Only commits if documents changed
- **Alerts:** Sends Slack notifications + creates GitHub issues

### Set up automation

1. Configure GitHub repository secrets (see [Secrets Setup](./committee-monitoring-secrets.md))
2. Commit configuration: `data/committees/config.json`

## Accessing Document Downloads

All fetched documents are stored in `data/committees/documents.json` with download URLs included.

### Document Structure

Each document contains:

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

### Fields Explained

- **`download_url`**: Direct link to the primary PDF (convenience field)
- **`attachments[]`**: Array of all available PDFs for this document
  - `id`: Attachment identifier
  - `filename`: Original PDF filename
  - `download_url`: Direct HTTPS link to download

### Performance Notes

Document fetching now makes **N+1 API calls** per fetch:
- 1 call: Fetch document list
- N calls: Fetch details for each document (to get attachment URLs)

With rate limiting at 2 req/sec:
- 100 documents ≈ 50 seconds
- Acceptable for daily scheduled job
3. Push to repository
4. Workflow runs automatically at 06:00 UTC daily

## Available Committees

The system supports all 624 committees from the EU comitology-register. Common committees:

- `C70408` - Digital, Industry and Space
- `C70389` - Environment
- `C70397` - Health and Consumer Protection

Find more: https://ec.europa.eu/transparency/comitology-register/

## Configuration

Configuration is stored in `~/.cordis-data/committees-config.json`:

```json
{
  "committees": [
    {
      "code": "C70408",
      "name": "Digital, Industry and Space",
      "enabled": true
    }
  ],
  "alerts": {
    "enabled": true,
    "slack_webhook": "https://hooks.slack.com/...",
    "email": null,
    "github_issues": false
  },
  "last_check": "2026-08-01T12:00:00Z"
}
```

### Managing configuration via CLI

```bash
# Show current config
cordis-data monitor config-show

# Set Slack webhook
cordis-data monitor config-set --slack "https://hooks.slack.com/services/..."

# Set email (for future use)
cordis-data monitor config-set --email "your@email.com"

# Enable GitHub Issues
cordis-data monitor config-set --github-issues
```

## Data Storage

- **Documents:** `data/committees/documents.json`
- **Changelog:** `data/committees/changelog/YYYY-MM-DD.json`
- **Config:** `~/.cordis-data/committees-config.json`

### Changelog format

Daily changelog records all document changes (NEW, UPDATED, UNCHANGED):

```json
{
  "fetch_date": "2026-08-01",
  "fetch_timestamp": "2026-08-01T12:00:00Z",
  "summary": {
    "new": 3,
    "updated": 2,
    "total_events": 5
  },
  "events": [
    {
      "event_type": "NEW",
      "topicId": "116169",
      "detected_at": "2026-08-01T12:00:00Z",
      "snapshot": { ... }
    }
  ]
}
```

## Document Access

Each document includes a direct PDF download link. Example:

```
https://ec.europa.eu/transparency/comitology-register/core/api/integration/ers/{attachment_id}/{document_reference}/{version}/attachment
```

Links are included in:
- Slack alert messages
- GitHub issue bodies
- Changelog entries

## Monitoring Window

The system maintains a rolling 3-month window:

- Fetches: Documents from the last 90 days
- Purges: Documents older than 90 days from active dataset
- Changelog: Kept indefinitely for audit trail

This ensures:
- Fresh data without bloat
- Complete change history
- Easy discovery of recent documents

## Alerts and Notifications

### Alert Types

#### ✅ NEW documents
Triggers alert immediately:
- Slack message with document summary
- GitHub issue created (if enabled)
- Included in changelog

#### ℹ️ UPDATED documents
Logged only (no alert):
- Recorded in changelog
- Not notified (updates don't require intervention)

### Slack Format

```
🆕 3 new committee document(s)

Document Title
Committee: C70408
Type: Committee Opinion
Ref: 116169
```

### GitHub Issue Format

```
Title: [C70408] Committee Opinion: Document Title

Body:
Committee: C70408
Type: Committee Opinion
Reference: 116169
Date: 2026-08-01
Language: EN

[Links to PDF attachments]
```

## Troubleshooting

### No documents fetched
- Check committee code: `cordis-data monitor list-committees`
- Verify API connectivity: Try adding a well-known committee first
- Check window: `--window 365` to search last year

### Alerts not arriving
- Verify Slack webhook is set: `cordis-data monitor config-show`
- Test webhook manually (see [Secrets Setup](./committee-monitoring-secrets.md))
- Check GitHub Actions workflow logs

### High API usage
- The system uses rate limiting (2 requests/second)
- Fetch for 624 committees takes ~5 minutes
- Consider monitoring only essential committees to reduce bandwidth

## API Information

- **Base URL:** https://ec.europa.eu/transparency/comitology-register/
- **Endpoints:**
  - `/core/api/front/documents/search` - Search documents
  - `/core/api/front/documents/{ref}/{version}` - Document details
  - `/core/api/integration/ers/{attachment_id}/{ref}/{version}/attachment` - PDF download
  - `/core/api/front/committees` - List all committees

- **Rate limit:** 2 requests/second (enforced client-side)
- **Timeout:** 10 seconds per request with exponential backoff

## Next Steps

- Monitor multiple committees for comprehensive coverage
- Configure Slack for team-wide notifications
- Set up GitHub Issues for tracking new documents
- Run manual fetch to verify setup works

For questions or issues, file a GitHub issue with the committee code and error message.
