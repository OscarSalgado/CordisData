## ADDED Requirements

### Requirement: Project is installable Python package
The project SHALL be structured as an installable Python package with `src/cordis_data/` as the package root, with clear separation of concerns across modules and subpackages.

#### Scenario: Package can be installed from local source
- **WHEN** `pip install -e .` is run in the project root
- **THEN** the `cordis_data` package is available for import system-wide

#### Scenario: Package exports public API
- **WHEN** code imports `from cordis_data.api import SediaClient, CordisClient`
- **THEN** the classes are available without errors

#### Scenario: Modules are logically organized
- **WHEN** exploring the package structure
- **THEN** it contains subpackages: `api/` (HTTP clients), `data/` (fetchers), and modules: `models.py` (data schemas), `cli.py` (CLI commands), `config.py` (configuration)

### Requirement: src/ layout prevents accidental local imports
The package SHALL use the `src/` layout to prevent Python from importing the local development directory before the installed package.

#### Scenario: Local package does not shadow installed version
- **WHEN** the installed package is updated and code is re-run
- **THEN** the new installed version is used, not the local directory

### Requirement: __init__ modules provide public exports
Each package and subpackage SHALL have an `__init__.py` that explicitly exports the public API.

#### Scenario: CLI imports top-level module without knowing internal structure
- **WHEN** `cli.py` imports required utilities
- **THEN** it uses short, clean imports like `from cordis_data.api import SediaClient` rather than `from cordis_data.api.sedia import SediaClient`

### Requirement: Configuration is centralized
The package SHALL have a `config.py` module that defines all runtime configuration (API endpoints, rate limits, TTLs, etc.) as importable constants or a configuration class.

#### Scenario: Fetchers read configuration
- **WHEN** a fetcher is instantiated
- **THEN** it reads configuration like `API_RATE_LIMIT`, `CORDIS_TTL_DAYS` from `cordis_data.config`

### Requirement: Utility functions are shared
Common utility functions (date normalization, budget extraction, etc.) that are used by multiple modules SHALL be collected in `utils.py`.

#### Scenario: Date normalization is reusable
- **WHEN** multiple modules need to normalize dates
- **THEN** they call `from cordis_data.utils import normalize_date` instead of duplicating logic
