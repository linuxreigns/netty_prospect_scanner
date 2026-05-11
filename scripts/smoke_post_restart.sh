#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://127.0.0.1:8000}"
DASHBOARD_BASE="${DASHBOARD_BASE:-http://127.0.0.1:8501}"
TMP_DIR="${TMP_DIR:-data/tmp_smoke}"

mkdir -p "$TMP_DIR"

echo "[SMOKE] 1/8 API health"
python3 - <<'PY'
import urllib.request
urllib.request.urlopen('http://127.0.0.1:8000/', timeout=8)
print('ok')
PY

echo "[SMOKE] 2/8 Dashboard health"
python3 - <<'PY'
import urllib.request
urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=8)
print('ok')
PY

echo "[SMOKE] 3/8 Dashboard summary"
python3 - <<'PY'
import json, urllib.request
with urllib.request.urlopen('http://127.0.0.1:8000/dashboard/summary', timeout=12) as r:
    d = json.loads(r.read().decode('utf-8'))
assert 'total_sites' in d
print('ok')
PY

echo "[SMOKE] 4/8 Pipeline async launch"
JOB_ID=$(python3 - <<'PY'
import json, urllib.request
req = urllib.request.Request(
    'http://127.0.0.1:8000/pipeline/discover-scan-export/async',
    data=json.dumps({'rubro':'restaurantes','provincia':'Panamá','limit':1,'min_hot_score':80}).encode('utf-8'),
    headers={'Content-Type':'application/json'},
    method='POST'
)
with urllib.request.urlopen(req, timeout=20) as r:
    d = json.loads(r.read().decode('utf-8'))
print(d.get('job_id',''))
PY
)

if [[ -z "$JOB_ID" ]]; then
  echo "[SMOKE][ERROR] job_id vacío" >&2
  exit 1
fi

echo "[SMOKE] 5/8 Pipeline job poll ($JOB_ID)"
python3 - <<PY
import json, time, urllib.request
job_id = "${JOB_ID}"
ok = False
for _ in range(20):
    with urllib.request.urlopen(f'http://127.0.0.1:8000/pipeline/jobs/{job_id}', timeout=12) as r:
        d = json.loads(r.read().decode('utf-8'))
    if d.get('status') in {'done','error'}:
        ok = True
        break
    time.sleep(1)
if not ok:
    raise SystemExit('pipeline job no completó dentro de timeout smoke')
print('ok')
PY

echo "[SMOKE] 6/8 Commercial queue list"
python3 - <<'PY'
import json, urllib.request
with urllib.request.urlopen('http://127.0.0.1:8000/commercial/queue?limit=5', timeout=12) as r:
    d = json.loads(r.read().decode('utf-8'))
assert 'items' in d
print('ok')
PY

echo "[SMOKE] 7/8 Export CSV trigger"
python3 - <<'PY'
import json, urllib.request
with urllib.request.urlopen('http://127.0.0.1:8000/export/csv', timeout=20) as r:
    d = json.loads(r.read().decode('utf-8'))
assert 'file' in d
print('ok')
PY

echo "[SMOKE] 8/8 Queue metrics"
python3 - <<'PY'
import json, urllib.request
with urllib.request.urlopen('http://127.0.0.1:8000/dashboard/commercial/queue-metrics?hours_threshold=24', timeout=12) as r:
    d = json.loads(r.read().decode('utf-8'))
assert 'counts' in d and 'pending_aging' in d
print('ok')
PY

echo "[SMOKE][OK] post-restart smoke completado"
