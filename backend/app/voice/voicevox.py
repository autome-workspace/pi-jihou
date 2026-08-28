"""VOICEVOX ENGINE HTTP client.

The backend proxies all VOICEVOX access; the frontend never talks to VOICEVOX
directly.
"""

from __future__ import annotations

import httpx

from app.config import settings


class VoicevoxClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.voicevox_url).rstrip("/")

    async def version(self) -> str:
        async with httpx.AsyncClient(timeout=settings.voicevox_timeout) as client:
            resp = await client.get(f"{self.base_url}/version")
            resp.raise_for_status()
            return resp.text.strip()

    async def speakers(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=settings.voicevox_timeout) as client:
            resp = await client.get(f"{self.base_url}/speakers")
            resp.raise_for_status()
            return resp.json()

    async def audio_query(
        self,
        text: str,
        speaker: int,
        speed: float = 1.0,
        pitch: float = 0.0,
        intonation: float = 1.0,
        volume: float = 1.0,
        pre_silence: float = 0.0,
        post_silence: float = 0.0,
    ) -> dict:
        params = {
            "text": text,
            "speaker": speaker,
            "speedScale": speed,
            "pitchScale": pitch,
            "intonationScale": intonation,
            "volumeScale": volume,
            "prePhonemeLength": pre_silence,
            "postPhonemeLength": post_silence,
        }
        async with httpx.AsyncClient(timeout=settings.voicevox_timeout) as client:
            resp = await client.post(f"{self.base_url}/audio_query", params=params)
            resp.raise_for_status()
            return resp.json()

    async def synthesis(self, query: dict, speaker: int) -> bytes:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/synthesis",
                params={"speaker": speaker},
                json=query,
            )
            resp.raise_for_status()
            return resp.content

    async def health(self) -> bool:
        try:
            await self.version()
            return True
        except httpx.HTTPError:
            return False


voicevox_client = VoicevoxClient()
