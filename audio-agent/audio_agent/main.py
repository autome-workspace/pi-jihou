"""Audio Agent HTTP server (localhost only)."""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from pydantic import BaseModel

from . import __version__
from .devices import enumerate_devices, is_mock
from .player import playback_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Raspberry Pi Audio Agent", version=__version__)

# Default: loopback only (never exposed to the network). When the backend runs
# in a container, set AUDIO_AGENT_BIND=0.0.0.0 so host.docker.internal can
# reach it, and protect the port with a firewall.
BIND_HOST = os.environ.get("AUDIO_AGENT_BIND", "127.0.0.1")
BIND_PORT = int(os.environ.get("AUDIO_AGENT_PORT", "8031"))


class PlayRequest(BaseModel):
    path: str
    device_id: str | None = None


class DeviceRequest(BaseModel):
    id: str


class VolumeRequest(BaseModel):
    volume: int


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "mock": is_mock()}


@app.get("/devices")
async def devices() -> list[dict]:
    return enumerate_devices()


@app.get("/devices/current")
async def current_device() -> dict | None:
    for device in enumerate_devices():
        if device["default"]:
            return device
    return None


@app.put("/devices/current")
async def set_current_device(data: DeviceRequest) -> dict:
    return {"id": data.id, "status": "set"}


@app.post("/play")
async def play(data: PlayRequest) -> dict:
    try:
        return await playback_manager.play(data.path, data.device_id)
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": str(exc)}


@app.post("/stop")
async def stop() -> dict:
    return await playback_manager.stop()


@app.post("/test")
async def test(data: DeviceRequest) -> dict:
    try:
        return await playback_manager.test(data.id)
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": str(exc)}


@app.post("/volume")
async def volume(data: VolumeRequest) -> dict:
    return await playback_manager.set_volume(data.volume)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host=BIND_HOST, port=BIND_PORT)


if __name__ == "__main__":
    main()
