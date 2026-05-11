#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${ROOT_DIR}/data"
BACKUP_ROOT="${DATA_DIR}/backups"
DB_BACKUP_DIR="${BACKUP_ROOT}/db"
EXPORTS_BACKUP_DIR="${BACKUP_ROOT}/exports"
TMP_DIR="${DATA_DIR}/tmp_restore_check"

mkdir -p "${TMP_DIR}"

LATEST_DB="$(ls -1t "${DB_BACKUP_DIR}"/*.db 2>/dev/null | head -n1 || true)"
LATEST_EXPORTS="$(ls -1t "${EXPORTS_BACKUP_DIR}"/*.tar.gz 2>/dev/null | head -n1 || true)"

if [[ -z "${LATEST_DB}" ]]; then
  echo "[ERROR] No se encontró backup de DB en ${DB_BACKUP_DIR}" >&2
  exit 1
fi

if [[ -z "${LATEST_EXPORTS}" ]]; then
  echo "[ERROR] No se encontró backup de exports en ${EXPORTS_BACKUP_DIR}" >&2
  exit 1
fi

RESTORE_DB="${TMP_DIR}/restore_test.db"
cp "${LATEST_DB}" "${RESTORE_DB}"

python3 - <<'PY'
import sqlite3
from pathlib import Path
p = Path("data/tmp_restore_check/restore_test.db")
con = sqlite3.connect(p)
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prospects';")
row = cur.fetchone()
con.close()
if not row:
    raise SystemExit("[ERROR] restore DB inválida: tabla prospects no encontrada")
print("[OK] restore DB verificada")
PY

RESTORE_EXPORTS_DIR="${TMP_DIR}/exports"
rm -rf "${RESTORE_EXPORTS_DIR}"
mkdir -p "${RESTORE_EXPORTS_DIR}"
tar -xzf "${LATEST_EXPORTS}" -C "${TMP_DIR}"

if [[ ! -d "${TMP_DIR}/exports" ]]; then
  echo "[ERROR] restore exports inválido: carpeta exports no encontrada" >&2
  exit 1
fi

echo "[OK] restore exports verificado"
rm -rf "${TMP_DIR}"
echo "[OK] Verificación de restore completada"
