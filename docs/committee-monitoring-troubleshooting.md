# Committee Monitoring - Troubleshooting Guide

## Common Issues and Solutions

### 1. "Committee code not found" error

**Error message:**
```
❌ Committee C12345 not found
```

**Causes:**
- Invalid committee code
- API connectivity issue
- Committee doesn't exist in comitology-register

**Solution:**
1. Verify the committee code exists:
   ```bash
   # Try a known committee
   cordis-data monitor add-committee C70408
   ```

2. Check API connectivity:
   ```bash
   # Test with curl
   curl "https://ec.europa.eu/transparency/comitology-register/core/api/front/committees" | head -20
   ```

3. Find correct code:
   - Browse: https://ec.europa.eu/transparency/comitology-register/
   - Search for your committee
   - Copy the code from the URL or committee title

### 2. "No documents fetched"

**Symptoms:**
- Fetch runs successfully but shows 0 documents
- Changelog shows no events

**Causes:**
- Committee has no documents in last 90 days
- Window is too short (`--window` parameter)
- API returning empty results

**Solutions:**

**Try a wider window:**
```bash
cordis-data monitor fetch --window 365  # Last year
```

**Check if committee exists and has documents:**
```bash
cordis-data monitor list-committees  # Verify committee is configured
```

**Test API directly:**
```bash
# Replace C70408 and 2026-01-01 with real values
curl -X POST "https://ec.europa.eu/transparency/comitology-register/core/api/front/documents/search?page=0&size=100" \
  -H "Content-Type: application/json" \
  -d '{
    "committeeCodes": ["C70408"],
    "documentStartDate": "2026-01-01T00:00:00.000Z"
  }' | python -m json.tool | head -50
```

### 3. Slack alerts not arriving

**Symptoms:**
- Fetch runs without errors
- New documents detected
- But no Slack message

**Causes:**
- Webhook URL not configured
- Webhook URL invalid or expired
- Webhook has restricted permissions

**Solutions:**

**Verify webhook is configured:**
```bash
cordis-data monitor config-show | grep slack_webhook
```

**If empty, set webhook:**
```bash
cordis-data monitor config-set --slack "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

**Test webhook manually:**
```bash
curl -X POST "https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Test message from CORDIS monitoring"
  }'
```

**Webhook expired:**
1. Go to your Slack workspace
2. Go to Incoming Webhooks
3. Check if webhook is still active
4. Regenerate if needed
5. Update secret in GitHub Actions → Settings → Secrets

### 4. GitHub workflow fails with "Webhook authentication failed"

**Symptoms:**
- Workflow shows red X
- Logs show "Webhook authentication failed"

**Causes:**
- Secret not set in GitHub
- Secret value is incorrect or expired
- Webhook URL missing https:// prefix

**Solutions:**

**Check secret is set:**
1. Go to repository Settings → Secrets and variables → Actions
2. Look for `CORDIS_SLACK_WEBHOOK`
3. If missing, click "New repository secret" and add it

**Verify secret value:**
```bash
# In workflow logs, this would be redacted, but in local test:
cordis-data monitor config-show  # Should show your webhook

# Copy the full URL (including https://)
```

**Update expired secret:**
1. Go to https://api.slack.com/apps
2. Select your app
3. Go to Incoming Webhooks
4. Delete old webhook
5. Create new webhook
6. Update GitHub secret with new URL

### 5. "No changes to commit" in workflow logs

**Message:**
```
No changes to commit
```

**This is normal when:**
- No new documents were detected
- Existing documents haven't changed
- All documents are older than 90 days

**To verify:**
1. Check workflow ran successfully (no red X)
2. Check logs for "Fetch complete"
3. New documents count in logs should show 0 or more

### 6. High API usage / Rate limit messages

**Symptoms:**
- Logs show 429 errors
- Fetch times out
- "Too many requests" messages

**Causes:**
- Monitoring too many committees (624 max)
- Very short window (fetches many documents per committee)
- Multiple workflows running simultaneously

**Solutions:**

**Monitor only essential committees:**
```bash
# Remove unnecessary committees
cordis-data monitor remove-committee C70408

