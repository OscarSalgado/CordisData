# CLI Unified Fetch Calls

## Purpose

The CLI `fetch-calls` command provides a unified interface for fetching all EU research funding calls (both open/forthcoming and closed) from the SEDIA API, orchestrating the `OpenCallsFetcher` and `ClosedCallsFetcher` internally for seamless data retrieval with JSONL.GZ output format.

## Requirements

### Requirement: CLI fetch-calls command orchestrates open and closed calls fetchers

The `cordis-data fetch-calls` command SHALL invoke both `OpenCallsFetcher` and `ClosedCallsFetcher` sequentially, writing their outputs to `data/calls/open.jsonl.gz` and `data/calls/closed.jsonl.gz` respectively. The command SHALL preserve all metadata, rate limiting, changelog generation, and HTML transformations from the previous implementation.

#### Scenario: Command fetches both open and closed calls
- **WHEN** user runs `cordis-data fetch-calls`
- **THEN** the system fetches open calls and writes to `data/calls/open.jsonl.gz`
- **THEN** the system fetches closed calls and writes to `data/calls/closed.jsonl.gz`
- **THEN** both operations complete with metadata and changelog entries tracked

#### Scenario: Command preserves rate limiting
- **WHEN** rate limiting would trigger during a fetch operation
- **THEN** the system applies rate limiting uniformly across both fetchers
- **THEN** rate limiting behavior is identical to the previous `CallsFetcher` implementation

#### Scenario: Command handles errors gracefully
- **WHEN** one fetcher fails (e.g., network error, API timeout)
- **THEN** the system reports the error with context (open vs closed)
- **THEN** already-written partial files remain for debugging

#### Scenario: Command applies HTML transformations
- **WHEN** fetching call data that contains HTML content
- **THEN** HTML cleaning and transformation is applied to both open and closed calls
- **THEN** output format and structure match the JSONL.GZ schema

### Requirement: CallsFetcher is removed from public API

The `CallsFetcher` class SHALL be removed from `cordis_data.data` module exports. Code that depends on `CallsFetcher` directly SHALL use `OpenCallsFetcher` and `ClosedCallsFetcher` instead.

#### Scenario: CallsFetcher is no longer importable
- **WHEN** code attempts to import `CallsFetcher` from `cordis_data.data`
- **THEN** import fails with AttributeError or ModuleNotFoundError
- **THEN** error message recommends using `OpenCallsFetcher` and `ClosedCallsFetcher`

#### Scenario: New fetchers are available in public API
- **WHEN** code imports from `cordis_data.data`
- **THEN** `OpenCallsFetcher` and `ClosedCallsFetcher` are available
- **THEN** both fetchers are fully documented for public use
