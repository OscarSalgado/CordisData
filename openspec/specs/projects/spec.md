# ProjectsFetcher Specification

## Purpose

Define the API contracts, data schemas, and behavior of ProjectsFetcher for incremental discovery of awarded projects from closed call topics.

## Requirements

### Requirement: Rolling Window Fetch

The system SHALL fetch and enrich awarded projects for closed call topics within a rolling 1-year window.

#### Scenario: First run (empty state)
- **WHEN** projects.json does not exist
- **THEN** fetch all topics from calls/closed.jsonl.gz closed within last 1 year
- **AND** create projects.json with enriched projects

#### Scenario: Subsequent runs (always fetch recent)
- **WHEN** projects.json exists with N projects
- **THEN** fetch all topics from calls/closed.jsonl.gz closed within last 1 year again
- **AND** append only new projects to existing projects.json (dedup)

#### Scenario: Skip old calls
- **WHEN** a closed call has deadline >1 year ago
- **THEN** skip that topic (optimization: no new activity expected)
- **AND** do not fetch from SEDIA

### Requirement: Topic-to-Projects Mapping

The system SHALL maintain a 1-to-many relationship: one topicId can have 0 or many awarded projects.

#### Scenario: Topic with multiple projects
- **WHEN** topicId has multiple awarded projects
- **THEN** all projects are added to projects.json
- **AND** all share the same topicId

#### Scenario: Topic with zero projects
- **WHEN** a closed call topic has no awarded projects (e.g., cancelled, no funding)
- **THEN** log the topic as "no projects found"
- **AND** mark topic as visited (do not re-fetch on next run)
- **AND** continue to next topic (graceful degradation)

### Requirement: CORDIS Enrichment

The system SHALL enrich each project with CORDIS narrative data (objective, grantDoi).

#### Scenario: CORDIS enrichment success
- **WHEN** SEDIA project is fetched
- **THEN** request additional data from CORDIS API (by projectId)
- **AND** merge objective and grantDoi into the project record
- **AND** add to projects.json

#### Scenario: CORDIS enrichment fails
- **WHEN** CORDIS API returns error for a projectId
- **THEN** log warning
- **AND** save project without objective/grantDoi (partial enrichment)
- **AND** continue to next project

#### Scenario: Rate limiting
- **WHEN** enriching multiple projects
- **THEN** respect CORDIS rate limit of max 2 requests/second
- **AND** queue and schedule requests accordingly

### Requirement: Deduplication

The system SHALL prevent duplicate entries in projects.json using (topicId, projectId) as key.

#### Scenario: New project for existing topic
- **WHEN** fetching projects for a topicId that already has projects in projects.json
- **THEN** check each project's projectId
- **AND** only append projects with new projectIds (not seen before)
- **AND** skip projects with duplicate (topicId, projectId) pairs

#### Scenario: Duplicate (topicId, projectId) pair
- **WHEN** a (topicId, projectId) pair already exists in projects.json
- **THEN** do not add it again (idempotent)
- **AND** keep the existing entry unchanged

### Requirement: Always-Running

The system SHALL run on every invocation without freshness checks, fetching recent topics each time.

#### Scenario: Always fetch recent topics
- **WHEN** fetch-projects is invoked
- **THEN** fetch all topics from calls.closed.json closed within last 1 year
- **AND** do not check freshness TTL or skip based on metadata
- **AND** append new projects to existing projects.json (idempotent)

#### Scenario: No explicit freshness gate
- **WHEN** user runs fetch-projects multiple times in quick succession
- **THEN** each run processes topics independently
- **AND** same projects are deduplicated, no duplicates added
- **AND** only new projects are appended

### Requirement: Read closed calls from JSONL.GZ file
ProjectsFetcher._load_closed_calls() SHALL read closed calls from `data/calls/closed.jsonl.gz`, parsing JSONL format (one record per line) and decompressing gzip, rather than reading `data/calls.closed.json`.

#### Scenario: Load closed calls from new location
- **WHEN** ProjectsFetcher._load_closed_calls() is called
- **THEN** it reads from `data/calls/closed.jsonl.gz` (not `data/calls.closed.json`)
- **AND** system decompresses gzip stream
- **AND** parses each line as a separate JSON record
- **AND** returns list of closed call dicts as before

#### Scenario: Extract topic IDs for project fetching
- **WHEN** closed calls are loaded
- **THEN** system extracts topic IDs from each record
- **AND** uses them to query SEDIA API for awarded projects
- **AND** behavior is identical to before (same topic ID extraction logic)

#### Scenario: Default path resolution
- **WHEN** no calls_path is provided to _load_closed_calls()
- **THEN** system uses default path: `data/calls/closed.jsonl.gz`
- **AND** gracefully handles missing file with clear error message
- **AND** suggests checking new data organization structure

### Requirement: Source Data

The system SHALL consume only closed calls (not open calls).

