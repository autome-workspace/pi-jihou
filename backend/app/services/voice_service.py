"""Voice generation service: template expansion -> cache -> VOICEVOX."""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import VoiceCache, VoiceTemplate, VoiceVariable
from app.voice import cache as cache_mod
from app.voice.template import expand_template
from app.voice.voicevox import voicevox_client

logger = logging.getLogger(__name__)


def _load_variables(db: Session) -> list[VoiceVariable]:
    return list(db.query(VoiceVariable).all())


def _variable_map(db: Session) -> dict:
    return {v.name: v for v in _load_variables(db)}


def expand_template_text(db: Session, template: VoiceTemplate, now: datetime) -> str:
    from app.voice.template import _to_variable_values

    variables = _to_variable_values(_load_variables(db))
    return expand_template(template.template_text, variables, now)


async def generate_for_template(
    db: Session, template: VoiceTemplate, now: datetime
) -> tuple[str, str]:
    """Generate (or reuse) a cached WAV for a template.

    Returns ``(cache_key, wav_path)``.
    """
    expanded_text = expand_template_text(db, template, now)

    version = ""
    try:
        version = await voicevox_client.version()
    except Exception:  # noqa: BLE001
        logger.warning("Could not determine VOICEVOX version")

    parameters = {
        "speed": template.speed,
        "pitch": template.pitch,
        "intonation": template.intonation,
        "volume": template.volume,
        "pre_silence_ms": template.pre_silence_ms,
        "post_silence_ms": template.post_silence_ms,
    }
    cache_key = cache_mod.compute_cache_key(
        template.speaker_id, template.style_id, parameters, expanded_text, version
    )

    existing = (
        db.query(VoiceCache).filter(VoiceCache.cache_key == cache_key).one_or_none()
    )
    wav_path = cache_mod.cache_path_for_key(cache_key)
    if existing and wav_path.exists():
        return cache_key, str(wav_path)

    cache_mod.ensure_cache_dir()
    query = await voicevox_client.audio_query(
        text=expanded_text,
        speaker=template.speaker_id,
        speed=template.speed,
        pitch=template.pitch,
        intonation=template.intonation,
        volume=template.volume,
        pre_silence=template.pre_silence_ms / 1000.0,
        post_silence=template.post_silence_ms / 1000.0,
    )
    wav_bytes = await voicevox_client.synthesis(query, template.speaker_id)
    wav_path.write_bytes(wav_bytes)

    record = existing or VoiceCache(cache_key=cache_key)
    record.wav_path = str(wav_path)
    record.speaker_id = template.speaker_id
    record.style_id = template.style_id
    record.parameters = parameters
    record.expanded_text = expanded_text
    record.voicevox_version = version
    record.size_bytes = len(wav_bytes)
    db.add(record)
    db.commit()

    return cache_key, str(wav_path)
