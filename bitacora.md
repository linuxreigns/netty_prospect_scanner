# Bitácora - Netty Prospect Scanner

## 2026-05-10

### Cambios realizados
- Se creó la estructura completa del proyecto MVP.
- Se implementó backend FastAPI con rutas de escaneo, dashboard y exportación.
- Se implementó base SQLite con SQLAlchemy y deduplicación por dominio.
- Se implementó scanner HTTP con `httpx` + `BeautifulSoup`.
- Se implementó fallback Playwright para sitios JS.
- Se implementó detección de tecnologías por fingerprints (CMS/eCommerce/frontend).
- Se implementó detección de señales comerciales (chatbot, WhatsApp, contacto, redes, etc.).
- Se implementó motor de scoring Netty Fit Score y clasificación.
- Se implementó dashboard Streamlit con métricas, filtros, ranking y detalle.
- Se implementó exportación CSV, XLSX y PDF resumen.
- Se creó README con instalación y uso.

### Módulos creados
- `app/main.py`, `config.py`, `database.py`, `models.py`
- `app/scanner/*`
- `app/scoring/*`
- `app/ai/*`
- `app/exporters/*`
- `app/api/*`
- `dashboard/streamlit_app.py`

### Decisiones técnicas
- SQLite para MVP y `DATABASE_URL` configurable para migración a PostgreSQL.
- Detección por reglas/fingerprints para minimizar costo y complejidad.
- IA desacoplada del scraping (uso comercial únicamente).

### Errores encontrados
- Bug en filtros de dashboard al invocar función de ruta directamente en pruebas (`Query` de FastAPI usado como valor SQL).
- Corregido reemplazando defaults `Query(...)` por primitivos en la firma para compatibilidad en pruebas y ejecución normal vía API.

### Pendientes
- Endpoint de búsqueda/fuente externa por rubro/provincia (discovery futuro).
- Integración real con proveedor IA (OpenAI/DeepSeek).
- Hardenización de fingerprints por sitio panameño real.

### Actualización posterior (fase 2)
- Se agregó suite inicial de tests con `pytest`:
  - scoring
  - detector tecnológico/comercial
  - smoke tests API
- Se integró Alembic:
  - `alembic.ini`
  - `alembic/env.py` con soporte a `DATABASE_URL`
  - migración inicial `0001_create_prospects`
- README actualizado con comandos de migración y testing.

### Actualización posterior (fase 3)
- Se implementó módulo de descubrimiento enchufable:
  - `app/discovery/providers.py`
  - `app/discovery/service.py`
  - endpoint `GET /discovery/search`
  - catálogo local inicial `data/discovery_catalog.csv`
- Se implementó integración IA comercial real opcional (OpenAI/DeepSeek compatible):
  - `app/ai/commercial_analysis.py`
  - endpoint `GET /ai/prospect/{id}/analysis`
  - nuevas variables `.env`: `AI_BASE_URL`
- Se dockerizó el proyecto:
  - `Dockerfile.api`
  - `Dockerfile.dashboard`
  - `docker-compose.yml`
- README actualizado con uso de discovery, IA y Docker.
- Se agregó pipeline comercial de 1 paso:
  - endpoint `POST /pipeline/discover-scan-export`
  - flujo `discover -> scan -> score -> persist -> export hot leads`.
- Mejora pipeline:
  - modo async con `job_id` (`POST /pipeline/discover-scan-export/async`)
  - polling de estado (`GET /pipeline/jobs/{job_id}` y `GET /pipeline/jobs`)
  - export dual de hot leads: CSV + XLSX.
- Dashboard Streamlit mejorado con controles para ejecutar pipeline sync/async y consultar jobs.
- Corrección técnica:
  - reemplazo de `datetime.utcnow` por timestamps timezone-aware (`datetime.now(timezone.utc)`) en modelo `Prospect` para eliminar warnings deprecados.
- Gobernanza de agentes:
  - creación de `AGENTS.md` con reglas duras de scraping ético, calidad, seguridad, pruebas y documentación.
- Calidad y automatización:
  - configuración de `pre-commit` (`.pre-commit-config.yaml`)
  - configuración de herramientas en `pyproject.toml` (ruff/black/isort)
  - workflow CI en GitHub Actions (`.github/workflows/ci.yml`) con lint + format check + imports + compile + tests.
