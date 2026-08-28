"""Playback queue and history models."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPkMixin
from app.models.enums import PlaybackResult, QueueStatus


class PlaybackQueue(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "playback_queue"

    schedule_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("schedules.id"), nullable=True
    )
    audio_file_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    voice_cache_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=10)
    status: Mapped[str] = mapped_column(String(16), default=QueueStatus.PENDING.value)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.utcnow())


class PlaybackHistory(Base, UUIDPkMixin):
    __tablename__ = "playback_history"

    schedule_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("schedules.id"), nullable=True
    )
    audio_file_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    voice_cache_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    delay_ms: Mapped[float] = mapped_column(Float, default=0.0)
    audio_device: Mapped[str] = mapped_column(String(255), default="")
    result: Mapped[str] = mapped_column(String(16), default=PlaybackResult.SUCCESS.value)
    error_message: Mapped[str] = mapped_column(String(1024), default="")
