"""Audio file schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AudioFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    original_filename: str
    format: str
    sample_rate: int
    channels: int
    bit_depth: int
    duration_seconds: float
    size_bytes: int
    created_at: datetime


class AudioPlayResult(BaseModel):
    audio_id: str
    status: str
    message: str = ""
