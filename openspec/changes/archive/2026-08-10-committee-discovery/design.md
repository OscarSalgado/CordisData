# Committee Discovery - Design

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│          COMMITTEE DISCOVERY SYSTEM FLOW                    │
└─────────────────────────────────────────────────────────────┘

                  GitHub Actions Workflow
                    (Daily, 07:00 UTC)
                          │
                          ▼
    ┌─────────────────────────────────┐
    │ 1. CommitteeDiscovery.discover() │
    │    - Fetch ALL committees       │
    │    - Load local config          │
    │    - Detect new ones            │
    └────────────┬────────────────────┘
                 │
                 ▼
    ┌─────────────────────────────────┐
    │ 2. Store in discovery.json      │
    │    - Deduplicate               │
    │    - Track metadata             │
    │    - Keep 90-day history        │
    └────────────┬────────────────────┘
                 │
                 ▼
    ┌─────────────────────────────────┐
    │ 3. Create GitHub Issue          │
    │    - Format committee list      │
    │    - Include links              │
    │    - Post via gh CLI            │
    └─────────────────────────────────┘
```

## Data Structures

### CommitteeDiscovery class

```python
class CommitteeDiscovery:
    """Discover new committees from EU API."""
    
    def discover(self) -> DiscoveryResult:
        """Find new committees, return summary."""
        
    def _fetch_all_committees(self) -> list[Committee]:
        """GET /committees/codes from API."""
        
    def _detect_new(self, all_committees, monitored) -> list[Committee]:
        """DIFF: which are new."""
        
    def _deduplicate(self, new_committees) -> list[Committee]:
        """Remove ones already reported."""
        
    def save_discovery_log(self, new_committees) -> None:
        """Append to discovery.json with timestamp."""
```

### Data Models

```python
class Committee:
    code: str          # e.g., "C70408"
    title: str         # e.g., "Digital Committee"
    discovered_at: str # ISO timestamp
    reported: bool     # Has GitHub issue been created?
```

### Discovery Log (discovery.json)

```json
{
  "last_run": "2026-08-10T07:00:00Z",
  "discoveries": [
    {
      "code": "C70408",
      "title": "Digital Committee",
      "discovered_at": "2026-08-10T07:00:00Z",
      "reported": true
    }
  ],
  "issues_created": [
    {
      "date": "2026-08-10",
      "issue_number": 42,
      "committees_count": 3
    }
  ]
}
```

## GitHub Workflow

### Trigger
- **Schedule**: Daily at 07:00 UTC (after document monitoring job)
- **Manual**: `workflow_dispatch` for on-demand discovery

### Steps

1. **Checkout code**
   ```yaml
   - uses: actions/checkout@v4
   ```

2. **Set up Python & dependencies**
   ```yaml
   - uses: actions/setup-python@v4
   - run: pip install -e .
   ```

3. **Run discovery**
   ```bash
   cordis-data monitor discover
   ```
   This:
   - Fetches all committees
   - Compares with config
   - Saves discovery log
   - Returns list of new committees
   - Exit code 1 if new committees found (to trigger issue creation)

4. **Create GitHub issue** (conditional, only if new committees)
   ```bash
   gh issue create --title "New EU committees discovered" \
     --body "$(cat discovery-report.md)"
   ```

## CLI Command

### New command: `cordis-data monitor discover`

```bash
$ cordis-data monitor discover
Fetching all committees from API...
Comparing with local config...
Found 3 new committees:
  - C12345: Innovation Committee
  - C12346: Research Coordination
  - C12347: Digital Governance

Updated discovery.json
Would you like to add any to monitoring? (use: cordis-data monitor add-committee)
```

### Return value
- Exit 0: No new committees
- Exit 1: New committees found (signals workflow to create issue)

## Storage

**Discovery Log Location:**
```
~/.cordis-data/discovery.json
```

**Workflow Artifacts:**
```
.github/workflows/discovery-committees.yml
```

## Integration Points

### With existing code:

1. **CommitteeConfig** (existing)
   - Load to get monitored committees
   - No changes needed

2. **CommitteeDocumentsClient** (existing)
   - Add method: `fetch_all_committees()` → enhances `list_committees()`
   - Use existing rate limiter

3. **CLI** (existing)
   - New command group: `cordis-data monitor discover`
   - Similar structure to existing `add-committee`, `remove-committee`

### With GitHub:

- Create issues using `gh` CLI (already available in Actions)
- Label: `discovery`
- Assignee: Optional (user can set in settings)

## Error Handling

| Scenario | Action |
|----------|--------|
| API timeout | Retry 3x with backoff, then fail workflow |
| Discovery log corrupted | Rebuild from scratch |
| GitHub issue creation fails | Log error, don't retry (user will notice) |
| No new committees | Silent success, no issue created |
| Rate limit hit | Back off exponentially, respect headers |

## Performance

- **API call**: ~500ms (fetch all committees)
- **Diff computation**: O(n) where n = total committees (~200)
- **Dedup check**: O(m) where m = discoveries in log (~50-100)
- **Total runtime**: < 5 seconds

## Security

- No secrets stored in discovery log
- GitHub API token passed via Actions secrets
- Rate limiter prevents API abuse

## Testing Strategy

### Unit Tests
- `test_discover()`: Mock API, verify diff logic
- `test_deduplicate()`: Verify no double-reporting
- `test_format_issue()`: Verify GitHub issue format

### Integration Tests
- `test_discover_e2e()`: Real API call, verify discovery.json written
- `test_workflow_trigger()`: Verify workflow creates issue correctly

### Manual Verification
- Run discovery, verify GitHub issue appears
- Verify discovery.json structure
- Verify de-duplication (run 2x, should not create 2 issues)