- Operación DX:
  - se agregó `Makefile` con comandos estándar (`check`, `test`, `lint`, `format`, `run-api`, `run-dashboard`, migraciones y compose).
  - se añadió `.gitignore` robusto.
  - se agregó `data/exports/.gitkeep` para versionar estructura sin archivos exportados.
  - se incluyó badge de CI en `README.md`.
- Security hardening aplicado:
  - mitigación SSRF en scanner (bloqueo localhost/loopback/redes privadas/link-local).
  - validación de ruta de CSV (`data/` + `.csv`) para evitar path traversal/LFI.
  - enforcement de HTTPS en `AI_BASE_URL` para proteger API keys.
  - límite/poda de jobs async en memoria para reducir riesgo de DoS lógico.
  - integración de secret scanning con `gitleaks` en:
    - pre-commit (`.pre-commit-config.yaml`)
    - CI GitHub Actions (`.github/workflows/ci.yml`)
    - configuración de allowlist en `.gitleaks.toml`.

### Hito de release
- Se creó `RELEASE.md` con checklist de salida a producción.
- Se creó `CHANGELOG.md` con versión inicial `v0.1.0` y resumen de capacidades MVP.
- Se reforzó la trazabilidad documental para preparar tag/release en repositorio.

### Documento de continuidad
- Se creó handoff detallado: `HANDOFF_2026-05-10.md`
  - incluye estado por módulo, seguridad, calidad/CI, riesgos abiertos y plan de siguiente sesión.
- Se formalizaron documentos estratégicos de NETTY SALES ENGINE:
  - `CORE_PRINCIPLES.md` (principios críticos, agentes obligatorios, límites MVP y prioridad absoluta).
  - `ROADMAP.md` (plan por etapas: estabilización pipeline → agentes → CRM operativo → 24/7).

### Avance Etapa 1 (estabilización pipeline)
- Se implementó persistencia de jobs async en DB:
  - nuevo modelo `PipelineJob` en `app/models.py`.
  - nueva migración Alembic `0002_create_pipeline_jobs.py`.
- Se refactorizó `routes_pipeline.py`:
  - estados normalizados: `queued|running|retry|done|error`.
  - trazabilidad por fase (`phase`) y timestamps (`created/started/finished/updated`).
  - métricas por job (`discovered/scanned/saved/hot_count`).
  - reintentos con backoff exponencial básico (máx. 3 intentos).
  - filtros de jobs por estado.
- Se actualizaron tests de pipeline y se añadió test de persistencia de `PipelineJob`.

### Avance Etapa 2 (agentes obligatorios)
- Se creó la capa explícita de agentes en `app/agents/`:
  - contratos/schemas (`base.py`, `schemas.py`)
  - implementaciones MVP de los 10 agentes obligatorios (`agents.py`)
  - orquestador (`orchestrator.py`) con ejecución secuencial y trazabilidad.
- Se añadió endpoint `POST /agents/run` en `app/api/routes_agents.py`.
- El flujo `/agents/run`:
  - ejecuta escaneo real base,
  - ejecuta cadena de 10 agentes,
  - retorna `agent_traces` auditables, score/clasificación, propuesta, outreach y follow-up.
- Se agregaron tests de integración para el flujo de agentes (`tests/test_agents.py`).

### Avance Etapa 2 (persistencia de trazas)
- Se añadió persistencia de ejecuciones de agentes:
  - modelo `AgentRun` (tabla `agent_runs`).
  - modelo `AgentTrace` (tabla `agent_traces`) vinculada por `run_id`.
- Se creó migración Alembic `0003_create_agent_runs_and_traces.py`.
- Se refactorizó `routes_agents.py`:
  - `POST /agents/run` ahora persiste run + 10 trazas de agentes.
  - nuevos endpoints:
    - `GET /agents/runs`
    - `GET /agents/runs/{id}`
- Se actualizaron tests de agentes para validar persistencia e historial.

### Avance Etapa 2 (trazabilidad cruzada)
- Se extendió `AgentRun` con enlaces cruzados:
  - `prospect_id` (FK a `prospects.id`)
  - `pipeline_job_id` (FK a `pipeline_jobs.job_id`)
