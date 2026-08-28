"""Audio playback.

MVP uses ``pw-play`` (PipeWire) or ``aplay`` (ALSA) as the playback backend. The
structure allows swapping to a resident playback engine later. In mock mode,
playback is only logged.
"""

from __future__ import annotations

import asyncio
import logging
import shutil

logger = logging.getLogger(__name__)

from .devices import is_mock


class PlaybackManager:
    def __init__(self) -> None:
        self._proc: asyncio.subprocess.Process | None = None
        self._current_device: str | None = None

    @property
    def is_playing(self) -> bool:
        return self._proc is not None and self._proc.returncode is None

    async def play(self, path: str, device_id: str | None = None) -> dict:
        if self.is_playing:
            await self.stop()

        if is_mock():
            logger.info("PLAY %s (device=%s)", path, device_id or "default")
            return {"status": "playing", "path": path, "device_id": device_id}

        self._current_device = device_id
        cmd = self._build_command(path, device_id)
        logger.info("Playing %s via %s", path, cmd)
        self._proc = await asyncio.create_subprocess_exec(*cmd)
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

    async def stop(self) -> dict:
        if self._proc and self._proc.returncode is None:
            self._proc.terminate()
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._proc.kill()
        self._proc = None
        return {"status": "stopped"}

    async def test(self, device_id: str) -> dict:
        # Play a generated short tone via the selected device.
        if is_mock():
            logger.info("TEST TONE (device=%s)", device_id)
            return {"status": "testing", "device_id": device_id}
        tone = "/tmp/raspi-audio-test.wav"
        await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            "sine=frequency=1000:duration=1", tone,
        )
        return await self.play(tone, device_id)

    async def set_volume(self, volume: int) -> dict:
        if not is_mock() and shutil.which("wpctl"):
            await asyncio.create_subprocess_exec(
                "wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{volume / 100:.2f}"
            )
        return {"volume": volume}


playback_manager = PlaybackManager()
