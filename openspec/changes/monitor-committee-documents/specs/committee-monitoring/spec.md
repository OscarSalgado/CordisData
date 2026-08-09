# Committee Monitoring Specification

## Overview

The committee-monitoring capability enables periodic fetching and change detection of EU comitology documents from configurable committees. It detects new documents, updated versions, and generates a changelog following the same pattern as calls and projects data.

## API Contract

### ComitteeDocumentsClient

```python
class ComitteeDocumentsClient:
    """Client for EU comitology-register REST API."""
    
    def fetch_documents(
        self,
        committee_codes: list[str],
        start_date: Optional[str] = None,
        page: int = 0,
        size: int = 100
    ) -> dict:
        """
        Fetch documents from comitology-register API.
        
        Args:
            committee_codes: List of committee codes (e.g., ["C70408", "C70409"])
            start_date: ISO-8601 date (e.g., "2026-06-01T00:00:00Z")
            page: Page number (0-indexed)
            size: Results per page (max 100 recommended)
        
        Returns:
            {
                "content": [document, ...],
                "totalElements": int,
                "totalPages": int,
                "pageable": {...}
            }
        
        Endpoint:
            POST /core/api/front/documents/search?page={page}&size={size}
            Body: {
                "reset": true,
                "committeeCodes": committee_codes,
                "documentStartDate": start_date
            }
        """
    
    def fetch_document_detail(
        self,
        document_reference: str,
        version: int
    ) -> dict:
        """
        Fetch complete document details including attachments.
        
        Returns:
            {
                "id": int,
                "documentReference": str,
                "version": int,
                "title": str,
                "creationDate": ISO-8601,
                "updateDate": ISO-8601,
                "documentsAttached": [
                    {
                        "id": int,
                        "filename": str,
                        "language": str,
                        "title": str
                    }
                ],
                "meeting": {...},
                "documentStatus": {...},
                "documentType": {...}
            }
        
        Endpoint:
            GET /core/api/front/documents/{documentReference}/{version}
        """
    
    def download_attachment(
        self,
        attachment_id: int,
        document_reference: str,
        version: int
    ) -> bytes:
        """
        Download PDF attachment.
        
        Returns: PDF binary content
        
        Endpoint:
            GET /core/api/integration/ers/{attachment_id}/{document_reference}/{version}/attachment
        """
```

### CommitteeDocumentsFetcher

```python
class CommitteeDocumentsFetcher:
    """Fetch and store committee documents with change detection."""
    
    def fetch(
        self,
        committee_codes: list[str],
        output_path: Path = None,
        metadata_path: Path = None,
        window_days: int = 90
    ) -> None:
        """
        Fetch documents for committees from rolling 3-month window.
        
        Steps:
        1. Calculate start_date = now() - window_days days
        2. Load existing documents from disk
        3. Fetch all documents >= start_date (with pagination)
        4. Purge documents older than window_days
        5. Detect changes (NEW, UPDATED, UNCHANGED)
        6. Merge fetched documents with existing
        7. Save documents.json
        8. Generate changelog with all events
        9. Update metadata (last fetch timestamp)
        
        Args:
            committee_codes: List to monitor
            output_path: Where to write documents.json
            metadata_path: Where to write metadata
            window_days: Days to look back (default: 90 for 3 months)
        """
    
    def detect_changes(
        self,
        existing: list[dict],
        fetched: list[dict]
    ) -> list[ChangeEvent]:
        """
        Compare existing documents with fetched.
        
        Logic:
        - Key: documentReference (unique per document, across all versions)
        - NEW: documentReference not in existing → triggers alert
        - UPDATED: documentReference exists but version/updateDate changed → logged only
        - UNCHANGED: same (ref, version, updateDate) → skipped
        
        Alert trigger: NEW documents only (not on version updates)
        Changelog: All events recorded (NEW, UPDATED, UNCHANGED) for audit
        
        Returns: List of ChangeEvent objects
        """
    
    def generate_changelog(
        self,
        changes: list[ChangeEvent],
        output_dir: Path
    ) -> None:
        """
        Write changelog/YYYY-MM-DD.json with events.
        
        File format:
        {
            "fetch_date": "2026-08-09",
            "fetch_timestamp": "2026-08-09T12:00:00Z",
            "total_documents": int,
            "summary": {
                "new": int,
                "updated": int,
                "unchanged": int
            },
            "events": [
                {
                    "event_type": "NEW|UPDATED",
                    "documentReference": str,
                    "version": int,
                    "title": str,
                    "detected_at": ISO-8601,
                    "files": [{"filename": str, "id": int, "downloadUrl": str}]
                }
            ]
        }
        """
```

## Data Storage

### documents.json

```json
{
  "documentReference": "116169",
  "version": 1,
  "title": "agenda ad hoc PC 10 07 2026",
  "creationDate": "2026-06-08T09:46:01.636Z",
  "updateDate": "2026-06-08T12:48:01.664Z",
  "committeeCode": "C70408",
  "committeeTitle": "Programme Committee for the specific programme...",
  "meeting": {
    "code": "CMTD(2026)974",
    "startDate": "2026-07-09T22:00:00Z",
    "endDate": "2026-07-09T22:00:00Z"
  },
  "documentType": {
    "id": 1,
    "description": "label.agenda",
    "letter": "A"
  },
  "status": "transmitted",
  "language": "EN",
  "files": [
    {
      "id": 533495,
      "filename": "agenda ad hoc PC 10 07 2026.pdf",
      "title": "Agenda...",
      "language": "EN",
      "downloadUrl": "https://ec.europa.eu/transparency/comitology-register/core/api/integration/ers/533495/116169/1/attachment"
    }
  ]
}
```

### changelog/YYYY-MM-DD.json

Same structure as calls/projects changelogs with NEW/UPDATED events.

## Configuration

### committees-config.json

```json
{
  "committees": [
    {"code": "C70408", "name": "Digital, Industry and Space", "enabled": true},
    {"code": "C70409", "name": "Health", "enabled": true}
  ],
  "alerts": {
    "enabled": true,
    "slack_webhook": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX",
    "email": "alerts@example.com",
    "github_issues": true,
    "issue_repo": "owner/repo"
  },
  "last_check": "2026-08-09T12:00:00Z"
}
```

## CLI Interface

```bash
# Add committee to monitoring
cordis-data monitor add-committee C70408 "Digital, Industry and Space"

# List monitored committees
cordis-data monitor list-committees

# Remove committee
cordis-data monitor remove-committee C70408

# Show config
cordis-data monitor config show

# Set alert configuration
cordis-data monitor config set alerts.slack_webhook "https://..."
cordis-data monitor config set alerts.email "user@example.com"

# Manual fetch (for testing)
cordis-data monitor fetch

# Fetch with full history
cordis-data monitor fetch --history
```

## Constraints

- **Rate limiting**: Max 2 requests/sec to comitology API (same as CORDIS)
- **Pagination**: Max size=100 per request
- **Archival**: Auto-delete changelog files older than 90 days
- **Storage**: documents.json kept under 50MB (limit ~10k documents)

## Error Handling

- API errors: Retry with exponential backoff (max 3 attempts)
- Fetch failure: Log error, don't update metadata (allows retry next run)
- Alert failure: Log error but continue (don't block fetch)
- Invalid committee code: Validate against `/committees` endpoint, reject if not found
