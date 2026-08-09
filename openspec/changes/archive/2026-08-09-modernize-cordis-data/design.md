## Context

CordisData currently consists of two Python scripts (`fetch_calls.py`, `fetch_projects.py`) that collect data from EU research funding APIs (SEDIA and CORDIS). The code works but lacks:
- Project structure (not installable, not importable)
- Automated testing (0% coverage)
- Quality gates (no linting, no type checking)
- Dependency management (manual updates)
- Usability (scripts, not CLI)

Goal: Transform into a production-grade Python module that can be used as a library by other applications and maintained with high quality standards.

## Goals / Non-Goals

**Goals:**
- Restructure as installable Python package with clear layered architecture (API clients, data fetchers, models, CLI)
- Achieve 100% test coverage with unit + integration tests
- Add flake8 + pyright gates in CI/CD
- Enable dependency updates via Dependabot (Python + GitHub Actions)
- Provide reusable API clients (`SediaClient`, `CordisClient`) for other projects
- Support both library usage (`from cordis_data.api import SediaClient`) and CLI usage (`cordis-data fetch-calls`)
- Maintain full backward compatibility with existing fetch behavior

**Non-Goals:**
- Change the fetch logic or data model
- Add database/backend storage (keep JSON files)
- Build a web API or dashboard
- Support Python < 3.12
- Add async/await (keep synchronous)

## Decisions

### 1. Python 3.12+ only
**Decision**: Target Python 3.12+ exclusively. No support for older versions.
**Rationale**: Latest stable version provides best DX, security, and performance. Reduces complexity (no version-specific workarounds).
**Alternatives considered**:
- 3.10 minimum (broader compatibility) → rejected: adds CI complexity, no runtime gain
- Pin exact version (3.12.5) → rejected: users should upgrade normally

### 2. `src/` layout for `cordis_data` package
**Decision**: Use `src/cordis_data/` instead of `cordis_data/` at root.
**Rationale**: Industry standard, prevents accidental imports from local package before installation, works better with tools.
**Structure**:
```
src/cordis_data/
  ├── __init__.py
  ├── cli.py                # Entry point
  ├── config.py             # Configuration
  ├── models.py             # Pydantic models (Call, Project)
  ├── utils.py              # Shared utilities
  ├── api/                  # API clients (reusable)
  │   ├── __init__.py
  │   ├── sedia.py
  │   ├── cordis.py
  │   └── rate_limiter.py
  └── data/                 # Data layer (orchestration)
      ├── __init__.py
      ├── fetcher.py        # Abstract base
      ├── calls.py          # CallsFetcher
      ├── projects.py       # ProjectsFetcher
      ├── metadata.py       # Metadata/freshness
      └── merger.py         # Merge logic
```

### 3. Mock-first testing strategy
**Decision**: Unit tests mock API responses; integration tests (if any) use fixtures or test endpoints.
**Rationale**:
- Unit tests must be fast and deterministic (no network calls)
- Mock responses are static JSON from real SEDIA/CORDIS responses (fixtures/)
- Avoids flakiness from API rate limits or changes
- 100% coverage achievable without API access
**Alternatives considered**:
- Live API testing → rejected: slow, flaky, violates rate limits
- VCR.py recording → rejected: adds maintenance burden, still need to refresh cassettes

### 4. Pydantic for data models
**Decision**: Use Pydantic v2 for `Call` and `Project` models.
**Rationale**: Validation, serialization, type safety. Enables contract clarity for library users.
**Alternatives considered**:
- TypedDict → rejected: no validation, no serialization
- dataclasses → rejected: no built-in validation

### 5. CLI via Click or typer
**Decision**: Use Click (lightweight, stable, no async overhead).
**Rationale**: Simple commands, no ASGI/FastAPI complexity.
**Entry points in pyproject.toml**:
```
[project.scripts]
cordis-data = "cordis_data.cli:main"
```

### 6. Pytest + coverage
**Decision**: pytest with pytest-cov for coverage measurement.
**Rationale**: Industry standard, clear test discovery, integrates with CI.
**Threshold**: 100% for `src/cordis_data/`, reasonable (not 100%) for CLI.

### 7. Flake8 + Pyright
**Decision**: Flake8 for style, Pyright for type checking.
**Rationale**: Flake8 is lightweight, Pyright is strict and catches real bugs.
**CI gates**: Fail on any violations.

### 8. Dependabot for all dependencies
**Decision**: Monitor Python deps (main + dev) and GitHub Actions workflows.
**Rationale**: Proactive security updates, automated PR creation.
**Scope**: Everything (not just code dependencies).

### 9. GitHub Actions workflows (scheduled + CI)
**Decision**: Three workflows:
1. **test.yml**: pytest + coverage on every push
2. **lint.yml**: flake8 + pyright on every push
3. **fetch-*.yml**: Scheduled (e.g., daily) for `fetch_calls`, `fetch_projects`
**Rationale**: Clear separation of concerns, scheduled fetches don't block PRs.

### 10. Keep urllib, no external HTTP library
**Decision**: Continue using stdlib `urllib` instead of migrating to `requests`.
**Rationale**: No new external dependencies, code already works, multipart form handling is custom anyway.
**Alternatives considered**:
- requests → rejected: adds dependency, no significant DX improvement for this use case
- httpx → rejected: async-first, overkill for sync code

## Risks / Trade-offs

**[Risk] 100% coverage is ambitious for API code**
- Mitigation: Mock all API responses; keep integration tests separate; accept reasonable pragmatism (e.g., `if __name__ == "__main__"` blocks excluded)

**[Risk] Scheduled GitHub Actions fetches may accumulate data drift if they fail silently**
- Mitigation: Monitoring/alerting on workflow failures (separate from this change). Implement proper error handling and logging.

**[Risk] Pydantic validation may reject valid API responses if schemas change**
- Mitigation: Use `model.config.extra = "allow"` for flexibility. Add version detection in API clients.

**[Risk] Breaking existing workflows that import these modules**
- Mitigation: Current code is not importable anyway (in `src/` at root level). No users affected.

**[Trade-off] Click adds lightweight dependency**
- Impact: CLI will require Click. Application code (using API clients) won't need it.
- Acceptable: Click is stable, minimal footprint, worth it for UX.

## Migration Plan

1. **Phase 1**: Restructure code (copy scripts to `src/cordis_data/` modules)
2. **Phase 2**: Add tests (mocked, achieve 100%)
3. **Phase 3**: Add linting + type checking (fix violations)
4. **Phase 4**: Build `pyproject.toml`, add dependencies
5. **Phase 5**: Create GitHub Actions workflows
6. **Phase 6**: Configure Dependabot

Rollback: Revert to current script-based approach (both versions can coexist during transition).

## Open Questions

- Should we keep the existing `data/` directory in the repo, or document it as generated/external?
- What's the desired GitHub Actions schedule for `fetch_calls` and `fetch_projects`? (daily? weekly? both?)
- Should failed CORDIS enrichments ever retry, or mark permanently as "not available"?
- Who monitors scheduled fetch failures, and how are they alerted?
