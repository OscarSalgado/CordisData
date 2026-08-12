# GitHub Actions Workflow Decoupling - Design

## Architecture

### Current State (Problematic)

```
fetch-calls.yml (02:00 UTC)
├─ Setup
├─ Fetch open calls → calls/open.jsonl.gz
├─ Fetch closed calls → calls/closed.jsonl.gz
├─ Fetch projects ← PROBLEM: belongs in fetch-projects.yml
├─ Validate (checks for both calls and projects)
└─ Commit (mixes calls + projects data)
    └─ Pushes both to main branch

fetch-projects.yml (04:00 UTC)
├─ Setup
├─ Fetch projects → projects.json ← DUPLICATE WORK
├─ Validate
└─ Commit projects.json
    └─ Pushes to main branch
```

**Problem**: Projects fetched twice, workflows have mixed concerns.

### Desired State (Decoupled)

```
fetch-calls.yml (02:00 UTC)
├─ Setup
├─ Fetch open calls → calls/open.jsonl.gz
├─ Fetch closed calls → calls/closed.jsonl.gz
├─ Validate calls data (checks .jsonl.gz files only)
└─ Commit calls data only
    └─ Pushes calls changes to main branch

fetch-projects.yml (04:00 UTC) — INDEPENDENT
├─ Setup
├─ Fetch projects → projects.json
├─ Validate projects data
└─ Commit projects data only
    └─ Pushes projects changes to main branch
```

**Benefit**: Each workflow has single responsibility, no duplication.

## Changes Required

### 1. fetch-calls.yml

**Remove:**
- Entire step: "Discover projects from closed calls" (lines 64-77)

**Update: "Validate fetched data" step**
- Change validation to check for `.jsonl.gz` files:
  - `data/calls/open.jsonl.gz` (was: `data/calls.open.json`)
  - `data/calls/closed.jsonl.gz` (was: `data/calls.closed.json`)
- Remove validation for `data/projects.json` (not our concern anymore)
- Remove references to projects in status messages

**Update: "Commit and push changes" step**
- Remove: `git add data/projects.json`
- Commit message should be calls-specific (already is: "chore(data): fetch calls")
- Only add calls-related files:
  - `data/calls/open.jsonl.gz`
  - `data/calls/closed.jsonl.gz`
  - `data/calls/changelog/`

### 2. fetch-projects.yml

**No changes needed** — Already independent and correct.

## Implementation Details

### File Paths Updated in Validation

Before:
```bash
if [ -f data/calls.open.json ]; then
  size=$(wc -c < data/calls.open.json)
  count=$(python -c "import json; print(len(json.load(open('data/calls.open.json'))))" 2>/dev/null || echo "unknown")
  echo "calls.open.json exists"
```

After:
```bash
if [ -f data/calls/open.jsonl.gz ]; then
  size=$(wc -c < data/calls/open.jsonl.gz)
  # For compressed files, we can't easily count records without decompressing
  # Just report file size
  echo "calls/open.jsonl.gz exists"
```

### Changelog Path Updates

Before:
```bash
git add data/changelog/open/*.json 2>/dev/null || true
git add data/changelog/closed/*.json 2>/dev/null || true
```

After:
```bash
git add data/calls/changelog/open/*.json 2>/dev/null || true
git add data/calls/changelog/closed/*.json 2>/dev/null || true
```

## Dependencies and Constraints

- **No code changes required** — Only GitHub Actions YAML files
- **Data format already migrated** — JSONL.GZ files already exist from previous change
- **No breaking changes** — CLI commands remain the same
- **Schedule intact** — fetch-calls still runs at 02:00, fetch-projects at 04:00

## Testing

1. Manually trigger both workflows
2. Verify fetch-calls commit contains only calls files
3. Verify fetch-projects commit contains only projects files
4. Check logs to confirm "Discover projects" step is gone
5. Run overnight and verify schedule works

## Rollback

If needed, revert changes to `.github/workflows/fetch-calls.yml` and fetch-projects will still work independently.