- Se creó migración Alembic `0004_link_agent_runs_with_prospects_and_pipeline_jobs.py`.
- `POST /agents/run` ahora:
  - acepta `pipeline_job_id` opcional,
  - valida existencia de ese job,
  - vincula automáticamente `prospect_id` por coincidencia de dominio cuando existe.
- `GET /agents/runs` y `GET /agents/runs/{id}` devuelven referencias cruzadas.
- Se agregaron tests para campos nuevos y validación de `pipeline_job_id` inválido.

### Avance Etapa 2 (dashboard CRM por agentes)
- Se enriqueció `routes_dashboard.py` con analítica de actividad de agentes:
  - `GET /dashboard/agents/summary`
  - `GET /dashboard/agents/activity`
- Se añadió trazabilidad comercial en prospectos:
  - `latest_agent_run_id` en `GET /dashboard/prospects`
  - `latest_agent_run_id` en `GET /dashboard/prospects/{id}`
- Se agregaron tests de smoke/integación para analytics y enlaces prospecto↔agent_run.

### Avance Etapa 2 (cierre CRM operativo)
- Se fortaleció el dashboard API con enfoque CRM operativo:
  - `latest_agent_run_id` y `latest_agent_run_at` en prospectos.
  - nuevos filtros de priorización comercial:
    - `con_actividad_agentes`
    - `sin_run_reciente_horas`
    - `hot_sin_chatbot_con_whatsapp`
  - nueva vista consolidada por prospecto:
    - `GET /dashboard/prospects/{id}/commercial-view`
- Se mejoró Streamlit para mostrar:
  - actividad multiagente (summary + activity),
  - filtros CRM nuevos,
  - vista comercial consolidada.
- Se añadió guardrail de arquitectura para impedir reintroducir `create_all` en runtime.
- Se agregaron tests de integración para filtros/CRM view y guardrail.

### Avance Etapa 2 (trazabilidad pipeline + cola vendedor)
- Pipeline mejorado para trazabilidad completa:
  - `PipelineRequest` soporta `run_agents_for_hot`.
  - cuando está activo, ejecuta agentes para HOT leads y persiste `AgentRun/AgentTrace` enlazado al `pipeline_job_id` y `prospect_id`.
  - salida incluye `hot_agent_runs` con mapeo `prospect_id/domain/agent_run_id`.
- Nuevo endpoint comercial operativo:
  - `GET /dashboard/sales-queue`
  - entrega cola priorizada para vendedor (score, WhatsApp, sin chatbot, stale run).
- Nuevos tests para ambos componentes.

### Cierre formal — ETAPA 2 completada
- Se completó la orquestación explícita del núcleo comercial multiagente:
  - 10 agentes obligatorios operativos y orquestador activo.
  - persistencia de ejecuciones y trazas (`agent_runs`, `agent_traces`).
  - trazabilidad cruzada `agent_runs ↔ prospects ↔ pipeline_jobs`.
- Se completó el bloque CRM operativo:
  - analytics de agentes (`/dashboard/agents/summary`, `/dashboard/agents/activity`).
  - filtros CRM avanzados y vista comercial consolidada por prospecto.
  - cola operativa vendedor (`/dashboard/sales-queue`).
  - NBA por prospecto (`/dashboard/prospects/{id}/next-best-action`).
  - exportación de sales-queue CSV/XLSX.
- Streamlit actualizado como centro operativo con activity, queue, NBA y accesos de export.
- Guardrail arquitectónico activo para evitar `create_all` en runtime.

### Inicio ETAPA 3 (dashboard operativo)
- Se añadieron endpoints de operación comercial:
  - `GET /dashboard/funnel` (KPIs discover→load_ok→score→agent_run→hot→queue_ready).
  - `GET /dashboard/pipeline-aging` (no_run/stale_run/fresh_run + lista stale priorizada).
  - `GET /dashboard/hot-alerts` (alertas accionables basadas en HOT queue stale).
- Streamlit actualizado con paneles de embudo, aging y alertas HOT.
- Tests de smoke ampliados para validar shape de endpoints de Etapa 3.
- ROADMAP actualizado: Etapa 2 marcada completada y Etapa 3 en curso.

