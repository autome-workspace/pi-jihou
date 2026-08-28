"""Audio playback.

MVP uses ``pw-play`` (PipeWire) or ``aplay`` (ALSA) as the playback backend. The
structure allows swapping to a resident playback engine later. In mock mode,
playback is only logged. Standard library only (no third-party dependencies).
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import threading

logger = logging.getLogger(__name__)

from .devices import is_mock


class PlaybackManager:
    def __init__(self) -> None:
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()

    @property
    def is_playing(self) -> bool:
        with self._lock:
            proc = self._proc
        return proc is not None and proc.poll() is None

    def play(self, path: str, device_id: str | None = None) -> dict:
        self.stop()

        if is_mock():
            logger.info("PLAY %s (device=%s)", path, device_id or "default")
            return {"status": "playing", "path": path, "device_id": device_id}

        cmd = self._build_command(path, device_id)
        logger.info("Playing %s via %s", path, cmd)
        with self._lock:
            self._proc = subprocess.Popen(cmd)
        return {"status": "playing", "path": path, "device_id": device_id}

    def _build_command(self, path: str, device_id: str | None) -> list[str]:
        if shutil.which("pw-play"):
            cmd = ["pw-play"]
            if device_id:
                cmd += ["--target", device_id]
            return cmd + [path]
        if shutil.which("aplay"):
            cmd = ["aplay"]
            if device_id and device_id.startswith("hw:"):
                cmd += ["-D", device_id]
            return cmd + [path]
        raise RuntimeError("no audio playback backend found (pw-play or aplay required)")

    def stop(self) -> dict:
        with self._lock:
            proc = self._proc
            self._proc = None
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        return {"status": "stopped"}

    def test(self, device_id: str) -> dict:
        if is_mock():
            logger.info("TEST TONE (device=%s)", device_id)
            return {"status": "testing", "device_id": device_id}
        tone = "/tmp/raspi-audio-test.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=1000:duration=1", tone],
            check=False,
        )
        return self.play(tone, device_id)

    def set_volume(self, volume: int) -> dict:
        if not is_mock() and shutil.which("wpctl"):
            subprocess.run(
                ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{volume / 100:.2f}"],
                check=False,
            )
        return {"volume": volume}


playback_manager = PlaybackManager()
