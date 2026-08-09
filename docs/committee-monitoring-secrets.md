# Committee Monitoring - GitHub Secrets Setup

This guide shows how to configure GitHub repository secrets for committee monitoring alerts.

## Required Secrets

### CORDIS_SLACK_WEBHOOK
Slack incoming webhook URL for sending alerts about new documents.

**How to get:**
1. Go to https://api.slack.com/apps
2. Create a new app or select existing one
3. Go to "Incoming Webhooks" and click "Add New Webhook to Workspace"
4. Select channel and authorize
5. Copy the webhook URL

**How to set in GitHub:**
1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `CORDIS_SLACK_WEBHOOK`
4. Value: Paste the webhook URL
5. Click "Add secret"

## Optional Secrets

### GH_TOKEN
GitHub Personal Access Token for creating issues when new documents are detected.

**How to get:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name (e.g., "cordis-monitoring")
4. Select scopes: `repo` (full repo access)
5. Click "Generate token"
6. Copy the token immediately (you won't see it again)

**How to set in GitHub:**
1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `GH_TOKEN`
4. Value: Paste the token
5. Click "Add secret"

## Testing

To test the setup without waiting for the scheduled run:
1. Go to Actions tab
2. Select "Monitor Committee Documents"
3. Click "Run workflow"
4. Choose branch and click "Run workflow"

Check the workflow logs to verify secrets are accessible.

## Troubleshooting

**Workflow fails with "Webhook authentication failed"**
- Check that `CORDIS_SLACK_WEBHOOK` secret is set correctly
- Verify the webhook URL is still valid (they can expire)

**GitHub issues not being created**
- Check that `GH_TOKEN` secret is set and has `repo` scope
- Verify the token hasn't expired

**"No changes to commit" in logs**
- This is normal if no new documents were found
- The workflow still ran successfully
