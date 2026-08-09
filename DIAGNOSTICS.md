# Troubleshooting & Diagnostics

## GitHub Actions Logs

### Viewing Logs

1. **GitHub UI**: Go to `Actions` → `Fetch Calls` or `Fetch Projects` → click run → view logs
2. **Download Logs**: Click "Artifacts" section to download `fetch-calls-logs` or `fetch-projects-logs`
3. **Command Line**: 
   ```bash
   gh run list
   gh run view <run-id> --log
   ```

### Log Files

Logs are automatically captured in:
- `logs/fetch-calls.log` — uploaded as artifact `fetch-calls-logs`
- `logs/fetch-projects.log` — uploaded as artifact `fetch-projects-logs`

Retention: **30 days**

### Workflow Summary

Each run includes a summary visible on GitHub:
- Fetch status (success/failed)
- Validation status (valid/invalid)
- Git status (pushed/no_changes/error)
- Timestamp
- Full logs in code block

## Common Issues & Solutions

### Issue: "No changes in calls/projects data"

**Cause**: Data is identical to previous run (no new records)

**Solution**: Normal behavior. Means:
- API returned same data
- No new calls/projects available
- Data is up-to-date

**Verify**: Check logs for "No changes" message

---

### Issue: "fetch-calls.log not found"

**Cause**: Workflow failed before creating logs

**Solution**:
1. Check raw GitHub Actions output (before artifact upload)
2. Look for error in "Fetch calls with logging" step
3. Common causes:
   - Dependency installation failed
   - Python import error
   - Network connectivity

**Verify**: Check Python version and pip list in logs

---

### Issue: "calls.json not found" or "projects.json not found"

**Cause**: Fetch command didn't create output files

**Solution**:
1. Check fetch error in logs
2. Verify SEDIA/CORDIS API is accessible
3. Check if rate limiting occurred
4. Verify network connectivity

**Verify**: Look for API error messages in logs

---

### Issue: Commit/push failed

**Cause**: Git operations failed

**Solution**:
1. Check git config (user.name, user.email)
2. Verify write permissions
3. Check if branch is protected
4. Look for merge conflicts

**Verify**: Check "Git Operations" section of logs

---

### Issue: CORDIS rate limiting

**Cause**: Too many requests to CORDIS API (max 2 req/sec)

**Solution**: 
- ProjectsFetcher has built-in TokenBucket limiter
- If error appears, it means requests exceeded limit
- Normal behavior when enriching many projects

**Verify**: Check for "429 Too Many Requests" in logs

---

## Local Testing

### Test fetch-calls locally

```bash
# Install package
pip install -e .

# Fetch with logging
mkdir -p logs
cordis-data fetch-calls --force 2>&1 | tee logs/fetch-calls.log

# Check output
cat data/calls.json | python -m json.tool | head -50
cat data/.metadata.json | python -m json.tool
```

### Test fetch-projects locally

```bash
# Fetch with logging
cordis-data fetch-projects 2>&1 | tee logs/fetch-projects.log

# Check output
cat data/projects.json | python -m json.tool | head -50
cat data/.metadata.json | python -m json.tool
```

### Check API connectivity

```bash
# Test SEDIA API
python3 << 'EOF'
from cordis_data.api.sedia import SediaClient
client = SediaClient()
result = client.search(
    query={"bool": {"must": [{"terms": {"type": ["1"]}}]}},
    sort={"field": "startDate", "order": "DESC"},
    page_num=1,
    page_size=10
)
print(f"API accessible: {len(result.get('results', []))} results")
EOF
```

## Monitoring

### Check data freshness

```bash
python3 << 'EOF'
from pathlib import Path
from cordis_data.data.metadata import load_metadata

metadata = load_metadata(Path("data/.metadata.json"))
print(f"Calls fetched: {metadata['calls_fetched_at']}")
print(f"Calls TTL: {metadata['calls_freshness_ttl_days']} days")
print(f"Projects fetched: {metadata['projects_fetched_at']}")
print(f"Projects TTL: {metadata['projects_freshness_ttl_days']} days")
EOF
```

### Track record counts

```bash
python3 << 'EOF'
import json
from pathlib import Path

calls = json.loads(Path("data/calls.json").read_text())
projects = json.loads(Path("data/projects.json").read_text())

print(f"Calls: {len(calls)}")
print(f"Projects: {len(projects)}")
EOF
```

## Debugging Steps

1. **Check workflow status** → GitHub Actions UI
2. **Download logs** → Artifacts section
3. **Search logs** → Look for "ERROR", "FAILED", "Exception"
4. **Check timestamps** → Verify workflow ran at expected time
5. **Validate data** → Check file sizes and record counts
6. **Check API** → Verify SEDIA/CORDIS accessibility
7. **Test locally** → Reproduce issue on local machine
8. **Check git** → Verify write permissions and branch status

## Contact & Support

For issues:
1. Check the logs in GitHub Actions artifacts
2. Run locally with same command: `cordis-data fetch-calls --force`
3. Report with:
   - Workflow run ID
   - Error message from logs
   - Local test results
   - Python version and environment
