#!/usr/bin/env bash
# Health check for the Raspberry Pi Audio Scheduler backend.
# Exits 0 when healthy, non-zero otherwise. Safe to use with systemd / curl.
set -euo pipefail

PORT="${APP_PORT:-8080}"
URL="http://127.0.0.1:${PORT}/api/v1/system/health"

if command -v curl >/dev/null 2>&1; then
  curl -fsS --max-time 5 "${URL}" >/dev/null
elif command -v wget >/dev/null 2>&1; then
  wget -q --timeout=5 -O /dev/null "${URL}"
else
  echo "curl or wget required" >&2
  exit 2
fi
