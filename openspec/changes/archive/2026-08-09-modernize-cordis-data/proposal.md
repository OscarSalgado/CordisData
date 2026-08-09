## Why

CordisData actualmente son dos scripts Python sueltos sin estructura de proyecto, testing, o automatización. Para escalar y reutilizar este código en múltiples aplicaciones de forma confiable, necesita ser un módulo Python moderno con tests 100%, linting automático, y actualizaciones de dependencias gestionadas. Esto habilita consumo seguro en otros proyectos y mantenimiento a largo plazo.

## What Changes

- **Restructured as installable Python module**: `cordis_data` con capas API, Data, Models
- **CLI interface**: Comandos `cordis-data fetch-calls`, `cordis-data fetch-projects`, `cordis-data status`
- **Full test coverage (100%)**: pytest con fixtures, unit + integration tests
- **Automated linting**: flake8 + pyright en CI/CD
- **Dependency management**: Dependabot para Python deps y GitHub Actions
- **Modern Python**: Python 3.12+ (última versión estable)
- **GitHub Actions workflows**: Scheduled fetches, test + lint gates, auto-updates

## Capabilities

### New Capabilities

- `python-module-structure`: Proyecto reorganizado como paquete Python instalable (`src/cordis_data/`) con arquitectura en capas (api, data, models, cli) para reutilización en múltiples aplicaciones.

- `cli-interface`: Interfaz de línea de comandos con comandos `fetch-calls`, `fetch-projects`, `status` permitiendo uso desde terminal o GitHub Actions.

- `testing-framework`: Suite completa de tests pytest con 100% coverage, fixtures reutilizables, tests unitarios (API clients, models, lógica) e integración.

- `automated-linting`: Pipeline CI/CD con flake8 (code style) + pyright (type checking) ejecutándose en cada push.

- `dependency-management`: Configuración Dependabot para monitorear y auto-actualizar dependencias Python y GitHub Actions (scope completo del proyecto).

- `data-api-clients`: Clientes API reutilizables para SEDIA y CORDIS (`cordis_data.api.SediaClient`, `cordis_data.api.CordisClient`) que otros proyectos pueden importar.

### Modified Capabilities

(No existing capabilities; this is a restructuring of existing code)

## Impact

- **Code organization**: Dos scripts en `src/` se reorganizan en `src/cordis_data/` con módulos temáticos (api/, data/, models/)
- **Entry points**: Scripts se reemplazan con CLI configurado en `pyproject.toml`
- **Dependencies**: Introduce `pyproject.toml` con dev-dependencies (pytest, flake8, pyright)
- **CI/CD**: Nuevo directorio `.github/workflows/` con test, lint, y scheduled fetch jobs
- **Reutilización**: Otros proyectos pueden ahora hacer `from cordis_data.api import SediaClient` o `from cordis_data.models import Call`
- **Data storage**: Permanece en `data/`, consumible por aplicaciones externas
