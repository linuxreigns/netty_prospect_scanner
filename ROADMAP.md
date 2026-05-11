# ROADMAP.md — NETTY SALES ENGINE

## Enfoque
Roadmap por etapas con prioridad en estabilidad operativa, modularidad y trazabilidad.

---

## ETAPA 0 — Base estable (completada)
- API FastAPI modular.
- Scanner + detector + scoring.
- Dashboard Streamlit.
- Export CSV/XLSX/PDF.
- Pipeline sync/async con `job_id`.
- Seguridad base (SSRF guard, CSV path, HTTPS IA).
- Calidad/CI/pre-commit/gitleaks.

Estado: ✅ Completada

---

## ETAPA 1 — Estabilización de pipeline (prioridad inmediata)

### Objetivo
Garantizar operación predecible 24/7 en entorno local (DEV Lenovo LOQ y mini desktop Debian).

### Entregables
1. **Persistencia de jobs** de pipeline (DB o Redis) en vez de memoria temporal.
2. **Reintentos controlados** para tareas fallidas (backoff, máximo intentos).
3. **Estados de job normalizados** (`queued/running/done/error/retry`).
4. **Trazabilidad extendida** por `job_id` (timestamps completos y métricas por fase).
5. **Control de concurrencia por worker** para evitar saturación.

### Criterio de salida
- 24h de ejecución continua sin fallas críticas.
- Jobs trazables y recuperables tras reinicio de servicio.

Estado: 🔄 En curso (avance aplicado: persistencia de jobs + estados normalizados + retries básicos)

---

## ETAPA 2 — Agentes obligatorios MVP (núcleo comercial)

Estado: ✅ Completada (10 agentes explícitos + orquestador + endpoint `/agents/run` + persistencia `agent_runs/agent_traces` + trazabilidad cruzada con `prospects/pipeline_jobs` + dashboard CRM operativo con analytics, sales-queue y NBA).

### Objetivo
Implementar explícitamente los 10 agentes obligatorios como servicios/módulos desacoplados.

### Entregables por agente
1. **Prospect Discovery Agent**: queries dinámicas DuckDuckGo + deduplicación.
2. **Panama Validation Agent**: score de pertenencia Panamá por señales locales.
3. **Technology Fingerprint Agent**: robustecer fingerprints y evidencias.
4. **Website Audit Agent**: checklists de oportunidad por sector.
5. **Commercial Qualification Agent**: Netty Fit Score v2 + razones interpretables.
6. **Netty Solution Architect Agent**: recomendaciones por rubro/caso.
7. **Proposal Generator Agent**: auditoría+pitch+email con narrativa meta-demostración.
8. **Outreach Agent**: secuencias preparadas con aprobación humana.
9. **Follow-Up Agent**: recordatorios y políticas de recontacto.
10. **CRM Intelligence Agent**: estados pipeline y métricas comerciales.

### Criterio de salida
- Cada agente tiene input/output definido y logs auditables.
- Flujo end-to-end funciona con datos reales.

Estado: ✅ Completada

---

## ETAPA 3 — CRM operativo y dashboard de mando

### Objetivo
Convertir dashboard en centro operativo comercial autónomo.

### Entregables
- Pipeline visual por estados.
- Alertas HOT y aging de oportunidades.
- KPIs de embudo (discover→scan→score→outreach→follow-up).
- Vista de actividad reciente por agente.
- Evidencia clara de “analizado por ecosistema Netty”.

### Avance aplicado (cierre de bloque Etapa 3)
- Endpoints operativos implementados:
  - `GET /dashboard/funnel` (KPIs + conversiones entre etapas)
  - `GET /dashboard/pipeline-states` (estados/fases de jobs de pipeline)
  - `GET /dashboard/pipeline-aging` (no_run/stale_run/fresh_run)
  - `GET /dashboard/hot-alerts` (severidad SLA 24/48/72)
- Dashboard Streamlit actualizado como centro operativo con:
  - embudo + conversiones,
  - pipeline por estados,
  - aging,
  - alertas HOT con severidad.
- Tests de smoke ampliados para validar endpoints y shape del bloque Etapa 3.

Estado: ✅ Completada

---

## ETAPA 4 — Automatización comercial controlada

### Objetivo
Escalar productividad sin comprometer seguridad/compliance.

### Entregables
- Plantillas por sector para outreach/follow-up.
- Recomendador de plan (Starter/Pro/Business) con reglas transparentes.
- Cola Redis para procesamiento desacoplado.
- Políticas de aprobación manual previas al envío.

### Avance aplicado (Etapa 4)
- Plantillas sectoriales implementadas en `app/commercial/templates.py`.
- Recomendador de plan transparente implementado en `app/commercial/plan_recommender.py`.
- Policy engine de aprobación implementado en `app/commercial/policy_engine.py`.
- Cola comercial desacoplada persistida en DB + auditoría:
  - `commercial_queue_items`
  - `commercial_queue_audit_events`
