# GitHub Actions Workflows Specification

## Purpose

Define the behavior, responsibilities, and data handling of GitHub Actions workflows for fetching calls and projects data.

## Requirements

### Requirement: Fetch Calls Workflow Independence
The `fetch-calls.yml` workflow SHALL fetch and commit only call-related data (open calls, closed calls, and their changelogs) without any project discovery logic.

#### Scenario: Fetch calls data only
- **WHEN** fetch-calls.yml runs on schedule (02:00 UTC daily)
- **THEN** it fetches open calls from SEDIA API
- **AND** fetches closed calls from comitology-register API
- **AND** writes to `data/calls/open.jsonl.gz` and `data/calls/closed.jsonl.gz`
- **AND** does NOT attempt to discover or fetch projects

#### Scenario: Validate JSONL.GZ format
- **WHEN** validation step executes
- **THEN** it checks for existence of `data/calls/open.jsonl.gz`
- **AND** checks for existence of `data/calls/closed.jsonl.gz`
- **AND** verifies changelog files exist at `data/calls/changelog/open/` and `data/calls/changelog/closed/`
- **AND** does NOT check for `data/projects.json`

#### Scenario: Commit calls data only
- **WHEN** changes are validated and present
- **THEN** git staging includes only calls-related files
- **AND** includes `data/calls/open.jsonl.gz`
- **AND** includes `data/calls/closed.jsonl.gz`
- **AND** includes `data/calls/changelog/`
- **AND** does NOT include projects.json or other project data
- **AND** commit message is calls-focused: "chore(data): fetch calls..."

### Requirement: Fetch Projects Workflow Independence
The `fetch-projects.yml` workflow SHALL run independently and fetch projects without any dependency on real-time calls data freshness.

#### Scenario: Projects fetched independently
- **WHEN** fetch-projects.yml runs on schedule (04:00 UTC daily)
- **THEN** it fetches projects using whatever calls data is currently available
- **AND** uses `data/calls/closed.jsonl.gz` if available
- **AND** writes to `data/projects.json`
- **AND** runs completely independent of fetch-calls.yml status

#### Scenario: No project duplication
- **WHEN** both workflows run
- **THEN** projects are fetched exactly once per day
- **AND** not fetched in multiple workflows
- **AND** commit history shows distinct calls commits and projects commits

### Requirement: Workflow Separation of Concerns
Each workflow SHALL have clear, non-overlapping responsibilities.

#### Scenario: Calls workflow scope
- **WHEN** fetch-calls.yml executes
- **THEN** its steps are: setup, fetch open calls, fetch closed calls, validate, commit
- **AND** includes no project-related steps
- **AND** logs only calls-related information

#### Scenario: Projects workflow scope
- **WHEN** fetch-projects.yml executes
- **THEN** its steps are: setup, fetch projects, validate, commit
- **AND** includes no calls-related steps
- **AND** logs only projects-related information

## Data Schema

### fetch-calls.yml Output

Files committed:
- `data/calls/open.jsonl.gz` — Open/forthcoming calls (JSONL.GZ format)
- `data/calls/closed.jsonl.gz` — Closed/expired calls (JSONL.GZ format)
- `data/calls/changelog/open/*.json` — Daily changelog snapshots for open calls
- `data/calls/changelog/closed/*.json` — Daily changelog snapshots for closed calls

### fetch-projects.yml Output

Files committed:
- `data/projects.json` — Awarded projects with CORDIS enrichment

## Constraints

- **fetch-calls runs first** at 02:00 UTC
- **fetch-projects runs later** at 04:00 UTC (independent timing, no coupling)
- **No real-time dependency** — Projects can work with calls data that is hours or days old
- **Format consistency** — Calls data in JSONL.GZ, projects in JSON
- **Commit isolation** — Each workflow commits only its own data

## Success Criteria

- ✓ fetch-calls.yml contains no project discovery steps
- ✓ fetch-projects.yml contains no calls-related steps
- ✓ Validation in fetch-calls checks only for .jsonl.gz files
- ✓ Commits from each workflow contain only relevant data
- ✓ Projects fetched exactly once per day (no duplication)
- ✓ Both workflows pass independently
- ✓ Logs clearly separate calls and projects operations
