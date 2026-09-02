"""Voice prefetch scheduler.

Runs independently of the main scheduler. For upcoming schedules that use a
VOICEVOX template, it evaluates the template and generates the WAV cache ahead
of the playback time so the main scheduler only plays pre-generated audio.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from app.config import settings
from app.database.session import SessionLocal
from app.models import AudioType, Schedule
from app.scheduler.rules import next_occurrence
from app.services.voice_service import generate_for_template
from app.time.time_provider import TimeProvider, time_provider

logger = logging.getLogger(__name__)

PREFETCH_TICK = 30  # seconds


class PrefetchScheduler:
    def __init__(self, provider: TimeProvider) -> None:
        self.provider = provider
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        while self._running:
            try:
                await self._prefetch_due()
            except Exception:  # noqa: BLE001
                logger.exception("Prefetch tick failed")
            await asyncio.sleep(PREFETCH_TICK)

    async def _prefetch_due(self) -> None:
        now = self.provider.now_local()
        horizon = now + timedelta(seconds=settings.voice_prefetch_seconds)

        db = SessionLocal()
        try:
            schedules = (
                db.query(Schedule)
                .filter(
                    Schedule.enabled.is_(True),
                    Schedule.audio_type == AudioType.VOICE.value,
                    Schedule.voice_template_id.isnot(None),
                )
                .all()
            )
            targets = []
            for schedule in schedules:
                for rule in schedule.rules:
                    t = next_occurrence(rule, now)
                    if t and t <= horizon:
                        targets.append((schedule.id, t))
        finally:
            db.close()

        for schedule_id, _ in targets:
            await self._generate(schedule_id)

    async def _generate(self, schedule_id: str) -> None:
        from app.models import VoiceTemplate

        db = SessionLocal()
        try:
            schedule = db.get(Schedule, schedule_id)
            if schedule is None or schedule.voice_template_id is None:
                return
            template = db.get(VoiceTemplate, schedule.voice_template_id)
            if template is None:
                return
            await generate_for_template(db, template, self.provider.now_local())
        except Exception as exc:  # noqa: BLE001
            logger.warning("Prefetch generation failed for schedule %s: %s", schedule_id, exc)
        finally:
            db.close()


prefetch_scheduler = PrefetchScheduler(time_provider)
