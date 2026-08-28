"""System / time / device / health schemas."""

from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    scheduler: bool = False
    ntp: bool = False
    audio_agent: bool = False
    voicevox: bool = False


class TimeStatus(BaseModel):
    state: str
    current_time: datetime
    ntp_offset_ms: float = 0.0
    last_sync: datetime | None = None
    servers: list[str] = []


class AudioDevice(BaseModel):
    id: str
    name: str
    description: str = ""
    default: bool = False


class AudioDeviceList(BaseModel):
    devices: list[AudioDevice]
    current: str | None = None
