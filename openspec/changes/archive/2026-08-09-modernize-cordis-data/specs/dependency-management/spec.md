## ADDED Requirements

### Requirement: Dependencies declared in pyproject.toml
All project dependencies (runtime and development) SHALL be declared in `pyproject.toml` following PEP 517/518 standards.

#### Scenario: Project has a pyproject.toml
- **WHEN** examining the project root
- **THEN** a valid `pyproject.toml` file exists with `[project]` and `[project.optional-dependencies]` sections

#### Scenario: Runtime dependencies are minimal
- **WHEN** examining `pyproject.toml`
- **THEN** runtime dependencies are listed (e.g., Click for CLI, Pydantic for models); no unnecessary libraries

#### Scenario: Dev dependencies are clearly separated
- **WHEN** examining `pyproject.toml`
- **WHEN** dev dependencies (pytest, flake8, pyright, pytest-cov) are listed under `[project.optional-dependencies.dev]`
- **THEN** they are not installed for end users

### Requirement: Python version constraint
The project SHALL specify Python 3.12 as the minimum version in `pyproject.toml`.

#### Scenario: Requires statement is explicit
- **WHEN** examining `pyproject.toml`
- **THEN** the `requires-python` field is set to `">=3.12"`

### Requirement: Dependabot monitors Python dependencies
Dependabot SHALL be configured to automatically check for updates to Python dependencies (main and dev) and create pull requests.

#### Scenario: Dependabot configuration exists
- **WHEN** examining `.github/dependabot.yml`
- **THEN** it includes a configuration block for `pip` package manager

#### Scenario: Dependabot creates PRs for updates
- **WHEN** a dependency release is published to PyPI
- **THEN** Dependabot creates a PR with the update within 24 hours

#### Scenario: Dependabot respects grouping
- **WHEN** examining Dependabot configuration
- **THEN** dependencies are grouped (e.g., dev dependencies together) to reduce PR noise

### Requirement: Dependabot monitors GitHub Actions
Dependabot SHALL be configured to monitor GitHub Actions workflow dependencies and create PRs for updates.

#### Scenario: Dependabot configuration includes GitHub Actions
- **WHEN** examining `.github/dependabot.yml`
- **THEN** it includes a configuration block for `github-actions`

#### Scenario: Dependabot updates workflow actions
- **WHEN** an action (e.g., `actions/setup-python@v4` → `v5`) is released
- **THEN** Dependabot creates a PR with the update

### Requirement: Dependabot PRs pass CI
All Dependabot-created PRs SHALL pass tests and linting before being mergeable.

#### Scenario: PR from Dependabot runs full CI
- **WHEN** Dependabot creates a PR
- **THEN** all workflows (test, lint) run and must pass

### Requirement: Lock file strategy is defined
The project SHALL clarify its lock file strategy (requirements.lock, poetry.lock, etc.) or confirm none is used.

#### Scenario: Lock file strategy is documented
- **WHEN** examining project documentation
- **THEN** it explains how dependencies are pinned (or not pinned)
