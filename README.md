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
  - Generates a daily changelog and auto-prunes after 90 days
  - Commits data/calls/* and `data/.metadata.json`

- **Projects**: Daily at 04:00 UTC (`fetch-projects.yml`)
  - Fetches awarded projects for closed calls
  - Enriches with CORDIS objective & DOI
  - Checkpoints every 500 projects (resumable on failure)
  - Commits `data/projects.json` and `data/.metadata.json`

- **Committee Documents**: Daily at 06:00 UTC (`monitor-committees.yml`)
  - Monitors EU committee documents from comitology-register
  - Detects new documents from last 90 days
  - Sends alerts on new documents (Slack, GitHub Issues)
  - Commits data/committees/* and changelog

All workflows use `github-actions[bot]` and include timestamps in commit messages.

Configure committee monitoring: See [Committee Monitoring Guide](./docs/committee-monitoring.md)

## Data

Data is organized by dataset type and stored in compressed JSONL.GZ format for efficient storage:

**Calls** (open/closed funding opportunities):
- `data/calls/open.jsonl.gz` — Active/forthcoming EU funding calls (compressed JSONL)
- `data/calls/closed.jsonl.gz` — Closed EU funding calls (compressed JSONL)
- `data/calls/changelog/{open,closed}/` — Daily changelog of call changes

**Projects** (awarded research projects):
- `data/projects.json` — Awarded projects with CORDIS enrichment

**Committee Documents** (EU committee meeting documents):
- `data/committees/documents.jsonl.gz` — Committee documents (compressed JSONL, rolling 90-day window)
- `data/committees/changelog/` — Daily changelog of document changes

**Metadata**:
- `data/.metadata.json` — Fetch timestamps and freshness info

### Data Format

Calls and committee document data is stored in **JSONL.GZ format** (JSON Lines compressed with gzip):
- Each record is one line of JSON
- Compressed with gzip (~85% size reduction)
- UTF-8 normalized to NFC canonical form
- Decompression is fast (~17ms for 8.5MB)

To read in Python:
```python
from cordis_data.utils.compression import JSONLGzipReader

reader = JSONLGzipReader("data/calls/open.jsonl.gz")
calls = reader.read_all()  # Load all records
# or stream line-by-line:
for call in reader.read_records():
    process(call)
```

Changelogs are retained for 90 days and auto-pruned on each fetch.

## License

MIT