# RELEASE.md — Checklist de Release

## Objetivo
Checklist operativo para publicar versiones de Netty Prospect Scanner con calidad, trazabilidad y seguridad.

## 1) Pre-release técnico
- [ ] `make format`
- [ ] `make lint`
- [ ] `make test`
- [ ] `python -m compileall app dashboard tests`
- [ ] Validar migraciones:
  - [ ] `alembic upgrade head`
  - [ ] `alembic downgrade -1` (en entorno de prueba)

## 2) Validación funcional mínima (MVP)
- [ ] API inicia correctamente (`uvicorn app.main:app --reload`)
- [ ] Dashboard inicia (`streamlit run dashboard/streamlit_app.py`)
- [ ] Escaneo CSV funciona (`POST /scan/csv`)
- [ ] Dashboard summary/prospects responde
- [ ] Exportaciones CSV/XLSX/PDF generan archivo
- [ ] Pipeline sync responde (`POST /pipeline/discover-scan-export`)
- [ ] Pipeline async responde + polling (`/async`, `/jobs/{job_id}`)

## 3) Seguridad y gobernanza
- [ ] Revisar `AGENTS.md` y cumplimiento de reglas duras
- [ ] Confirmar que `.env` no está versionado
- [ ] Verificar que no hay llaves/API keys en logs/código
- [ ] Verificar crawling ético (delay, concurrencia, robots)

## 4) Documentación
- [ ] Actualizar `README.md` si hubo cambios funcionales
- [ ] Actualizar `bitacora.md` (fecha, cambios, errores, pendientes)
- [ ] Actualizar `CHANGELOG.md`

## 5) Versionado y publicación
- [ ] Definir versión SemVer (`MAJOR.MINOR.PATCH`)
- [ ] Crear tag Git (`vX.Y.Z`)
- [ ] Publicar release notes desde `CHANGELOG.md`
- [ ] Validar CI en rama principal (workflow verde)

## 6) Post-release
- [ ] Smoke test en entorno objetivo
- [ ] Verificar creación de prospectos y exports
- [ ] Monitorear errores de API/logs iniciales
- [ ] Registrar hallazgos en bitácora
