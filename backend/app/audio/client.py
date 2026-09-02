"""HTTP client for the host-side Audio Agent (listens on 127.0.0.1:8031)."""

from __future__ import annotations

import httpx

from app.config import settings


class AudioAgentClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.audio_agent_url).rstrip("/")

    async def get_devices(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{self.base_url}/devices")
            resp.raise_for_status()
            return resp.json()

    async def get_current_device(self) -> dict | None:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{self.base_url}/devices/current")
            resp.raise_for_status()
            return resp.json()

    async def set_current_device(self, device_id: str) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.put(
                f"{self.base_url}/devices/current", json={"id": device_id}
            )
            resp.raise_for_status()
            return resp.json()

    async def play(self, path: str, device_id: str | None = None) -> dict:
        payload: dict = {"path": path}
        if device_id:
            payload["device_id"] = device_id
        # The agent blocks /play until playback completes, so allow long audio.
        async with httpx.AsyncClient(timeout=3600) as client:
            resp = await client.post(f"{self.base_url}/play", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def stop(self) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{self.base_url}/stop")
            resp.raise_for_status()
            return resp.json()

    async def test(self, device_id: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{self.base_url}/test", json={"device_id": device_id})
            resp.raise_for_status()
            return resp.json()

    async def set_volume(self, volume: int) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{self.base_url}/volume", json={"volume": volume})
            resp.raise_for_status()
            return resp.json()

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(f"{self.base_url}/health")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False


audio_agent_client = AudioAgentClient()
