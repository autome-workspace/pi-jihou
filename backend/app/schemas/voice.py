"""VOICEVOX template / variable / preview schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import GenerationStrategy, VariableType


class VoiceTemplateBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    template_text: str = ""
    speaker_id: int = 1
    style_id: int = 0
    speed: float = 1.0
    pitch: float = 0.0
    intonation: float = 1.0
    volume: float = 1.0
    pre_silence_ms: int = 0
    post_silence_ms: int = 0
    generation_strategy: GenerationStrategy = GenerationStrategy.BEFORE_PLAYBACK


class VoiceTemplateCreate(VoiceTemplateBase):
    pass


class VoiceTemplateUpdate(BaseModel):
    name: str | None = None
    template_text: str | None = None
    speaker_id: int | None = None
    style_id: int | None = None
    speed: float | None = None
    pitch: float | None = None
    intonation: float | None = None
    volume: float | None = None
    pre_silence_ms: int | None = None
    post_silence_ms: int | None = None
    generation_strategy: GenerationStrategy | None = None


class VoiceTemplateOut(VoiceTemplateBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    updated_at: datetime


class PreviewRequest(BaseModel):
    text: str | None = None
    speaker_id: int | None = None
    style_id: int | None = None
    speed: float | None = None
    pitch: float | None = None
    intonation: float | None = None
    volume: float | None = None


class PreviewResponse(BaseModel):
    expanded_text: str
    wav_available: bool = False


class GenerateResponse(BaseModel):
    cache_key: str | None = None
    wav_path: str | None = None
    expanded_text: str = ""


class VoiceVariableBase(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    value_type: VariableType = VariableType.STRING
    value: str = ""


class VoiceVariableOut(VoiceVariableBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


class VoiceVariableUpdate(BaseModel):
    name: str | None = None
    value_type: VariableType | None = None
    value: str | None = None


class SpeakerInfo(BaseModel):
    name: str
    speaker_uuid: str
    styles: list[dict] = []
