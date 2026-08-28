"""Audio file model."""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPkMixin


class AudioFile(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "audio_files"

    name: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String(255))
    original_path: Mapped[str] = mapped_column(String(1024))
    playback_path: Mapped[str] = mapped_column(String(1024), default="")
    format: Mapped[str] = mapped_column(String(16), default="")
    sample_rate: Mapped[int] = mapped_column(Integer, default=0)
    channels: Mapped[int] = mapped_column(Integer, default=0)
    bit_depth: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float] = mapped_column(default=0.0)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