### Cierre de bloque — ETAPA 3 completa
- Se completó el dashboard operativo con enfoque 24/7:
  - embudo con conversiones (`/dashboard/funnel`),
  - pipeline por estados/fases (`/dashboard/pipeline-states`),
  - aging de oportunidades (`/dashboard/pipeline-aging`),
  - alertas HOT con severidad SLA 24/48/72 (`/dashboard/hot-alerts`).
- Streamlit actualizado para mostrar el bloque completo de operación comercial.
- Tests de smoke actualizados para validar shape y estabilidad de endpoints Etapa 3.
- ROADMAP actualizado con Etapa 3 marcada como completada.

### Cierre formal ETAPA 4 (automatización comercial controlada)
- Se completó el bloque comercial controlado con trazabilidad auditable end-to-end.
- Implementaciones cerradas:
  - plantillas por sector,
  - recomendador de plan transparente,
  - cola comercial persistida en DB,
  - auditoría de cambios de estado,
  - policy engine (`requires_manager_approval`),
  - aprobación individual y masiva por filtros,
  - simulación de dispatch sin envío real,
  - métricas SLA de cola en dashboard,
  - operación Streamlit para cola comercial (aprobación, bulk, auditoría, simulación).
- Seguridad operativa mantenida:
  - sin autoenvío,
  - políticas `manual_only`/`simulation_only`.
- Validación del cierre:
  - format/lint/tests en verde,
  - suite con cobertura ampliada de Etapa 4.

### Inicio ETAPA 5 (producción local 24/7)
- Se endureció `docker-compose.yml`:
  - `restart: unless-stopped` en API/dashboard,
  - healthcheck API (`/`) y dashboard (`/_stcore/health`),
  - `depends_on` del dashboard condicionado a API saludable.
- Se implementó backup/restore operativo base:
  - `scripts/backup_data.sh` (respaldo DB + exports + retención por `RETENTION_DAYS`).
  - `scripts/verify_restore.sh` (verificación de restore del backup más reciente).
  - objetivos Makefile: `make backup-data` y `make verify-restore`.
- Se implementó monitoreo básico local + alertas:
  - `scripts/monitor_services.sh` (chequeo API/dashboard/cola/pipeline con alertas en `data/monitor_alerts.log`).
  - `scripts/monitor_loop.sh` (ejecución periódica configurable por `INTERVAL_SECONDS`).
  - `scripts/systemd/netty-monitor.service` como plantilla de despliegue local 24/7.
  - objetivos Makefile: `make monitor-check` y `make monitor-loop`.
- Se añadieron tests de existencia/integración para scripts de backup y monitoreo.

### Avance ETAPA 5 — recuperación operativa
- Se creó `OPERATIONS_PLAYBOOK.md` con procedimientos de:
  - arranque estándar,
  - reinicio controlado,
  - backup/restore,
  - monitoreo,
  - incidentes comunes,
  - smoke test post-reinicio.
- Se creó `scripts/smoke_post_restart.sh` para validar API, dashboard, summary, pipeline async, cola comercial, exports y métricas SLA tras reinicio.
- Se agregó target Makefile `make smoke-post-restart`.
- Se añadió test de existencia/integración de playbook y smoke script.

### Remediación CVEs y actualización de dependencias — 2026-05-11
- Se ejecutó `pip-audit`: 17 CVEs encontrados en 7 paquetes.
- Se actualizaron todas las dependencias directas e indirectas a versiones más recientes:
  - fastapi: 0.116.1 → 0.136.1
  - uvicorn: 0.35.0 → 0.46.0
  - sqlalchemy: 2.0.42 → 2.0.49
  - pydantic: 2.11.7 → 2.13.4
  - pydantic-settings: 2.10.1 → 2.14.1
  - beautifulsoup4: 4.13.4 → 4.14.3
  - pandas: 2.3.1 → 3.0.2
  - streamlit: 1.48.0 → 1.57.0 (CVE-2026-33682 resuelto)
  - fpdf2: 2.8.3 → 2.8.7
  - playwright: 1.55.0 → 1.59.0
  - python-multipart: 0.0.20 → 0.0.28 (3 CVEs resueltos)
  - starlette: 0.47.3 → 1.0.0 (CVE-2025-62727 resuelto, vía upgrade de FastAPI)
  - pillow: 11.3.0 → 12.2.0 (6 CVEs resueltos)
  - pytest: 8.4.1 → 9.0.3 (CVE-2025-71176 resuelto)
  - black: 24.10.0 → 26.3.1 (CVE-2026-32274 resuelto)
  - ruff: 0.6.9 → 0.15.12
  - isort: 5.13.2 → 8.0.1
  - alembic: 1.16.4 → 1.18.4
  - pre-commit: 3.8.0 → 4.6.0
  - pip: 24.0 → 26.1.1 (4 CVEs resueltos)
