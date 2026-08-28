#!/usr/bin/env bash
# Raspberry Pi Audio Scheduler - uninstaller
# By default removes the application only and keeps data.
set -euo pipefail

APP_NAME="raspi-audio-scheduler"
INSTALL_DIR="/opt/${APP_NAME}"
DATA_DIR="/var/lib/${APP_NAME}"
CONFIG_DIR="/etc/${APP_NAME}"
LOG_DIR="/var/log/${APP_NAME}"
SERVICE_USER="audio-scheduler"

log() { printf '\033[1;34m[uninstall]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { echo "run as root" >&2; exit 1; }

REMOVE_DATA=0
for arg in "$@"; do
  case "${arg}" in
    --all|-a) REMOVE_DATA=1 ;;
  esac
done

stop_services() {
  log "Stopping services..."
  systemctl stop raspi-audio-scheduler.service 2>/dev/null || true
  systemctl stop raspi-audio-agent.service 2>/dev/null || true
  systemctl disable raspi-audio-scheduler.service 2>/dev/null || true
  systemctl disable raspi-audio-agent.service 2>/dev/null || true
}

remove_services() {
  log "Removing systemd units..."
  rm -f /etc/systemd/system/raspi-audio-scheduler.service
  rm -f /etc/systemd/system/raspi-audio-scheduler.target
  rm -f /etc/systemd/system/raspi-audio-agent.service
  systemctl daemon-reload
}

remove_app() {
  log "Removing application directory ${INSTALL_DIR}..."
  rm -rf "${INSTALL_DIR}"
  log "Removing configuration ${CONFIG_DIR}..."
  rm -rf "${CONFIG_DIR}"
  log "Removing logs ${LOG_DIR}..."
  rm -rf "${LOG_DIR}"
}

remove_data() {
  log "Removing data directory ${DATA_DIR}..."
  rm -rf "${DATA_DIR}"
}

remove_user() {
  if id -u "${SERVICE_USER}" >/dev/null 2>&1; then
    log "Removing service user '${SERVICE_USER}'..."
    userdel "${SERVICE_USER}" 2>/dev/null || true
  fi
}

main() {
  stop_services
  remove_services
  remove_app

  if [ "${REMOVE_DATA}" -eq 1 ]; then
    remove_data
  else
    warn "Keeping data in ${DATA_DIR}. Use --all to also remove all data."
  fi

  if [ "${REMOVE_DATA}" -eq 1 ]; then
    remove_user
  else
    warn "Keeping service user '${SERVICE_USER}'."
  fi

  log "Uninstall complete."
}

main "$@"