- API comercial:
  - `GET /commercial/templates/{sector}`
  - `GET /commercial/prospects/{id}/plan`
  - `POST /commercial/queue`
  - `GET /commercial/queue`
  - `POST /commercial/queue/{item_id}/approval`
  - `POST /commercial/queue/bulk-approval`
  - `POST /commercial/queue/{id}/simulate-dispatch`
  - `GET /commercial/queue/audit`
- Dashboard operativo agrega métricas SLA de cola:
  - `GET /dashboard/commercial/queue-metrics`
- Despacho mantiene política controlada: `manual_only` y `simulation_only`, sin envío real.

Estado: ✅ Completada

### Criterio de cierre alcanzado
- Productividad comercial controlada con aprobación manual y trazabilidad auditable.
- Cola comercial persistida en DB con operación individual y masiva.
- Policy engine activo para control de aprobaciones sensibles.
- Simulación de dispatch sin envío real.
- Métricas SLA operativas disponibles en dashboard.
- Tests de regresión de Etapa 4 en verde.

---

## ETAPA 5 — Producción local 24/7

### Objetivo
Operación continua en mini desktop Debian local.

### Entregables
- Docker Compose endurecido (healthchecks, restart policies, volúmenes persistentes).
- Backups automáticos DB + exports.
- Monitoreo básico de procesos y alertas de caída.
- Playbooks de recuperación.

### Avance aplicado (Etapa 5)
- `docker-compose.yml` endurecido con:
  - `restart: unless-stopped` en API y dashboard,
  - `healthcheck` para API (`/`) y dashboard (`/_stcore/health`),
  - dependencia por salud (`depends_on.condition: service_healthy`) para dashboard.
- Backups automáticos base implementados:
  - script `scripts/backup_data.sh` para DB + exports,
  - retención por días (`RETENTION_DAYS`, default 14),
  - script `scripts/verify_restore.sh` para validar restore de últimos backups,
  - objetivos operativos en Makefile (`backup-data`, `verify-restore`).
- Monitoreo básico local + alertas implementado:
  - script `scripts/monitor_services.sh` (health API/dashboard + métricas cola/pipeline + alertas),
  - script `scripts/monitor_loop.sh` para ejecución periódica,
  - servicio systemd de referencia `scripts/systemd/netty-monitor.service`,
  - objetivos operativos en Makefile (`monitor-check`, `monitor-loop`).
- Playbook de recuperación y smoke post-reinicio implementados:
  - `OPERATIONS_PLAYBOOK.md`,
  - `scripts/smoke_post_restart.sh`,
  - objetivo Makefile `smoke-post-restart`.

### Avance final Etapa 5 — monitoreo de recursos
- `scripts/monitor_services.sh` extendido con sección 5: CPU / RAM / Disco.
- Variables configurables: `CPU_WARN_PCT`, `MEM_WARN_PCT`, `DISK_WARN_PCT` (default 85%), `DISK_PATH` (default `/`).
- Lectura via `/proc/stat` (CPU con muestra de 0.5 s), `/proc/meminfo` y `shutil.disk_usage`.
- Alerta MEDIUM cuando cualquier métrica supera su umbral.
- Test de existencia y contenido en `tests/test_monitoring_scripts.py`.

Estado: ✅ Completada

---

## ETAPA 6 — Preparación de evolución (post-MVP)

### Objetivo
Dejar camino listo para escalar sin rehacer núcleo.

### Entregables
- PostgreSQL como default productivo (SQLite fallback).
- Redis como queue principal.
- Contratos API estables para futura UI Next.js.
- Plan de versionado y migración incremental.

### Entregables implementados
- **PostgreSQL**: driver `psycopg2-binary` instalado; servicio `postgres:16-alpine` con volumen persistente en docker-compose; `DATABASE_URL` sobrescrita en entorno Docker; Alembic compatible sin cambios adicionales.
- **Redis**: cliente `redis[hiredis]` instalado; servicio `redis:7-alpine` con volumen persistente en docker-compose; `app/queue.py` con `enqueue_pipeline_job` y consumer async; fallback transparente a `BackgroundTasks` cuando `REDIS_URL` no está configurado.
- **Contratos API estables**: `FastAPI(version="1.0.0")` + endpoint `GET /api/info` con versión, backend activo y mapa de endpoints.
- **Versionado**: versión `1.0.0` expuesta en health (`GET /`) y OpenAPI auto-generado en `/docs`.

Estado: ✅ Completada

---

## Riesgos actuales priorizados
1. CVEs en dependencias (pendiente remediación por lotes).
2. Falta de auth/rate-limits para endpoints sensibles.
3. Operación 24/7 aún sin hardening completo de procesos/healthchecks/backups.

---

## Checklist de entrada — ETAPA 5 (producción local 24/7)
1. Docker Compose con healthchecks y restart policies para API/Dashboard.
2. Backups automáticos de DB y `data/exports/` con retención.
3. Monitoreo de procesos (latido API, consumo recursos, cola pendiente) + alertas locales.
4. Playbook de recuperación (reinicio, rollback migraciones, restauración backup).
5. Smoke test post-reinicio (API, dashboard, pipeline async, cola comercial, exports).