# List current
cordis-data monitor list-committees
```

**Use longer intervals:**
- Modify GitHub Actions schedule to run less frequently
- Edit `.github/workflows/monitor-committees.yml`:
  ```yaml
  schedule:
    - cron: "0 */6 * * *"  # Every 6 hours instead of daily
  ```

**Stagger runs if monitoring 500+ committees:**
- Run multiple workflows with different committee subsets
- Or use manual trigger (`workflow_dispatch`) for batch runs

### 7. "Rate limiter exceeded" errors

**Error:**
```
cordis_data.api.rate_limiter: Rate limit exceeded
```

**Cause:**
- System hitting internal 2 req/sec limit with many committees

**Solution:**
1. Monitor fewer committees (200-300 is comfortable)
2. Run fetch during off-peak hours
3. Increase `--window` to fewer but larger fetches

### 8. Documents keep disappearing

**Symptoms:**
- Documents appeared yesterday
- Missing from documents.json today
- But still in changelog

**Causes:**
- Documents older than 90 days are purged (by design)
- Documents deleted from EU API

**This is expected behavior:**
- System maintains rolling 90-day window
- Changelog keeps audit trail indefinitely
- To preserve longer history: Archive `data/committees/changelog/` separately

### 9. Same document appears multiple times in alerts

**Symptoms:**
- Same document appears in multiple Slack messages
- Document shows as "NEW" every day

**Causes:**
- Document reference not consistent across API calls
- Document metadata includes timestamp

**Solution:**
- Document references should be stable
- If this occurs, check:
  1. API still returning same `documentReference`
  2. No accidental clearing of `documents.json`
  3. Workflow running with correct output path

### 10. "Authentication failed" for GitHub Issues

**Symptoms:**
- GitHub Issues not being created
- Logs show auth error

**Causes:**
- `GH_TOKEN` not set
- Token doesn't have `repo` scope
- Token is expired

**Solutions:**

**Check token is set:**
1. Go to Settings → Secrets and variables → Actions
2. Look for `GH_TOKEN`
3. If missing: Create new token at https://github.com/settings/tokens

**Verify token scope:**
1. Go to https://github.com/settings/tokens
2. Find token for CORDIS
3. Verify it has `repo` (full repo access) scope
4. If not, delete and create new with correct scope

**Token expired:**
- GitHub tokens expire after 1 year
- Create new token and update secret

### 11. "No input data" or similar errors

**Symptoms:**
- Fetch fails with "No input data" or similar
- Stack trace shows error in data processing

**Solutions:**

**Enable debug logging:**
```bash
export CORDIS_DEBUG=1
cordis-data monitor fetch --window 90
```

**Try a known working committee:**
```bash
# Reset to known good state
cordis-data monitor remove-committee YOUR_COMMITTEE
cordis-data monitor add-committee C70408
cordis-data monitor fetch
```

**Check data file integrity:**
```bash
# If documents.json is corrupted, start fresh
rm data/committees/documents.json
cordis-data monitor fetch
```

### 12. Workflow times out after 5 minutes

**Symptoms:**
- Workflow job times out
- Monitoring 500+ committees
- Logs show incomplete fetch

**Solutions:**

1. **Monitor fewer committees** (200-300 max)
2. **Run multiple workflows** with subsets of committees
3. **Increase timeout** (if allowed by GitHub plan):
   - Edit `.github/workflows/monitor-committees.yml`
   - Add `timeout-minutes: 15` to job

## Debug Mode

Enable detailed logging:
```bash
export CORDIS_DEBUG=1
cordis-data monitor fetch --window 90
```

This shows:
- API request details
- Rate limiter state
- Change detection logs
- File I/O operations

## Getting Help

If issues persist:

1. **Check logs:**
   - Local: Run with `CORDIS_DEBUG=1`
   - GitHub: Check workflow logs in Actions tab

2. **Verify setup:**
   - Run: `cordis-data monitor list-committees`
   - Check: `cordis-data monitor config-show`

3. **Test API directly:**
   - Use curl to hit endpoints directly
   - Verify committees exist

4. **File an issue:**
   - Include: Committee code, error message, logs
   - Include: Output of `cordis-data monitor list-committees`
   - Include: Relevant workflow logs

## Rate Limits and Quotas

- **API Rate Limit:** 2 requests/second (enforced by client)
- **Max Committees:** 624 (all EU committees)
- **Recommended:** Monitor 200-400 committees per workflow
- **Storage:** 1 day = ~100KB of changelog data

## Performance Expectations

- **Single committee:** < 1 second
- **100 committees:** < 5 seconds
- **624 committees:** < 5 minutes

If consistently slower, check:
- Internet connectivity
- API responsiveness: https://ec.europa.eu/transparency/comitology-register/
- System resources (CPU, memory, disk I/O)
