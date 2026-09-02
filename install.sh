#!/usr/bin/env bash
# Raspberry Pi Audio Scheduler - installer
# Idempotent: safe to run multiple times.
set -euo pipefail

APP_NAME="raspi-audio-scheduler"
INSTALL_DIR="/opt/${APP_NAME}"
DATA_DIR="/var/lib/${APP_NAME}"
CONFIG_DIR="/etc/${APP_NAME}"
LOG_DIR="/var/log/${APP_NAME}"
SERVICE_USER="audio-scheduler"
REQUIRED_PACKAGES="curl git jq ffmpeg pipewire pipewire-pulse wireplumber alsa-utils python3 ca-certificates"

log()  { printf '\033[1;34m[install]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; }

must_root() {
  if [ "$(id -u)" -ne 0 ]; then
    err "This script must be run as root (sudo ./install.sh)"
    exit 1
  fi
}

check_os() {
  local arch
  arch="$(uname -m)"
  if [ "$arch" != "aarch64" ]; then
    warn "Expected aarch64 but detected '${arch}'. Only Raspberry Pi 4 (ARM64) is officially supported."
  fi
  if [ -f /proc/device-tree/model ]; then
    local model
    model="$(tr -d '\0' < /proc/device-tree/model)"
    log "Detected hardware: ${model}"
    case "${model}" in
      *"Raspberry Pi 4"*|*"Raspberry Pi 5"*) ;;
      *) warn "This does not look like a Raspberry Pi 4." ;;
    esac
  fi
}

package_installed() {
  dpkg -s "$1" >/dev/null 2>&1
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

user_exists() {
  id -u "${SERVICE_USER}" >/dev/null 2>&1
}

install_packages() {
  log "Updating package lists..."
  apt-get update -y

  local missing=""
  for pkg in ${REQUIRED_PACKAGES}; do
    if ! package_installed "${pkg}"; then
      missing="${missing} ${pkg}"
    fi
  done

  if [ -n "${missing}" ]; then
    log "Installing required packages:${missing}"
    DEBIAN_FRONTEND=noninteractive apt-get install -y ${missing}
  else
    log "Required packages already installed."
  fi

  # Offer (but never force) a full upgrade.
  if [ -t 0 ]; then
    read -r -p "Run 'apt upgrade' now? [y/N] " resp
    case "${resp}" in
      [Yy]*) apt-get upgrade -y ;;
      *) log "Skipping apt upgrade." ;;
    esac
  fi
}

install_docker() {
  if command_exists docker; then
    log "Docker already installed ($(docker --version))."
  else
    log "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
  fi

  if command_exists docker && ! docker compose version >/dev/null 2>&1; then
    warn "Docker Compose plugin not found; it is required. Please install docker-compose-plugin."
  fi
}

create_user() {
  if user_exists; then
    log "User '${SERVICE_USER}' already exists."
  else
    log "Creating service user '${SERVICE_USER}'..."
    useradd --system --home "${DATA_DIR}" --shell /usr/sbin/nologin "${SERVICE_USER}"
  fi
  for grp in audio video; do
    if getent group "${grp}" >/dev/null 2>&1; then
      usermod -a -G "${grp}" "${SERVICE_USER}" 2>/dev/null || true
    fi
  done
}

create_dirs() {
  log "Ensuring directories..."
  install -d -m 755 -o root -g root "${INSTALL_DIR}"
  install -d -m 755 -o "${SERVICE_USER}" -g "${SERVICE_USER}" "${DATA_DIR}"
  install -d -m 755 -o "${SERVICE_USER}" -g "${SERVICE_USER}" "${DATA_DIR}/audio"
  install -d -m 755 -o "${SERVICE_USER}" -g "${SERVICE_USER}" "${DATA_DIR}/voice-cache"
  install -d -m 755 -o "${SERVICE_USER}" -g "${SERVICE_USER}" "${DATA_DIR}/database"
  install -d -m 755 -o "${SERVICE_USER}" -g "${SERVICE_USER}" "${DATA_DIR}/backups"
  install -d -m 755 -o root -g "${SERVICE_USER}" "${CONFIG_DIR}"
  install -d -m 755 -o root -g root "${LOG_DIR}"
}

write_env() {
  local env_file="${CONFIG_DIR}/app.env"
  if [ -f "${env_file}" ]; then
    log "Environment file already exists (${env_file}); leaving untouched."
    return
  fi
  log "Creating environment file ${env_file}..."
  cat > "${env_file}" <<EOF
APP_PORT=8080
APP_TIMEZONE=Asia/Tokyo
DATA_DIR=${DATA_DIR}
NTP_PRIMARY=ntp.nict.jp
NTP_SECONDARY=time.cloudflare.com
NTP_TERTIARY=time.google.com
NTP_INTERVAL=300
VOICEVOX_URL=http://127.0.0.1:50021
VOICE_PREFETCH_SECONDS=600
AUDIO_AGENT_URL=http://host.docker.internal:8031
EOF
  chmod 640 "${env_file}"
  chown root:"${SERVICE_USER}" "${env_file}"
}

