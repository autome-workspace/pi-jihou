#!/usr/bin/env bash
# Detect and list available audio output devices via PipeWire (wpctl) or ALSA.
# Used by install.sh and the audio-agent device manager.
set -euo pipefail

list_wireplumber() {
  if command -v wpctl >/dev/null 2>&1; then
    wpctl status 2>/dev/null | awk '/Sinks:/{flag=1; next} /Sources:/{flag=0} flag' || true
  fi
}

list_alsa() {
  if command -v aplay >/dev/null 2>&1; then
    aplay -l 2>/dev/null || true
  fi
}

echo "== PipeWire sinks =="
list_wireplumber

echo "== ALSA playback devices =="
list_alsa
