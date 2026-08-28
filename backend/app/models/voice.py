"""VOICEVOX template, variable and cache models."""

from sqlalchemy import JSON, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPkMixin
from app.models.enums import GenerationStrategy


class VoiceTemplate(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "voice_templates"

    name: Mapped[str] = mapped_column(String(255))
    template_text: Mapped[str] = mapped_column(String(4096))
    speaker_id: Mapped[int] = mapped_column(Integer, default=1)
    style_id: Mapped[int] = mapped_column(Integer, default=0)
    speed: Mapped[float] = mapped_column(Float, default=1.0)
    pitch: Mapped[float] = mapped_column(Float, default=0.0)
    intonation: Mapped[float] = mapped_column(Float, default=1.0)
    volume: Mapped[float] = mapped_column(Float, default=1.0)
    pre_silence_ms: Mapped[int] = mapped_column(Integer, default=0)
    post_silence_ms: Mapped[int] = mapped_column(Integer, default=0)
    generation_strategy: Mapped[str] = mapped_column(
        String(32), default=GenerationStrategy.BEFORE_PLAYBACK.value
    )


class VoiceVariable(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "voice_variables"

    name: Mapped[str] = mapped_column(String(128), unique=True)
    value_type: Mapped[str] = mapped_column(String(16))
    value: Mapped[str] = mapped_column(String(1024), default="")


class VoiceCache(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "voice_cache"

    cache_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    wav_path: Mapped[str] = mapped_column(String(1024))
    speaker_id: Mapped[int] = mapped_column(Integer, default=1)
    style_id: Mapped[int] = mapped_column(Integer, default=0)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    expanded_text: Mapped[str] = mapped_column(String(4096), default="")
    voicevox_version: Mapped[str] = mapped_column(String(64), default="")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
