#!/usr/bin/env bash
# Raspberry Pi Audio Scheduler - updater
# Backs up configuration, pulls updates, migrates the DB and restarts services.
set -euo pipefail

APP_NAME="raspi-audio-scheduler"
INSTALL_DIR="/opt/${APP_NAME}"
DATA_DIR="/var/lib/${APP_NAME}"
CONFIG_DIR="/etc/${APP_NAME}"
BACKUP_DIR="${DATA_DIR}/backups"

log() { printf '\033[1;34m[update]\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; }

[ "$(id -u)" -eq 0 ] || { err "run as root"; exit 1; }

backup_config() {
  local stamp
  stamp="$(date +%Y%m%d-%H%M%S)"
  log "Backing up configuration to ${BACKUP_DIR}/${stamp}..."
  install -d -m 755 "${BACKUP_DIR}"
  tar -czf "${BACKUP_DIR}/config-${stamp}.tar.gz" -C "${CONFIG_DIR}" . 2>/dev/null || true
  if [ -f "${DATA_DIR}/database/app.db" ]; then
    cp "${DATA_DIR}/database/app.db" "${BACKUP_DIR}/app-${stamp}.db"
  fi
}

pull_code() {
  cd "${INSTALL_DIR}"
  if [ -d .git ]; then
    log "Pulling latest code..."
    git pull --ff-only
  else
    log "No git repository in ${INSTALL_DIR}; updating files in place is not supported."
  fi
}

pull_images() {
  log "Pulling VOICEVOX image..."
  docker compose -f "${INSTALL_DIR}/compose.yml" pull voicevox
  log "Building backend / frontend images..."
  docker compose -f "${INSTALL_DIR}/compose.yml" build backend frontend
}

migrate() {
  log "Running database migrations..."
  docker compose -f "${INSTALL_DIR}/compose.yml" exec -T backend alembic upgrade head
}

restart() {
  log "Restarting services..."
  systemctl restart raspi-audio-agent.service
  systemctl restart raspi-audio-scheduler.service
}

healthcheck() {
  log "Health check..."
  sleep 5
  if bash "${INSTALL_DIR}/scripts/healthcheck.sh"; then
    log "Health check passed."
  else
    err "Health check failed. Review logs with: journalctl -u raspi-audio-scheduler.service"
  fi
}

main() {
  backup_config
  pull_code
  pull_images
  migrate
  restart
  healthcheck
}

main "$@"
