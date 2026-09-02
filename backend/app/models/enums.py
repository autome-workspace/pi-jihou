"""Enums shared across models and schemas."""

import enum


class ScheduleType(str, enum.Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKDAYS = "weekdays"
    WEEKLY = "weekly"
    DATE = "date"
    CRON = "cron"
    INTERVAL = "interval"


class ConflictPolicy(str, enum.Enum):
    QUEUE = "queue"
    INTERRUPT = "interrupt"
    SKIP = "skip"


class AudioType(str, enum.Enum):
    FILE = "file"
    VOICE = "voice"


class VariableType(str, enum.Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"


class GenerationStrategy(str, enum.Enum):
    BEFORE_PLAYBACK = "before_playback"
    DAILY = "daily"
    WHEN_VARIABLE_CHANGES = "when_variable_changes"
    FIXED_TIME = "fixed_time"


class PlaybackResult(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class QueueStatus(str, enum.Enum):
    PENDING = "pending"
    PLAYING = "playing"
    DONE = "done"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class NtpState(str, enum.Enum):
    SYNCHRONIZED = "synchronized"
    DEGRADED = "degraded"
    UNSYNCHRONIZED = "unsynchronized"
