## ADDED Requirements

### Requirement: Code style enforcement with flake8
The project SHALL use flake8 for code style checking, with violations flagged in CI/CD.

#### Scenario: flake8 runs on every push
- **WHEN** code is pushed to the repository
- **THEN** CI/CD executes flake8 against `src/` and `tests/`

#### Scenario: flake8 violations fail the build
- **WHEN** flake8 detects style violations (e.g., line too long, unused imports)
- **THEN** the CI job fails and blocks merging

#### Scenario: Configuration is explicit
- **WHEN** developers examine the project
- **THEN** flake8 configuration is defined in `pyproject.toml` (or `.flake8`) with clear line-length, ignore rules, etc.

### Requirement: Type checking with pyright
The project SHALL use Pyright for static type checking, with violations flagged in CI/CD.

#### Scenario: pyright runs on every push
- **WHEN** code is pushed to the repository
- **THEN** CI/CD executes pyright against `src/` and `tests/`

#### Scenario: Type errors fail the build
- **WHEN** pyright detects type violations (e.g., incompatible function arguments, missing type hints)
- **THEN** the CI job fails and blocks merging

#### Scenario: Type hints are enforced
- **WHEN** functions in `src/cordis_data/` are defined
- **THEN** they have type hints for arguments and return values

#### Scenario: Pyright configuration is strict
- **WHEN** pyright runs
- **THEN** it uses strict mode (or equivalent) to catch more errors

### Requirement: GitHub Actions lint workflow
A dedicated CI workflow SHALL run flake8 and pyright on every push and pull request.

#### Scenario: Lint workflow runs independently
- **WHEN** code is pushed
- **THEN** the lint workflow runs in parallel with the test workflow

#### Scenario: Workflow results are visible
- **WHEN** a PR is opened
- **THEN** lint job status (pass/fail) is visible on the PR

### Requirement: Linting is local-reproducible
Developers SHALL be able to reproduce lint checks locally before pushing.

#### Scenario: Developer can run flake8 locally
- **WHEN** `flake8 src/ tests/` is run locally
- **THEN** it produces identical results to CI

#### Scenario: Developer can run pyright locally
- **WHEN** `pyright` is run locally
- **THEN** it produces identical results to CI
