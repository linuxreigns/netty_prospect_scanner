# Changelog

## [1.1.0] - 2026-05-11

### Added
- Auth `X-API-Key` en endpoints sensibles (`/scan`, `/pipeline`, `/export`, `/agents`, `/commercial`, `/ai`). Sin configuración activa en modo dev (compatible hacia atrás).
- Monitoreo de recursos del sistema en `scripts/monitor_services.sh`: CPU, RAM y disco con umbrales configurables (`CPU_WARN_PCT`, `MEM_WARN_PCT`, `DISK_WARN_PCT`).
- Soporte PostgreSQL productivo: driver `psycopg2-binary`, servicio `postgres:16-alpine` en docker-compose.
- Cola Redis: driver `redis[hiredis]`, servicio `redis:7-alpine` en docker-compose, `app/queue.py` con fallback transparente a BackgroundTasks.
- Endpoint `GET /api/info` con versión, backend activo y mapa de endpoints.
- `FastAPI(version="1.0.0")` + versión expuesta en `GET /`.
- Lifespan (`asynccontextmanager`) para inicialización/cierre de Redis y consumer de pipeline.

### Changed
- Todas las dependencias actualizadas a versiones más recientes (17 CVEs eliminados).
- Etapas 5 y 6 del ROADMAP completadas.

### Fixed
- `pip`, `python-multipart`, `starlette`, `pillow`, `streamlit`, `black`, `pytest` — CVEs resueltos vía upgrade.

Todas las modificaciones relevantes de este proyecto se documentan en este archivo.

El formato está inspirado en Keep a Changelog y versionado semántico (SemVer).

## [0.1.0] - 2026-05-10

### Added
- MVP completo de **Netty Prospect Scanner**:
  - Backend FastAPI con rutas de scan, dashboard, export, discovery, IA y pipeline.
  - Scanner ético con `httpx` + `BeautifulSoup` y fallback Playwright.
  - Detección tecnológica por fingerprints (CMS/eCommerce/frontend).
  - Detección de señales comerciales (chatbot, WhatsApp, formulario, contacto, redes, etc.).
  - Motor de scoring `Netty Fit Score` + clasificación (Caliente/Bueno/Medio/Bajo).
  - Persistencia SQLite con modelo `Prospect` y deduplicación por dominio.
  - Exportaciones CSV/XLSX/PDF y listas comerciales.
  - Dashboard Streamlit con métricas, filtros, ranking y detalle.
  - Discovery enchufable (`LocalCatalogProvider`, `NullWebProvider`) con endpoint `/discovery/search`.
  - IA comercial opcional compatible OpenAI/DeepSeek en `/ai/prospect/{id}/analysis`.
  - Pipeline comercial sync/async con `job_id`, polling y export dual CSV/XLSX.

- Calidad y operación:
  - Suite de tests con `pytest`.
  - Migraciones Alembic (`0001_create_prospects`).
  - Dockerfiles + docker-compose.
  - Pre-commit (ruff, black, isort, pytest pre-push).
  - CI GitHub Actions con lint + format checks + compile + tests.
  - Makefile con comandos operativos.
  - Reglas duras en `AGENTS.md`.
  - Checklist de release en `RELEASE.md`.

### Fixed
- Corrección de filtros dashboard para compatibilidad en ejecución/pruebas.
- Corrección de timestamps a formato timezone-aware (UTC).
- Ajustes de lint/estilo para pipeline de calidad automatizado.
