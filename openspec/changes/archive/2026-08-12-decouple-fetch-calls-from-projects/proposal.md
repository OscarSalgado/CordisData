# Decouple Fetch Calls from Fetch Projects

## Summary

Separate the GitHub Actions workflows for `fetch-calls` and `fetch-projects` to eliminate workflow coupling and simplify CI/CD responsibilities.

## Problem

Currently, `fetch-calls.yml` (runs at 02:00 UTC) includes a step that discovers and fetches projects via `cordis-data fetch-projects`. This creates several issues:

1. **Workflow coupling** — Calls workflow has responsibility for projects logic
2. **Duplicated work** — Projects are fetched twice:
   - Once in fetch-calls.yml (02:00 UTC)
   - Again in fetch-projects.yml (04:00 UTC)
3. **Mixed concerns** — Calls workflow commits both calls AND projects data
4. **Unclear dependencies** — No clear separation between what depends on what
5. **Outdated validation** — Validation still checks for `.json` files, not `.jsonl.gz`

## Solution

Remove the "Discover projects from closed calls" step from `fetch-calls.yml` entirely. Let `fetch-projects.yml` handle all project fetching independently:

**fetch-calls.yml changes:**
- Remove step: "Discover projects from closed calls"
- Update validation to check for `.jsonl.gz` files instead of `.json`
- Commit ONLY calls data (calls.{open,closed}.jsonl.gz, changelog)

**fetch-projects.yml:**
- No changes needed (already independent)
- Continues running at 04:00 UTC daily
- Works with whatever calls data is available (no tight coupling)

## Rationale

- **Projects are not time-dependent on calls** — They have ~6 month difference between call closure and project award discovery, so real-time sync is unnecessary
- **Each workflow has single responsibility** — calls handles calls, projects handles projects
- **Simpler testing and debugging** — Can run each workflow independently without side effects
- **Cleaner commits** — Git history shows what actually changed (calls or projects, not both)
- **Updated to new data format** — Aligns with JSONL.GZ migration already completed

## Acceptance Criteria

- [ ] "Discover projects from closed calls" step removed from fetch-calls.yml
- [ ] Validation updated to check for .jsonl.gz files
- [ ] fetch-calls.yml only commits calls data
- [ ] fetch-projects.yml remains unchanged and independent
- [ ] Both workflows run successfully on schedule
- [ ] No duplicate project fetching

## Impact

- **Scope**: CI/CD workflows only (GitHub Actions YAML files)
- **Data**: No change to data format or content
- **APIs**: No changes to CLI commands or Python code
- **Breaking changes**: None

## Timeline

Quick change, 1-2 hours implementation.
