#!/usr/bin/env bash
set -euo pipefail

INTERVAL_SECONDS="${INTERVAL_SECONDS:-60}"

while true; do
  ./scripts/monitor_services.sh || true
  sleep "$INTERVAL_SECONDS"
done
