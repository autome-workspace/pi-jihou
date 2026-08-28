"""System-level models: settings, NTP history, system events."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPkMixin


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(String(2048), default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow()
    )


class NtpHistory(Base, UUIDPkMixin):
    __tablename__ = "ntp_history"

    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    server: Mapped[str] = mapped_column(String(255), default="")
    offset_ms: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str] = mapped_column(String(1024), default="")


class SystemEvent(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "system_events"

    level: Mapped[str] = mapped_column(String(16), default="INFO")
    category: Mapped[str] = mapped_column(String(32), default="system")
    message: Mapped[str] = mapped_column(String(2048))
