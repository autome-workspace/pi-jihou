"""Schedule, schedule rule and fired-event models."""

from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPkMixin
from app.models.enums import AudioType, ConflictPolicy, ScheduleType


class Schedule(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "schedules"

    name: Mapped[str] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    volume: Mapped[int] = mapped_column(Integer, default=80)
    priority: Mapped[int] = mapped_column(Integer, default=10)
    conflict_policy: Mapped[str] = mapped_column(String(16), default=ConflictPolicy.QUEUE.value)
    audio_type: Mapped[str] = mapped_column(String(16), default=AudioType.FILE.value)

    audio_file_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("audio_files.id"), nullable=True
    )
    voice_template_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("voice_templates.id"), nullable=True
    )

    rules: Mapped[list["ScheduleRule"]] = relationship(
        back_populates="schedule", cascade="all, delete-orphan"
    )


class ScheduleRule(Base, UUIDPkMixin):
    __tablename__ = "schedule_rules"

    schedule_id: Mapped[str] = mapped_column(String(36), ForeignKey("schedules.id"))
    rule_type: Mapped[str] = mapped_column(String(16), default=ScheduleType.DAILY.value)
    time: Mapped[time | None] = mapped_column(Time, nullable=True)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    interval_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    days_of_week: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    specific_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    cron_expression: Mapped[str | None] = mapped_column(String(128), nullable=True)

    schedule: Mapped["Schedule"] = relationship(back_populates="rules")


class ScheduleEvent(Base, UUIDPkMixin):
    """Record that a schedule was fired for a given target time (dedup)."""

    __tablename__ = "schedule_events"

    schedule_id: Mapped[str] = mapped_column(String(36), ForeignKey("schedules.id"))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[str] = mapped_column(String(16), default="pending")
