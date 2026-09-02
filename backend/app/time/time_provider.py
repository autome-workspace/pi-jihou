"""Application time provider.

The scheduler never reads the OS wall clock directly. Instead it asks this
provider, which derives the current time from the last NTP synchronization:

    application_time = base_ntp_time + (CLOCK_MONOTONIC - base_monotonic)

This keeps playback timing stable even if the OS clock is stepped or adjusted.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.config import settings
from app.models.enums import NtpState


class TimeProvider:
    def __init__(self) -> None:
        self._base_ntp_time: datetime | None = None
        self._base_monotonic: float = 0.0
        self._state: NtpState = NtpState.UNSYNCHRONIZED
        self._offset_ms: float = 0.0
        self._last_sync: datetime | None = None
        self._last_sync_server: str = ""

    @property
    def state(self) -> NtpState:
        return self._state

    @property
    def offset_ms(self) -> float:
        return self._offset_ms

    @property
    def last_sync(self) -> datetime | None:
        return self._last_sync

    @property
    def last_sync_server(self) -> str:
        return self._last_sync_server

    def apply_offset(self, offset_ms: float, latency_ms: float, server: str) -> None:
        """Record an NTP offset measurement and rebase the monotonic anchor."""
        now_wall = datetime.now(timezone.utc)
        self._base_ntp_time = now_wall + timedelta(milliseconds=offset_ms)
        self._base_monotonic = time.monotonic()
        self._offset_ms = offset_ms
        self._last_sync = now_wall
        self._last_sync_server = server
        self._state = NtpState.SYNCHRONIZED

    def mark_degraded(self) -> None:
        if self._state == NtpState.SYNCHRONIZED:
            self._state = NtpState.DEGRADED

    def mark_unsynchronized(self) -> None:
        self._state = NtpState.UNSYNCHRONIZED

    def now(self) -> datetime:
        """Return the current application time (UTC)."""
        if self._base_ntp_time is None:
            return datetime.now(timezone.utc)
        elapsed = time.monotonic() - self._base_monotonic
        return self._base_ntp_time + timedelta(seconds=elapsed)

    def now_naive(self) -> datetime:
        """Return the current application time as a naive datetime (UTC)."""
        return self.now().replace(tzinfo=None)

    def now_local(self) -> datetime:
        """Return the current application time as a naive local datetime.

        Schedules are entered as local wall-clock times, so the scheduler and
        next-playback computation must use local time. Falls back to the system
        timezone when ``APP_TIMEZONE`` is unset.
        """
        utc = self.now()
        if settings.app_timezone:
            return utc.astimezone(ZoneInfo(settings.app_timezone)).replace(tzinfo=None)
        return utc.astimezone().replace(tzinfo=None)


# Process-wide singleton.
time_provider = TimeProvider()
