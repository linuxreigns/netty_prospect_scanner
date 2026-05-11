#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${ROOT_DIR}/data"
DB_FILE="${DATA_DIR}/netty_scanner.db"
EXPORTS_DIR="${DATA_DIR}/exports"
BACKUP_ROOT="${DATA_DIR}/backups"
DB_BACKUP_DIR="${BACKUP_ROOT}/db"
EXPORTS_BACKUP_DIR="${BACKUP_ROOT}/exports"

RETENTION_DAYS="${RETENTION_DAYS:-14}"
TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"

mkdir -p "${DB_BACKUP_DIR}" "${EXPORTS_BACKUP_DIR}"

if [[ -f "${DB_FILE}" ]]; then
  cp "${DB_FILE}" "${DB_BACKUP_DIR}/netty_scanner_${TIMESTAMP}.db"
else
  echo "[WARN] DB file no encontrado: ${DB_FILE}" >&2
fi

if [[ -d "${EXPORTS_DIR}" ]]; then
  tar -czf "${EXPORTS_BACKUP_DIR}/exports_${TIMESTAMP}.tar.gz" -C "${DATA_DIR}" "exports"
else
  echo "[WARN] Exports dir no encontrado: ${EXPORTS_DIR}" >&2
fi

find "${DB_BACKUP_DIR}" -type f -name "*.db" -mtime +"${RETENTION_DAYS}" -delete
find "${EXPORTS_BACKUP_DIR}" -type f -name "*.tar.gz" -mtime +"${RETENTION_DAYS}" -delete

echo "[OK] Backup completado"
echo "- DB backup dir: ${DB_BACKUP_DIR}"
echo "- Exports backup dir: ${EXPORTS_BACKUP_DIR}"
echo "- Retention days: ${RETENTION_DAYS}"
