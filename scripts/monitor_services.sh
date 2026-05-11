#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://127.0.0.1:8000}"
DASHBOARD_BASE="${DASHBOARD_BASE:-http://127.0.0.1:8501}"
QUEUE_PENDING_WARN="${QUEUE_PENDING_WARN:-100}"
ALERT_LOG="${ALERT_LOG:-data/monitor_alerts.log}"
CPU_WARN_PCT="${CPU_WARN_PCT:-85}"
MEM_WARN_PCT="${MEM_WARN_PCT:-85}"
DISK_WARN_PCT="${DISK_WARN_PCT:-85}"
DISK_PATH="${DISK_PATH:-/}"

mkdir -p "$(dirname "$ALERT_LOG")"

timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

alert() {
  local level="$1"
  local msg="$2"
  echo "[$(timestamp)] [$level] $msg" | tee -a "$ALERT_LOG" >&2
}

ok() {
  local msg="$1"
  echo "[$(timestamp)] [OK] $msg"
}

fetch_json() {
  local url="$1"
  python3 - "$url" <<'PY'
import json, sys, urllib.request
url = sys.argv[1]
with urllib.request.urlopen(url, timeout=8) as r:
    print(r.read().decode('utf-8'))
PY
}

# 1) API health
if ! fetch_json "${API_BASE}/" >/tmp/netty_api_health.json 2>/tmp/netty_api_health.err; then
  alert "CRITICAL" "API caída o no responde: ${API_BASE}/"
  exit 1
fi
ok "API responde"

# 2) Dashboard health endpoint
if ! python3 - <<'PY'
import urllib.request
urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=8)
print('ok')
PY
then
  alert "HIGH" "Dashboard no responde healthcheck: ${DASHBOARD_BASE}/_stcore/health"
  exit 1
fi
ok "Dashboard responde"

# 3) Queue metrics
if ! fetch_json "${API_BASE}/dashboard/commercial/queue-metrics?hours_threshold=24" >/tmp/netty_queue_metrics.json 2>/tmp/netty_queue_metrics.err; then
  alert "HIGH" "No se pudieron consultar métricas de cola"
  exit 1
fi

pending=$(python3 - <<'PY'
import json
with open('/tmp/netty_queue_metrics.json', 'r', encoding='utf-8') as f:
    d = json.load(f)
print(d.get('counts', {}).get('pending', 0))
PY
)

if [ "$pending" -ge "$QUEUE_PENDING_WARN" ]; then
  alert "MEDIUM" "Pendientes en cola >= umbral (${pending} >= ${QUEUE_PENDING_WARN})"
else
  ok "Cola pendiente dentro de umbral (${pending}/${QUEUE_PENDING_WARN})"
fi

# 4) Pipeline states quick check
if ! fetch_json "${API_BASE}/dashboard/pipeline-states?limit=50" >/tmp/netty_pipeline_states.json 2>/tmp/netty_pipeline_states.err; then
  alert "HIGH" "No se pudo consultar estado de pipeline"
  exit 1
fi

errors=$(python3 - <<'PY'
import json
with open('/tmp/netty_pipeline_states.json', 'r', encoding='utf-8') as f:
    d = json.load(f)
print(d.get('status_counts', {}).get('error', 0))
PY
)

if [ "$errors" -gt 0 ]; then
  alert "MEDIUM" "Existen jobs pipeline en error: ${errors}"
else
  ok "Sin jobs pipeline en error"
fi

# 5) Recursos del sistema (CPU / RAM / Disco)
resources=$(python3 - "$CPU_WARN_PCT" "$MEM_WARN_PCT" "$DISK_WARN_PCT" "$DISK_PATH" <<'PY'
import sys, shutil, time

cpu_warn  = int(sys.argv[1])
mem_warn  = int(sys.argv[2])
disk_warn = int(sys.argv[3])
disk_path = sys.argv[4]

def read_stat():
    with open('/proc/stat') as f:
        parts = f.readline().split()
    total = sum(int(x) for x in parts[1:])
    idle  = int(parts[4])
    return total, idle

t1, i1 = read_stat()
time.sleep(0.5)
t2, i2 = read_stat()
dt = t2 - t1
cpu_pct = int((1 - (i2 - i1) / dt) * 100) if dt > 0 else 0

mem = {}
with open('/proc/meminfo') as f:
    for line in f:
        k, v = line.split(':', 1)
        mem[k.strip()] = int(v.strip().split()[0])
mem_total = mem['MemTotal']
mem_avail = mem.get('MemAvailable', mem.get('MemFree', 0))
mem_pct   = int((mem_total - mem_avail) * 100 / mem_total)

usage    = shutil.disk_usage(disk_path)
disk_pct = int(usage.used * 100 / usage.total)

alerts = []
if cpu_pct  >= cpu_warn:  alerts.append(f"CPU:{cpu_pct}%>={cpu_warn}%")
if mem_pct  >= mem_warn:  alerts.append(f"MEM:{mem_pct}%>={mem_warn}%")
if disk_pct >= disk_warn: alerts.append(f"DISK:{disk_pct}%>={disk_warn}%")

print(f"CPU={cpu_pct}% MEM={mem_pct}% DISK={disk_pct}% ALERTS={'|'.join(alerts) or 'none'}")
PY
)

cpu_val=$(echo "$resources"  | grep -oP 'CPU=\K[0-9]+')
mem_val=$(echo "$resources"  | grep -oP 'MEM=\K[0-9]+')
disk_val=$(echo "$resources" | grep -oP 'DISK=\K[0-9]+')
res_alerts=$(echo "$resources" | grep -oP 'ALERTS=\K.*')

if [ "$res_alerts" != "none" ]; then
  alert "MEDIUM" "Recursos sobre umbral — $res_alerts"
else
  ok "Recursos OK — CPU=${cpu_val}% MEM=${mem_val}% DISK=${disk_val}%"
fi

ok "Monitoreo puntual completado"
