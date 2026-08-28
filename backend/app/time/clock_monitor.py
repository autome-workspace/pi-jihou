"""Background NTP synchronization loop.

Queries the configured NTP servers periodically and keeps the
:class:`TimeProvider` in sync. Failures degrade the state but never stop the
scheduler.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from app.config import settings
from app.database.session import SessionLocal
from app.models import NtpHistory, NtpState
from app.time.ntp_client import query_async
from app.time.time_provider import TimeProvider, time_provider

logger = logging.getLogger(__name__)

_DEGRADED_AFTER_INTERVALS = 3


class ClockMonitor:
    def __init__(self, provider: TimeProvider) -> None:
        self.provider = provider
        self._servers = [
            settings.ntp_primary,
            settings.ntp_secondary,
            settings.ntp_tertiary,
        ]
        self._servers = [s for s in self._servers if s]
        self._running = False
        self._task: asyncio.Task | None = None

    async def sync_once(self) -> bool:
        """Try each configured server in order. Returns True on success."""
        for server in self._servers:
            try:
                offset, latency = await query_async(
                    server, timeout=settings.ntp_timeout
                )
            except Exception as exc:  # noqa: BLE001 - network errors vary
                self._record_history(server, success=False, error=str(exc))
                logger.warning("NTP sync failed against %s: %s", server, exc)
                continue

            self.provider.apply_offset(offset * 1000.0, latency * 1000.0, server)
            self._record_history(
                server,
                success=True,
                offset_ms=offset * 1000.0,
                latency_ms=latency * 1000.0,
            )
            logger.info("NTP synchronized via %s (offset %.1f ms)", server, offset * 1000)
            return True
        return False

    def _record_history(
        self,
        server: str,
        success: bool,
        offset_ms: float = 0.0,
        latency_ms: float = 0.0,
        error: str = "",
    ) -> None:
        try:
            db = SessionLocal()
            try:
                db.add(
                    NtpHistory(
                        synced_at=datetime.now(timezone.utc),
                        server=server,
                        offset_ms=offset_ms,
                        latency_ms=latency_ms,
                        success=success,
                        error_message=error,
                    )
                )
                db.commit()
            finally:
                db.close()
        except Exception:  # noqa: BLE001 - never crash the monitor on DB errors
            logger.exception("Failed to record NTP history")

    async def _run(self) -> None:
        while self._running:
            ok = await self.sync_once()
            if not ok:
                self._mark_offline_state()
            await asyncio.sleep(settings.ntp_interval)

    def _mark_offline_state(self) -> None:
        last = self.provider.last_sync
        if last is None:
            self.provider.mark_unsynchronized()
            return
        stale_for = (datetime.now(timezone.utc) - last).total_seconds()
        if stale_for > settings.ntp_interval * _DEGRADED_AFTER_INTERVALS:
            self.provider.mark_degraded()

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())
        # Perform an immediate sync attempt.
        await self.sync_once()

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    def status(self) -> dict:
        state: NtpState = self.provider.state
        return {
            "state": state.value,
            "current_time": self.provider.now(),
            "ntp_offset_ms": self.provider.offset_ms,
            "last_sync": self.provider.last_sync,
            "servers": self._servers,
        }


clock_monitor = ClockMonitor(time_provider)
