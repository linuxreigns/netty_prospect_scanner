# Netty Prospect Scanner (MVP)

[![CI](https://github.com/linuxreigns/netty_prospect_scanner/actions/workflows/ci.yml/badge.svg)](https://github.com/linuxreigns/netty_prospect_scanner/actions/workflows/ci.yml)

Herramienta interna para prospectar negocios en Panamá, detectar stack tecnológico y priorizar leads B2B para Netty.

## Stack MVP
- Backend: FastAPI (Python)
- Base de datos: SQLite (migrable a PostgreSQL vía `DATABASE_URL`)
- Scanner: `httpx` + `BeautifulSoup`
- Fallback JS: Playwright
- Dashboard: Streamlit
- Exportación: CSV, XLSX, PDF resumen

## Estructura
```text
netty-prospect-scanner/
├── app/
├── dashboard/
├── data/
├── tests/
├── requirements.txt
├── .env.example
├── README.md
└── bitacora.md
```

## Instalación
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install
```

## Ejecutar API
```bash
uvicorn app.main:app --reload
```

## Ejecutar dashboard
```bash
streamlit run dashboard/streamlit_app.py
```

## Atajos con Makefile
```bash
make install
make check
make test
make lint
make format
make run-api
make run-dashboard
```

## Migraciones (Alembic)
```bash
# usar DATABASE_URL del entorno o alembic.ini
alembic upgrade head
alembic downgrade -1
```

## Tests
```bash
pytest
```

## Calidad de código (pre-commit)
```bash
pre-commit install
pre-commit run --all-files
```

Hooks configurados:
- ruff (lint + autofix)
- ruff-format
- black
- isort
- gitleaks (secret scanning)
- pytest (en pre-push)

## Docker
```bash
cp .env.example .env
docker compose up --build
```

## CI (GitHub Actions)
Workflow: `.github/workflows/ci.yml`

Valida automáticamente en push/PR:
- lint (ruff)
- formato (black)
- orden de imports (isort)
- secret scanning (gitleaks)
- compilación (`compileall`)
- tests (`pytest`)

Servicios:
- API: http://localhost:8000
- Dashboard: http://localhost:8501

## Flujo MVP
1. Cargar URLs por CSV (`url,rubro,provincia`) en `data/input_urls.csv`.
2. (Opcional) Descubrir por rubro/provincia desde catálogo local enchufable:
   - `GET /discovery/search?rubro=restaurantes&provincia=Panamá&limit=50`
3. Ejecutar escaneo:
   - `POST /scan/csv` con `{ "csv_path": "data/input_urls.csv" }`
   - o `POST /scan/urls` con lista directa.
4. Consultar dashboard:
   - `GET /dashboard/summary`
   - `GET /dashboard/prospects` con filtros.
5. Exportar:
   - `GET /export/csv`
   - `GET /export/xlsx`
   - `GET /export/pdf-summary`
   - `GET /export/hot-leads`, `/sales-list`, `/whatsapp-campaign`, `/email-campaign`
6. IA comercial (opcional):
   - `GET /ai/prospect/{id}/analysis`
7. Orquestación de agentes (Etapa 2):
   - `POST /agents/run`
   - ejecuta cadena explícita de 10 agentes obligatorios con trazabilidad (`agent_traces`).
   - persiste ejecución y trazas en DB (`agent_runs`, `agent_traces`).
   - trazabilidad cruzada: `agent_runs` se vincula a `prospects` y opcionalmente a `pipeline_jobs`.
   - consulta de historial: `GET /agents/runs` y `GET /agents/runs/{id}`.
8. Dashboard CRM (Etapa 2):
   - analytics de agentes: `GET /dashboard/agents/summary` y `GET /dashboard/agents/activity`.
   - prospectos enriquecidos con `latest_agent_run_id` y `latest_agent_run_at` para trazabilidad comercial.
   - filtros CRM adicionales en `/dashboard/prospects`:
     - `con_actividad_agentes=true`
     - `sin_run_reciente_horas=<n>`
     - `hot_sin_chatbot_con_whatsapp=true`
   - vista consolidada comercial por prospecto:
     - `GET /dashboard/prospects/{id}/commercial-view`
9. Pipeline operativo 1-paso:
   - opcional `run_agents_for_hot=true` para enlazar HOT leads con `agent_run_id` (trazabilidad completa).
10. Cola operativa comercial:
   - `GET /dashboard/sales-queue`
   - prioriza prospectos para vendedor: score alto, sin chatbot, con WhatsApp y sin run reciente.
   - export directo:
     - `GET /export/sales-queue-csv`
     - `GET /export/sales-queue-xlsx`
11. Next Best Action (NBA) por prospecto:
   - `GET /dashboard/prospects/{id}/next-best-action`
12. Operación Etapa 3:
   - embudo operativo + conversiones: `GET /dashboard/funnel`
   - pipeline por estados/fases: `GET /dashboard/pipeline-states?limit=200`
   - aging comercial: `GET /dashboard/pipeline-aging?hours_threshold=24`
   - alertas HOT con severidad SLA 24/48/72: `GET /dashboard/hot-alerts?limit=20&stale_hours=24`
   - Streamlit muestra panel operativo completo (embudo, conversiones, estados, aging, alertas HOT).
   - Sync: `POST /pipeline/discover-scan-export`
   - Async: `POST /pipeline/discover-scan-export/async`
   - Polling: `GET /pipeline/jobs/{job_id}` y `GET /pipeline/jobs`
   - Filtro por estado en jobs: `GET /pipeline/jobs?status=queued|running|retry|done|error`
   - body ejemplo: `{ "rubro": "restaurantes", "provincia": "Panamá", "limit": 50, "min_hot_score": 80 }`
   - salida: conteo discover/scan/save + rutas CSV/XLSX de hot leads.
   - jobs async persistidos en tabla `pipeline_jobs` con trazabilidad de fase, intentos y métricas.

## Scoring
Se implementa `Netty Fit Score` 0-100 con reglas solicitadas (chatbot, WhatsApp, formulario, eCommerce, tecnología, señales de contacto, redes, rubro, etc.) y clasificación:
- 80-100: Caliente
- 60-79: Bueno
- 40-59: Medio
- 0-39: Bajo

## Crawling ético
- User-Agent configurable
- Delay entre requests
- Concurrencia limitada
- Respeto de `robots.txt` (configurable)
- Fallback JS solo cuando el HTML no trae contenido suficiente
- Bloqueo de destinos locales/privados (mitigación SSRF)

## Seguridad adicional
- Carga CSV restringida a `data/` y archivos `.csv`.
- Integración IA exige `HTTPS` para `AI_BASE_URL`.

## IA comercial (opcional)
Módulo en `app/ai/` para análisis comercial y generación de mensajes.
No participa del scraping técnico.

Configurar en `.env`:
- `AI_PROVIDER=openai` o `deepseek`
- `AI_API_KEY=...`
- `AI_MODEL=...` (opcional)
- `AI_BASE_URL=...` (opcional, endpoint compatible)

## Estado actual
- MVP estable con escaneo, detección, scoring, persistencia y exportaciones.
- Dashboard Streamlit conectado a API con filtros, detalle y acciones.
- Pipeline comercial sync/async con polling y export dual CSV/XLSX.
- Descubrimiento enchufable por rubro/provincia listo para ampliar proveedores.
- Etapa 4 completada:
  - plantillas por sector (`GET /commercial/templates/{sector}`),
  - recomendador de plan Starter/Pro/Business (`GET /commercial/prospects/{id}/plan`),
  - cola comercial desacoplada persistida en DB (`commercial_queue_items`) con aprobación manual (`/commercial/queue`, `/commercial/queue/{id}/approval`).
  - policy engine de aprobación (incluye casos `requires_manager_approval` por score/canal/rubro).
  - aprobación/rechazo masivo por filtros: `POST /commercial/queue/bulk-approval`.
  - simulación de dispatch sin envío real: `POST /commercial/queue/{id}/simulate-dispatch`.
  - auditoría de cambios de estado: `GET /commercial/queue/audit`.
  - métricas de cola/SLA: `GET /dashboard/commercial/queue-metrics`.
  - **No envío automático**: despacho queda en modo `manual_only` o `simulation_only`.

## Checklist de entrada — Etapa 5 (24/7)
1. ✅ Activar healthchecks y restart policies en Docker Compose.
2. ✅ Backups de DB y exports con retención + verificación de restore.
3. ✅ Monitoreo básico de API/dashboard/cola y alertas de caída.
4. ✅ Playbook de recuperación y smoke tests post-reinicio.

### Estado Etapa 5 (avance)
- `docker-compose.yml` incluye:
  - `restart: unless-stopped` para API/dashboard,
  - healthcheck API: `GET /`,
  - healthcheck dashboard: `GET /_stcore/health`,
  - `depends_on` por condición de servicio saludable.
- Backups operativos agregados:
  - `scripts/backup_data.sh` (DB + exports, retención por `RETENTION_DAYS`).
  - `scripts/verify_restore.sh` (restauración/verificación de backup más reciente).
  - Make targets:
    - `make backup-data`
    - `make verify-restore`
- Monitoreo básico local + alertas:
  - `scripts/monitor_services.sh` (chequeo puntual API/dashboard/cola/pipeline + alertas en `data/monitor_alerts.log`).
  - `scripts/monitor_loop.sh` (ejecución periódica con `INTERVAL_SECONDS`).
  - unit systemd de referencia: `scripts/systemd/netty-monitor.service`.
  - Make targets:
    - `make monitor-check`
    - `make monitor-loop`
- Recuperación operativa:
  - playbook: `OPERATIONS_PLAYBOOK.md`.
  - smoke post-reinicio: `scripts/smoke_post_restart.sh`.
  - Make target: `make smoke-post-restart`.

## Gobernanza para agentes
Antes de cualquier cambio, revisar y cumplir `AGENTS.md` (reglas duras operativas/técnicas).

## Nota
Para migrar a PostgreSQL, cambia `DATABASE_URL` y aplica migraciones Alembic (`alembic upgrade head`).
