"""Schedule schemas."""

from datetime import date, datetime, time as time_type

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AudioType, ConflictPolicy, ScheduleType


class ScheduleRuleBase(BaseModel):
    rule_type: ScheduleType = ScheduleType.DAILY
    time: time_type | None = None
    start_time: time_type | None = None
    end_time: time_type | None = None
    interval_minutes: int | None = Field(default=None, ge=0)
    days_of_week: list[int] | None = None
    specific_date: date | None = None
    cron_expression: str | None = None


class ScheduleRuleOut(ScheduleRuleBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


class ScheduleBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    enabled: bool = True
    volume: int = Field(default=80, ge=0, le=100)
    priority: int = Field(default=10, ge=0, le=1000)
    conflict_policy: ConflictPolicy = ConflictPolicy.QUEUE
    audio_type: AudioType = AudioType.FILE
    audio_file_id: str | None = None
    voice_template_id: str | None = None
    rules: list[ScheduleRuleBase] = []


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    enabled: bool | None = None
    volume: int | None = Field(default=None, ge=0, le=100)
    priority: int | None = Field(default=None, ge=0, le=1000)
    conflict_policy: ConflictPolicy | None = None
    audio_type: AudioType | None = None
    audio_file_id: str | None = None
    voice_template_id: str | None = None
    rules: list[ScheduleRuleBase] | None = None


class ScheduleOut(ScheduleBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    rules: list[ScheduleRuleOut] = []
    created_at: datetime
    updated_at: datetime


class ScheduleRunResult(BaseModel):
    schedule_id: str
    status: str
    message: str = ""
