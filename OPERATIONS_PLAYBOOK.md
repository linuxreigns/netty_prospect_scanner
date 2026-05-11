# OPERATIONS PLAYBOOK — Netty Sales Engine

Este playbook describe operación, recuperación y smoke tests para ejecutar Netty Sales Engine en una mini desktop Debian local 24/7.

## 1. Principios operativos

- No ejecutar scraping agresivo.
- Mantener `.env` fuera de git.
- Aplicar migraciones con Alembic antes de levantar servicios tras cambios de schema.
- Validar backups antes de depender de ellos.
- Mantener `manual_only` / `simulation_only` para operaciones comerciales.

## 2. Arranque estándar

```bash
cd /opt/netty-prospect-scanner
cp .env.example .env  # solo primera vez, luego editar secretos
make migrate-up
docker compose up -d --build
```

Verificar:

```bash
docker compose ps
make monitor-check
```

## 3. Reinicio controlado

```bash
docker compose down
docker compose up -d --build
make smoke-post-restart
```

## 4. Backup y restore check

Backup manual:

```bash
make backup-data
```

Verificación de restore:

```bash
make verify-restore
```

Variables útiles:

```bash
RETENTION_DAYS=30 make backup-data
```

## 5. Monitoreo básico

Chequeo puntual:

```bash
make monitor-check
```

Loop local:

```bash
make monitor-loop
```

Systemd sugerido:

```bash
sudo cp scripts/systemd/netty-monitor.service /etc/systemd/system/netty-monitor.service
sudo systemctl daemon-reload
sudo systemctl enable --now netty-monitor
sudo systemctl status netty-monitor
```

> Ajustar `WorkingDirectory` en el unit file si el proyecto no está en `/opt/netty-prospect-scanner`.

## 6. Incidentes comunes

### API caída

1. Revisar contenedor:
   ```bash
   docker compose ps
   docker logs netty-scanner-api --tail=200
   ```
2. Verificar `.env` y DB:
   ```bash
   test -f data/netty_scanner.db && echo OK
   make migrate-up
   ```
3. Reiniciar:
   ```bash
   docker compose restart api
   make monitor-check
   ```

### Dashboard caído

```bash
docker logs netty-scanner-dashboard --tail=200
docker compose restart dashboard
make monitor-check
```

### DB corrupta o faltante

1. Detener servicios:
   ```bash
   docker compose down
   ```
2. Identificar último backup válido:
   ```bash
   ls -1t data/backups/db/*.db | head
   ```
3. Restaurar manualmente:
   ```bash
   cp data/backups/db/<backup>.db data/netty_scanner.db
   make verify-restore
   docker compose up -d
   make smoke-post-restart
   ```

### Exceso de cola comercial pendiente

1. Revisar métricas:
   ```bash
   curl http://127.0.0.1:8000/dashboard/commercial/queue-metrics
   ```
2. Revisar cola:
   ```bash
   curl http://127.0.0.1:8000/commercial/queue?status=pending
   ```
3. Usar dashboard Streamlit para aprobar/rechazar o simular dispatch.

## 7. Smoke test post-reinicio

```bash
make smoke-post-restart
```

Valida:

- API health.
- Dashboard health.
- Summary dashboard.
- Pipeline async básico.
- Polling de job.
- Cola comercial.
- Export CSV.
- Métricas SLA de cola.

## 8. Cierre de incidente

Registrar en `bitacora.md`:

- fecha/hora,
- síntoma,
- causa probable,
- acciones tomadas,
- resultado,
- próximos ajustes preventivos.
