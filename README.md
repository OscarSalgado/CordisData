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

## Data

- `data/calls.json` — Available EU funding calls
- `data/projects.json` — Awarded projects with CORDIS enrichment
- `data/.metadata.json` — Fetch timestamps and freshness info

## License

MIT