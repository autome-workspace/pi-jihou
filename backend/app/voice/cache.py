"""Voice cache: keyed WAV storage for generated VOICEVOX audio."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.config import settings


def compute_cache_key(
    speaker: int,
    style: int,
    parameters: dict,
    expanded_text: str,
    voicevox_version: str,
) -> str:
    """Compute a deterministic SHA-256 cache key.

    Per the design, the key is derived from speaker, style, generation
    parameters, the expanded text and the VOICEVOX version.
    """
    payload = {
        "speaker": speaker,
        "style": style,
        "parameters": parameters,
        "expanded_text": expanded_text,
        "voicevox_version": voicevox_version,
    }
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def cache_path_for_key(cache_key: str) -> Path:
    return settings.voice_cache_dir / f"{cache_key}.wav"


def ensure_cache_dir() -> Path:
    settings.voice_cache_dir.mkdir(parents=True, exist_ok=True)
    return settings.voice_cache_dir