#### Scenario: Closed calls only
- **WHEN** ProjectsFetcher runs
- **THEN** read from calls.closed.jsonl.gz (pre-filtered closed calls in new format)
- **AND** ignore open calls entirely
- **AND** do not attempt to fetch projects for open calls

#### Scenario: Year filtering (optional)
- **WHEN** user provides --years N
- **THEN** filter calls by deadline >= (today - N*365 days)
- **AND** only fetch projects for those filtered calls

### Requirement: Error Handling

The system SHALL handle errors gracefully without losing data.

#### Scenario: Transient error (network)
- **WHEN** SEDIA API is temporarily unavailable
- **THEN** retry with exponential backoff (max 3 attempts)
- **AND** if still fails, stop fetch (resumable on next run)
- **AND** do not mark topic as visited (will be retried)

#### Scenario: Permanent error (invalid topicId)
- **WHEN** SEDIA returns 404 or validation error for a topicId
- **THEN** log error
- **AND** skip this topic (mark as visited, don't retry)
- **AND** continue to next topic

#### Scenario: Write failure
- **WHEN** writing projects.json fails (disk full, permission, etc.)
- **THEN** fail fast (exit with error code)
- **AND** do not update metadata (next run will retry from same checkpoint)

### Requirement: Metadata Tracking

The system SHALL maintain metadata for observability.

#### Scenario: Metadata fields
- **WHEN** ProjectsFetcher completes
- **THEN** metadata contains:
  - projects_topics_processed_count: total topics processed this cycle
  - projects_fetched_at: timestamp when this fetch cycle started
  - projects_freshness_ttl_days: default 30 (projects are fresh for 30 days)
  - projects_rolling_window_days: 365 (only fetch topics from last 1 year)
  - projects_topics_without_projects_count: topics with 0 awarded projects

#### Scenario: Progress reporting
- **WHEN** user runs `cordis-data status`
- **THEN** display:
  - Projects: Last fetched at <timestamp>
  - Freshness: <days since last fetch> days ago (TTL: 30 days)
  - Rolling window: 365 days (topics >1 year old are skipped)

### Requirement: CLI Interface

The system SHALL provide CLI commands for project fetching.

#### Scenario: Basic fetch
- **WHEN** user runs `cordis-data fetch-projects`
- **THEN** fetch from calls.closed.json (default path)
- **AND** write to projects.json (default path)
- **AND** always run (no freshness check)

#### Scenario: Custom paths
- **WHEN** user runs `cordis-data fetch-projects --calls-closed /path/to/calls.jsonl.gz --output /path/to/projects.json`
- **THEN** use custom paths instead of defaults

#### Scenario: Help
- **WHEN** user runs `cordis-data fetch-projects --help`
- **THEN** show usage with options:
  - --calls-closed PATH (default: data/calls/closed.jsonl.gz)
  - --output PATH (default: data/projects.json)

## Data Schema

### projects.json Structure

```json
[
  {
    "topicId": "HORIZON-2023-CL5-01-01",
    "projectId": "999999",
    "title": "Project Title",
    "acronym": "PT",
    "status": "funded",
    "programme": "Horizon Europe",
    
    "coordinator": "University of Example",
    "coordinatorCode": "1234567",
    "coordinatorCountry": "IT",
    
    "participantCount": 5,
    
    "startDate": "2023-01-01",
    "endDate": "2025-12-31",
    
    "budget": 1000000,
    "euroBudget": 1000000,
    
    "objective": "Project objective and description (from CORDIS)...",
    "grantDoi": "10.3030/123456789",
    
    "fetchedAt": "2026-08-10T12:00:00Z"
  }
]
```

**Primary key:** (topicId, projectId)
**Indexing:** By topicId for O(1) deduplication checks

### Metadata Structure

```json
{
  "projects_topics_processed_count": 2140,
  "projects_fetched_at": "2026-08-10T12:00:00Z",
  "projects_freshness_ttl_days": 30,
  "projects_rolling_window_days": 365,
  "projects_topics_without_projects_count": 1234
}
```

## Constraints

- **Sequential processing:** Topics are processed one at a time (no parallelism)
- **Rate limiting:** CORDIS enrichment max 2 requests/second
- **Rolling window:** Only fetch topics with deadline >= (today - 365 days)
- **Always-running:** No freshness check, fetch on every invocation
- **Append-only projects:** New projects added, never overwritten or removed
- **No resumption state:** Single pass per run, no checkpointing

## Success Criteria

- ✓ Topics with deadline < (today - 1 year) are skipped (optimization)
- ✓ Topics with deadline >= (today - 1 year) are fetched on each run
- ✓ projects.json contains all awarded projects with no duplicate (topicId, projectId) pairs
- ✓ New projects appear on each run (appended, not replaced)
- ✓ CORDIS enrichment adds objective and grantDoi to each project
- ✓ Graceful handling of topics with 0 projects (logged, not failed)
- ✓ Rate limiting respected (2 req/s to CORDIS)
- ✓ Idempotent: running twice produces same projects.json
- ✓ Metadata accurately reflects progress (topics_processed_count)
