# CordisData

Collect and manage EU research funding data from CORDIS and SEDIA APIs.

## Installation

```bash
git clone <repo>
cd cordis-data
pip install -e ".[dev]"  # with dev dependencies for testing
```

## Quick Start

### CLI Usage

Fetch open/forthcoming/closed EU grant calls:
```bash
cordis-data fetch-calls
```

Fetch awarded projects and enrich with CORDIS data:
```bash
cordis-data fetch-projects
```

Check status of fetched data:
```bash
cordis-data status
```

Monitor EU committee documents:
```bash
cordis-data monitor add-committee C70408
cordis-data monitor fetch
```

See [Committee Monitoring Guide](./docs/committee-monitoring.md) for details.

### Library Usage

```python
from cordis_data.api import SediaClient, CordisClient
from cordis_data.models import Call, Project
from cordis_data.data import CallsFetcher, ProjectsFetcher

# Use API clients directly
sedia = SediaClient()
cordis = CordisClient()

# Or use high-level fetchers
calls_fetcher = CallsFetcher()
calls_fetcher.fetch()

projects_fetcher = ProjectsFetcher()
projects_fetcher.fetch()
```

## Development

### Running Tests

```bash
pytest                                  # Run all tests
pytest --cov=src/cordis_data           # With coverage
pytest -m unit                         # Only unit tests
```

### Code Quality

```bash
flake8 src/ tests/                     # Style checking
pyright                                # Type checking
```

## Automated Data Collection

GitHub Actions workflows automatically fetch and update data:

- **Calls**: Daily at 02:00 UTC (`fetch-calls.yml`)
  - Fetches open/forthcoming/closed EU funding calls
  - Merges with existing data (preserves older records by default)
  - Generates a daily changelog at `data/changelog/YYYY-MM-DD.json` and deletes
    changelog files older than 90 days
  - Commits `data/calls.json`, `data/.metadata.json`, and `data/changelog/*.json`

- **Projects**: Daily at 04:00 UTC (`fetch-projects.yml`)
  - Fetches awarded projects for closed calls
  - Enriches with CORDIS objective & DOI
  - Checkpoints every 500 projects (resumable on failure)
  - Commits `data/projects.json` and `data/.metadata.json`

- **Committee Documents**: Daily at 06:00 UTC (`monitor-committees.yml`)
  - Monitors EU committee documents from comitology-register
  - Detects new documents from last 90 days
  - Sends alerts on new documents (Slack, GitHub Issues)
  - Generates daily changelog at `data/committees/changelog/YYYY-MM-DD.json`
  - Commits `data/committees/documents.json` and changelog

All workflows use `github-actions[bot]` and include timestamps in commit messages.

Configure committee monitoring: See [Committee Monitoring Guide](./docs/committee-monitoring.md)

## Data

- `data/calls.json` — Available EU funding calls
- `data/projects.json` — Awarded projects with CORDIS enrichment
- `data/committees/documents.json` — EU committee documents (rolling 90-day window)
- `data/.metadata.json` — Fetch timestamps and freshness info
- `data/changelog/YYYY-MM-DD.json` — Daily changelog of call changes
- `data/committees/changelog/YYYY-MM-DD.json` — Daily changelog of committee document changes

Changelogs are retained for 90 days and auto-pruned on each fetch.

## License

MIT