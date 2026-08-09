## ADDED Requirements

### Requirement: Comprehensive test suite with 100% coverage
The project SHALL have a test suite using pytest that achieves 100% code coverage for `src/cordis_data/` (excluding `__main__` blocks and CLI-specific code).

#### Scenario: Tests can be run locally
- **WHEN** developer runs `pytest` from project root
- **THEN** all tests pass and coverage report is generated

#### Scenario: Coverage is measured and enforced
- **WHEN** coverage report is generated
- **THEN** it shows 100% coverage for `src/cordis_data/` modules (api, data, models, utils, config)

### Requirement: Unit tests for API clients
API clients (`SediaClient`, `CordisClient`) SHALL have unit tests that mock HTTP responses and validate request/response handling without making real network calls.

#### Scenario: SEDIA client retry logic is tested
- **WHEN** a test simulates a failed HTTP request
- **THEN** the client retries the configured number of times before giving up

#### Scenario: Rate limiter is tested
- **WHEN** a test simulates rapid requests to CORDIS
- **THEN** the TokenBucket rate limiter enforces the 2 req/second limit

#### Scenario: API error responses are parsed correctly
- **WHEN** the API returns an error (429, 500, 404)
- **THEN** the client handles it appropriately (retry vs. give up)

### Requirement: Unit tests for data models
Pydantic models (`Call`, `Project`) SHALL have unit tests validating schema enforcement and validation.

#### Scenario: Model rejects invalid data
- **WHEN** a Call object is instantiated with missing required fields
- **THEN** Pydantic raises a validation error

#### Scenario: Model serializes correctly
- **WHEN** a Call model is serialized to JSON
- **THEN** the output matches the expected schema

### Requirement: Unit tests for business logic
Data transformation and merge logic SHALL have unit tests.

#### Scenario: Calls are merged correctly by reference
- **WHEN** existing and new calls are merged
- **THEN** records with the same reference are updated, new records are added, unchanged records remain

#### Scenario: Budget extraction handles edge cases
- **WHEN** budget data is extracted from malformed or missing fields
- **THEN** None values are returned gracefully (not errors)

### Requirement: Test fixtures for API responses
Real API response samples SHALL be stored as JSON fixtures and used by mocked tests.

#### Scenario: Fixtures are realistic
- **WHEN** tests run with mocked API responses
- **THEN** the fixtures are actual SEDIA/CORDIS responses (or close equivalents)

### Requirement: Tests are organized by type
Tests SHALL be organized into `tests/unit/` and `tests/integration/` directories with clear naming.

#### Scenario: Unit tests don't require external services
- **WHEN** unit tests run
- **THEN** no external services (APIs, databases, files) are accessed

### Requirement: Conftest provides shared fixtures
Common test fixtures (mock API clients, temporary directories, sample data) SHALL be defined in `tests/conftest.py` for reuse across tests.

#### Scenario: Tests use reusable fixtures
- **WHEN** multiple tests need a mocked SediaClient
- **THEN** they all use a single `sedia_client` fixture from conftest
