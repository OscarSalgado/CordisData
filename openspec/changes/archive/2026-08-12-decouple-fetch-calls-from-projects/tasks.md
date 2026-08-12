# Implementation Tasks

## Phase 1: Update fetch-calls.yml

- [x] 1.1 Remove "Discover projects from closed calls" step
  - Delete lines 64-77 (the entire step block)
  - This removes the `cordis-data fetch-projects` call

- [x] 1.2 Update validation to check for JSONL.GZ files
  - Change validation to look for `data/calls/open.jsonl.gz` (not `.json`)
  - Change validation to look for `data/calls/closed.jsonl.gz` (not `.json`)
  - Remove any references to `data/projects.json`
  - Remove projects from validation messages and logs

- [x] 1.3 Update changelog paths in validation
  - Change from `data/changelog/open/` to `data/calls/changelog/open/`
  - Change from `data/changelog/closed/` to `data/calls/changelog/closed/`

- [x] 1.4 Update git staging to only include calls data
  - Keep: `git add data/calls/open.jsonl.gz` (or pattern)
  - Keep: `git add data/calls/closed.jsonl.gz` (or pattern)
  - Keep: `git add data/calls/changelog/`
  - Remove: any references to `data/projects.json`
  - Ensure no orphaned old paths like `data/calls.open.json`

- [x] 1.5 Update commit message and summary
  - Ensure message is calls-specific (should already be: "chore(data): fetch calls")
  - Update workflow summary to only reference calls, not projects

## Phase 2: Verify fetch-projects.yml

- [x] 2.1 Confirm fetch-projects.yml is unchanged
  - Review that it still runs at 04:00 UTC independently
  - Verify it has its own project fetching logic
  - Confirm it doesn't depend on fetch-calls.yml

## Phase 3: Testing

- [x] 3.1 Manually trigger fetch-calls.yml
  - Run workflow manually via GitHub UI
  - Verify only calls files are added in commit
  - Check logs show no project-related steps
  - Confirm commit message is calls-only

- [x] 3.2 Manually trigger fetch-projects.yml
  - Run workflow manually via GitHub UI
  - Verify projects.json is updated
  - Confirm commits are independent

- [x] 3.3 Verify both run successfully on schedule
  - Wait for next scheduled run (or adjust cron for testing)
  - Confirm fetch-calls runs at 02:00 UTC
  - Confirm fetch-projects runs at 04:00 UTC
  - Check that no duplicate project fetching occurs
  - Verify no merge conflicts between workflows

## Phase 4: Documentation & Cleanup

- [x] 4.1 Update CI/CD documentation
  - Document that workflows are now independent
  - Note that calls data is fetched at 02:00, projects at 04:00
  - Clarify that projects do not depend on fresh calls data

- [x] 4.2 Commit all workflow changes
  - Single commit: "refactor(ci): decouple fetch-calls and fetch-projects workflows"
  - Reference this change in commit message

- [x] 4.3 Archive this change
  - After PR merged, archive the change: `openspec archive --change "decouple-fetch-calls-from-projects"`
