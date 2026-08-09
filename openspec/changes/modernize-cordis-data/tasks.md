## 1. Project Setup & Configuration

- [ ] 1.1 Create `pyproject.toml` with project metadata, dependencies (Click, Pydantic), and dev-dependencies (pytest, pytest-cov, flake8, pyright)
- [ ] 1.2 Create `.python-version` file specifying Python 3.12
- [ ] 1.3 Create `.gitignore` entries for Python artifacts, test coverage, and development directories
- [ ] 1.4 Create `src/cordis_data/__init__.py` with version and public API exports

## 2. Restructure Code: API Layer

- [ ] 2.1 Create `src/cordis_data/api/` subpackage with `__init__.py`
- [ ] 2.2 Create `src/cordis_data/api/rate_limiter.py` — Extract TokenBucket from fetch_projects.py
- [ ] 2.3 Create `src/cordis_data/api/sedia.py` — SediaClient: Extract SEDIA API logic into a reusable client class
- [ ] 2.4 Create `src/cordis_data/api/cordis.py` — CordisClient: Extract CORDIS API logic into a reusable client class
- [ ] 2.5 Add type hints to all API client methods
- [ ] 2.6 Update `src/cordis_data/api/__init__.py` to export SediaClient, CordisClient, TokenBucket

## 3. Restructure Code: Models & Utilities

- [ ] 3.1 Create `src/cordis_data/models.py` with Pydantic models for Call and Project
- [ ] 3.2 Create `src/cordis_data/utils.py` with shared functions (normalize_date, extract_budget, parse_action_type, merge utilities)
- [ ] 3.3 Create `src/cordis_data/config.py` with configuration constants (API_URL, CORDIS_URL_TEMPLATE, rate limits, TTLs, status maps, programme names)
- [ ] 3.4 Add comprehensive docstrings and type hints to all modules

## 4. Restructure Code: Data Layer

- [ ] 4.1 Create `src/cordis_data/data/` subpackage with `__init__.py`
- [ ] 4.2 Create `src/cordis_data/data/metadata.py` — Extract metadata/freshness logic (load_metadata, save_metadata, is_stale, update_timestamp)
- [ ] 4.3 Create `src/cordis_data/data/merger.py` — Extract merge and change-summary logic (merge_calls, merge_projects, summarize_changes)
- [ ] 4.4 Create `src/cordis_data/data/fetcher.py` — Abstract base Fetcher class with common interface
- [ ] 4.5 Create `src/cordis_data/data/calls.py` — CallsFetcher class (refactored from fetch_calls.py)
- [ ] 4.6 Create `src/cordis_data/data/projects.py` — ProjectsFetcher class (refactored from fetch_projects.py)
- [ ] 4.7 Update `src/cordis_data/data/__init__.py` to export fetcher classes
- [ ] 4.8 Ensure all data modules accept dependency-injected clients (for testability)

## 5. Create CLI Layer

- [ ] 5.1 Create `src/cordis_data/cli.py` with Click commands: `fetch-calls`, `fetch-projects`, `status`
- [ ] 5.2 Implement `fetch-calls` command with `--full-history` option
- [ ] 5.3 Implement `fetch-projects` command with `--years` option
- [ ] 5.4 Implement `status` command to display metadata (last fetch timestamps, record counts, freshness)
- [ ] 5.5 Add proper error handling and user-friendly messages to CLI

## 6. Create Test Infrastructure

- [ ] 6.1 Create `tests/` directory with structure: `unit/`, `integration/`, `conftest.py`, `fixtures/`
- [ ] 6.2 Create `tests/conftest.py` with reusable pytest fixtures (mock clients, temporary directories, sample data)
- [ ] 6.3 Create `tests/fixtures/` directory with realistic API response JSON files (sedia_calls.json, cordis_project.json, etc.)

## 7. Write Unit Tests: API Clients

- [ ] 7.1 Create `tests/unit/test_api_sedia.py` — Test SediaClient (mocked HTTP, query building, pagination, retry logic)
- [ ] 7.2 Create `tests/unit/test_api_cordis.py` — Test CordisClient (rate limiting, 404 handling, JSON parsing)
- [ ] 7.3 Create `tests/unit/test_api_rate_limiter.py` — Test TokenBucket (token regeneration, concurrent access, blocking)

