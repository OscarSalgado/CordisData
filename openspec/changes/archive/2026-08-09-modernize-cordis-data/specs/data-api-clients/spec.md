## ADDED Requirements

### Requirement: Reusable SEDIA API client
A `SediaClient` class SHALL be provided in `cordis_data.api` that encapsulates all SEDIA API communication and can be imported and used by external projects.

#### Scenario: External project imports SediaClient
- **WHEN** external code runs `from cordis_data.api import SediaClient`
- **THEN** the class is available and can be instantiated with `client = SediaClient(api_key="...")`

#### Scenario: Client abstracts multipart form handling
- **WHEN** code uses `SediaClient.search(...)`
- **THEN** the client handles multipart form-data encoding internally; caller just passes structured arguments

#### Scenario: Client enforces rate limiting
- **WHEN** multiple calls are made to SEDIA API
- **THEN** the client respects API rate limits and never exceeds them

#### Scenario: Client handles retries
- **WHEN** a request fails transiently (timeout, 5xx)
- **THEN** the client retries automatically with exponential backoff

### Requirement: Reusable CORDIS API client
A `CordisClient` class SHALL be provided in `cordis_data.api` for CORDIS API access.

#### Scenario: External project imports CordisClient
- **WHEN** external code runs `from cordis_data.api import CordisClient`
- **THEN** the class is available and can be instantiated with `client = CordisClient()`

#### Scenario: Client respects CORDIS rate limits
- **WHEN** CordisClient makes requests
- **THEN** it uses a shared TokenBucket to enforce max 2 requests/second

#### Scenario: Client handles 404 gracefully
- **WHEN** a project ID doesn't exist in CORDIS
- **THEN** the client returns None instead of raising an error

### Requirement: Pydantic data models are public
Pydantic models (`Call`, `Project`) SHALL be exported from `cordis_data.models` and usable by external code.

#### Scenario: External project imports Call model
- **WHEN** external code runs `from cordis_data.models import Call`
- **THEN** the model is available and can be used for validation/serialization

#### Scenario: Models validate input
- **WHEN** external code instantiates a `Call` with invalid data
- **THEN** Pydantic raises a clear validation error

#### Scenario: Models serialize to JSON
- **WHEN** a `Call` or `Project` model is serialized with `.model_dump_json()`
- **THEN** valid JSON output is produced

### Requirement: API clients are testable with dependency injection
API clients and fetchers SHALL accept dependencies as constructor arguments (e.g., session, rate limiter) for easy testing.

#### Scenario: CORDIS client can use a mock rate limiter
- **WHEN** a test passes a mock TokenBucket to CordisClient
- **THEN** the client uses the mock instead of creating its own

#### Scenario: Fetcher accepts injected client
- **WHEN** a test instantiates CallsFetcher with a mock SediaClient
- **THEN** the fetcher uses the mock for API calls

### Requirement: Configuration constants are public
Rate limits, API endpoints, TTLs, and other constants SHALL be importable from `cordis_data.config`.

#### Scenario: Code imports rate limit constants
- **WHEN** external code runs `from cordis_data.config import CORDIS_RATE_LIMIT`
- **THEN** the constant is available and can be used

### Requirement: Utilities are reusable
Utility functions (date normalization, budget parsing, etc.) SHALL be public in `cordis_data.utils`.

#### Scenario: External code imports utility functions
- **WHEN** external code runs `from cordis_data.utils import normalize_date`
- **THEN** the function is available and well-documented