copy_app() {
  log "Copying application files to ${INSTALL_DIR}..."
  rsync -a --delete \
    --exclude '.git' \
    --exclude 'data' \
    --exclude 'frontend/node_modules' \
    ./ "${INSTALL_DIR}/"
}

detect_audio_user() {
  # Return the user who owns an active PipeWire session; otherwise the first
  # regular user; otherwise root. The agent must run as the PipeWire session
  # user (or root) to access the audio device.
  local socket uid user
  socket="$(ls -d /run/user/[0-9]*/pipewire-0 2>/dev/null | head -n1)"
  if [ -n "${socket}" ]; then
    uid="$(basename "$(dirname "${socket}")")"
    user="$(id -un "${uid}" 2>/dev/null || true)"
    if [ -n "${user}" ]; then echo "${user}"; return; fi
  fi
  user="$(getent passwd | awk -F: '$3>=1000 && $3<60000 {print $1; exit}')"
  echo "${user:-root}"
}

install_audio_agent() {
  log "Installing audio-agent (systemd service)..."
  # The audio agent uses only the Python standard library, so no venv/pip
  # (and no PyPI access) is required at install time.
  local agent_dir="${INSTALL_DIR}/audio-agent"
  local agent_user agent_uid agent_home
  agent_user="$(detect_audio_user)"
  agent_uid="$(id -u "${agent_user}" 2>/dev/null || echo 0)"
  agent_home="$(getent passwd "${agent_user}" | cut -d: -f6)"
  agent_home="${agent_home:-/var/lib/${APP_NAME}}"

  install -m 644 "${agent_dir}/raspi-audio-agent.service" /etc/systemd/system/
  install -d /etc/systemd/system/raspi-audio-agent.service.d
  {
    echo "[Service]"
    echo "User=${agent_user}"
    echo "Group=audio"
    echo "Environment=HOME=${agent_home}"
    echo "Environment=XDG_RUNTIME_DIR=/run/user/${agent_uid}"
    # The backend runs in a container and reaches the agent via host-gateway.
    echo "Environment=AUDIO_AGENT_BIND=0.0.0.0"
  } > /etc/systemd/system/raspi-audio-agent.service.d/override.conf
  log "Audio agent will run as user '${agent_user}' (uid ${agent_uid})."

  systemctl daemon-reload
  systemctl enable raspi-audio-agent.service
  systemctl restart raspi-audio-agent.service
}

setup_backend_service() {
  log "Setting up backend systemd service..."
  install -m 644 deploy/systemd/raspi-audio-scheduler.service /etc/systemd/system/
  install -m 644 deploy/systemd/raspi-audio-scheduler.target /etc/systemd/system/
  systemctl daemon-reload
  systemctl enable raspi-audio-scheduler.service
}

pull_images() {
  log "Pulling VOICEVOX image..."
  docker compose -f "${INSTALL_DIR}/compose.yml" pull voicevox
  log "Building backend / frontend images..."
  docker compose -f "${INSTALL_DIR}/compose.yml" build backend frontend
}

check_audio() {
  if command_exists wpctl || command_exists pw-cli || command_exists pactl; then
    log "PipeWire/Pulse tools detected."
    local count
    count="$(bash "${INSTALL_DIR}/scripts/detect-audio.sh" 2>/dev/null | grep -c 'alsa_output\|Built-in\|HDMI\|USB' || true)"
    log "Detected audio outputs: ~${count}"
  else
    warn "No PipeWire tools found. Audio output will be unavailable until PipeWire is configured."
  fi
}

summary() {
  local ip
  ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
  ip="${ip:-<ip-address>}"
  cat <<EOF

Raspberry Pi Audio Scheduler installed successfully.

Web UI:
  http://${ip}/
  http://${ip}:8080  (API)

Services:
  audio-agent    $(systemctl is-active raspi-audio-agent.service)
  backend        $(systemctl is-active raspi-audio-scheduler.service || echo "not-started")
  voicevox       $(docker ps -q -f name=raspi-audio-voicevox >/dev/null 2>&1 && echo running || echo pending)

Configuration:
  ${CONFIG_DIR}/app.env
EOF
}

main() {
  must_root
  check_os
  create_user
  create_dirs
  install_packages
  install_docker
  copy_app
  write_env
  install_audio_agent
  setup_backend_service
  pull_images
  check_audio
  # Start the backend stack (backend + frontend + voicevox).
  systemctl restart raspi-audio-scheduler.service || true
  summary
}

main "$@"