## 8. Write Unit Tests: Models

- [ ] 8.1 Create `tests/unit/test_models.py` — Test Call and Project Pydantic models (validation, serialization, edge cases)

## 9. Write Unit Tests: Utilities

- [ ] 9.1 Create `tests/unit/test_utils.py` — Test utility functions (date normalization, budget extraction, action type parsing, merge logic)

## 10. Write Unit Tests: Data Layer

- [ ] 10.1 Create `tests/unit/test_data_metadata.py` — Test metadata loading/saving, freshness checks
- [ ] 10.2 Create `tests/unit/test_data_merger.py` — Test merge_calls, merge_projects, summarize_changes logic
- [ ] 10.3 Create `tests/unit/test_data_calls.py` — Test CallsFetcher with mocked SediaClient (full workflow: query building, fetching, merging, marking expired)
- [ ] 10.4 Create `tests/unit/test_data_projects.py` — Test ProjectsFetcher with mocked clients (full workflow: batching, fetching, CORDIS enrichment)

## 11. Write Integration Tests (Optional)

- [ ] 11.1 Create `tests/integration/test_end_to_end.py` — End-to-end fetch workflow with fixture data (no real API calls)

## 12. Add Linting Configuration

- [ ] 12.1 Add flake8 configuration to `pyproject.toml` (max-line-length, extend-ignore, etc.)
- [ ] 12.2 Add pyright configuration to `pyproject.toml` (strict mode, ignore patterns)
- [ ] 12.3 Run `flake8 src/ tests/` and fix all violations
- [ ] 12.4 Run `pyright` and fix all type errors (add missing type hints)

## 13. Verify Test Coverage

- [ ] 13.1 Run `pytest --cov=src/cordis_data --cov-report=html` and verify 100% coverage
- [ ] 13.2 Fix any uncovered code or document why coverage is not 100% (e.g., `if __name__ == "__main__"` blocks)

## 14. Create GitHub Actions Workflows

- [ ] 14.1 Create `.github/workflows/test.yml` — Run pytest + coverage on every push/PR
- [ ] 14.2 Create `.github/workflows/lint.yml` — Run flake8 + pyright on every push/PR
- [ ] 14.3 Create `.github/workflows/fetch-calls.yml` — Scheduled job (e.g., daily) to run `cordis-data fetch-calls`
- [ ] 14.4 Create `.github/workflows/fetch-projects.yml` — Scheduled job (e.g., daily) to run `cordis-data fetch-projects`
- [ ] 14.5 Ensure workflows upload test results and coverage reports as artifacts

## 15. Configure Dependabot

- [ ] 15.1 Create `.github/dependabot.yml` with configuration for `pip` (Python dependencies)
- [ ] 15.2 Add configuration for `github-actions` to Dependabot
- [ ] 15.3 Set Dependabot to group dependency updates to reduce PR noise
- [ ] 15.4 Test Dependabot by checking that it can create a test PR manually

## 16. Documentation & Cleanup

- [ ] 16.1 Update or create `README.md` with installation instructions, CLI usage examples, and library usage examples
- [ ] 16.2 Add docstrings/comments for any complex logic
- [ ] 16.3 Verify that `pip install -e .` works and CLI is available
- [ ] 16.4 Test importing from `cordis_data` in a Python REPL (models, API clients, utilities)
- [ ] 16.5 Remove or archive old scripts (fetch_calls.py, fetch_projects.py at root) — they're now in the module

## 17. Final Validation

- [ ] 17.1 Run full test suite: `pytest` — all tests pass
- [ ] 17.2 Run linting: `flake8 src/ tests/` — no violations
- [ ] 17.3 Run type checking: `pyright` — no errors
- [ ] 17.4 Verify coverage: `pytest --cov=src/cordis_data` — 100% coverage
- [ ] 17.5 Test CLI locally: `cordis-data fetch-calls`, `cordis-data status`, etc.
- [ ] 17.6 Verify GitHub Actions workflows pass locally (or on a test branch)