- `requirements.txt` actualizado con versiones exactas instaladas.
- `make format` ejecutado para adaptar código al nuevo black 26.
- Validación final: `make check` verde (lint + format + tests).
- `pip-audit`: 0 CVEs conocidos.

### Auth básica en endpoints sensibles — 2026-05-11
- Se creó `app/auth.py` con dependencia `require_api_key` via header `X-API-Key`.
- Se agregó campo `api_key: str | None = None` a `app/config.py` (activado con env var `API_KEY`).
- Si `API_KEY` no está configurada, la auth se salta (modo dev compatible con entorno local).
- Routers protegidos en `app/main.py`: `/scan/*`, `/export/*`, `/pipeline/*`, `/agents/*`, `/commercial/*`, `/ai/*`.
- Routers públicos: `/` (health), `/dashboard/*`, `/discovery/*`.
- 5 tests de auth agregados en `tests/test_security.py`.
- Validación: `make check` verde, 39 tests passing.

### Cierre formal ETAPA 5 — monitoreo de recursos — 2026-05-11
- `scripts/monitor_services.sh` extendido con sección 5 (CPU / RAM / Disco):
  - Variables: `CPU_WARN_PCT`, `MEM_WARN_PCT`, `DISK_WARN_PCT` (default 85%), `DISK_PATH` (default `/`).
  - CPU: muestra `/proc/stat` con intervalo de 0.5 s.
  - RAM: `/proc/meminfo` (MemTotal - MemAvailable).
  - Disco: `shutil.disk_usage`.
  - Alerta MEDIUM cuando cualquier métrica supera umbral.
- Test agregado en `tests/test_monitoring_scripts.py`.
- ROADMAP: Etapa 5 marcada como completada.
- Validación: `make check` verde, 40 tests passing.

### Cierre formal ETAPA 6 — PostgreSQL, Redis, contratos API — 2026-05-11
- Drivers instalados: `psycopg2-binary==2.9.12`, `redis[hiredis]==7.4.0`.
- `docker-compose.yml` actualizado con:
  - Servicio `postgres:16-alpine` con volumen `postgres_data` y healthcheck `pg_isready`.
  - Servicio `redis:7-alpine` con volumen `redis_data` y healthcheck `redis-cli ping`.
  - API y dashboard: `DATABASE_URL` y `REDIS_URL` configurados en `environment` (override sobre `.env`).
  - Cadena de dependencias: `redis/db → api → dashboard`.
- `app/queue.py` creado:
  - `init_redis()` / `close_redis()` / `is_available()`.
  - `enqueue_pipeline_job(job_id)` — push a Redis list; retorna False si no hay Redis.
  - `start_consumer(fn)` — consumer async con `blpop`, cancellable en shutdown.
- `app/api/routes_pipeline.py`: endpoint async usa Redis si disponible, BackgroundTasks como fallback.
- `app/main.py`:
  - Lifespan (`asynccontextmanager`) gestiona init/close de Redis y arranque del consumer.
  - `FastAPI(version="1.0.0", description=...)`.
  - Nuevo endpoint `GET /api/info`: versión, backend de queue/DB, auth activo, mapa de endpoints.
  - `GET /` incluye `version` en respuesta.
- Tests: 41 passing (1 nuevo para `/api/info`).
- `make check` verde.

### Próximos pasos
1. Corregir badge CI en README (reemplazar `OWNER/REPO` con repo real).
2. Conectar repo a GitHub y activar branch protection.
3. Ampliar Discovery con proveedor web real (fuera de catálogo local).
