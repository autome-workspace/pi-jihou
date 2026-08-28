"""ORM models package. Importing this module registers all tables on Base.metadata."""

from app.models.audio import AudioFile
from app.models.base import Base
from app.models.enums import (
    AudioType,
    ConflictPolicy,
    GenerationStrategy,
    NtpState,
    PlaybackResult,
    QueueStatus,
    ScheduleType,
    VariableType,
)
from app.models.playback import PlaybackHistory, PlaybackQueue
from app.models.schedule import Schedule, ScheduleEvent, ScheduleRule
from app.models.system import NtpHistory, Setting, SystemEvent
from app.models.voice import VoiceCache, VoiceTemplate, VoiceVariable

__all__ = [
    "Base",
    "AudioFile",
    "Schedule",
    "ScheduleRule",
    "ScheduleEvent",
    "PlaybackQueue",
    "PlaybackHistory",
    "VoiceTemplate",
    "VoiceVariable",
    "VoiceCache",
    "Setting",
    "NtpHistory",
    "SystemEvent",
    "ScheduleType",
    "ConflictPolicy",
    "AudioType",
    "VariableType",
    "GenerationStrategy",
    "PlaybackResult",
    "QueueStatus",
    "NtpState",
]
