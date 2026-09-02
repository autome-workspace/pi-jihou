"""Scheduler loop.

Polls at a 100–250 ms cadence, computes the next occurrence of each enabled
schedule, and fires due events. Deduplication is handled via ``schedule_events``
so the same event is never played twice even if the clock moves.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models import AudioType, ConflictPolicy, Schedule, ScheduleEvent
from app.scheduler.executor import PlaybackItem, playback_executor
from app.scheduler.rules import next_occurrence
from app.services.voice_service import expand_template_text
from app.time.time_provider import TimeProvider, time_provider
from app.voice import cache as cache_mod
from app.voice.voicevox import voicevox_client

logger = logging.getLogger(__name__)

TICK_INTERVAL = 0.2  # seconds (100–250 ms per design)
LOOKBACK_WINDOW = timedelta(seconds=2)


class Scheduler:
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
                await self._tick()
            except Exception:  # noqa: BLE001 - keep the loop alive
                logger.exception("Scheduler tick failed")
            await asyncio.sleep(TICK_INTERVAL)

    async def _tick(self) -> None:
        now = self.provider.now_local()
        db = SessionLocal()
        try:
            schedules = db.query(Schedule).filter(Schedule.enabled.is_(True)).all()
            due = [
                (schedule, t)
                for schedule in schedules
                for rule in schedule.rules
                if (t := next_occurrence(rule, now - LOOKBACK_WINDOW)) and t <= now
            ]
        finally:
            db.close()

        for schedule, target in due:
            await self._fire(schedule.id, target)

    async def _fire(self, schedule_id: str, target: datetime) -> None:
        db = SessionLocal()
        try:
            already = (
                db.query(ScheduleEvent)
                .filter(
                    ScheduleEvent.schedule_id == schedule_id,
                    ScheduleEvent.scheduled_at == target,
                )
                .first()
            )
            if already:
                return

            event = ScheduleEvent(
                schedule_id=schedule_id,
                scheduled_at=target,
                executed_at=self.provider.now_local(),
                result="pending",
            )
            db.add(event)
            db.commit()

            schedule = db.get(Schedule, schedule_id)
            if schedule is None or not schedule.enabled:
                return

            item = await self._build_item(db, schedule, target)
            if item is None:
                event.result = "skipped"
                db.commit()
                logger.warning("Schedule %s skipped (no audio source)", schedule.name)
                return

            await playback_executor.submit(
                item, ConflictPolicy(schedule.conflict_policy)
            )
            event.result = "queued"
            db.commit()
        finally:
            db.close()

    async def _build_item(
        self, db: Session, schedule: Schedule, target: datetime
    ) -> PlaybackItem | None:
        audio_device = ""  # resolved by the audio agent's current device

        # Continuous (絶え間なく) repeat: an interval rule with 0 minutes loops
        # playback back-to-back until the window's end time.
        loop_until: datetime | None = None
        for rule in schedule.rules:
            if (
                rule.rule_type == "interval"
                and (rule.interval_minutes or 0) == 0
                and rule.end_time is not None
            ):
                loop_until = datetime.combine(target.date(), rule.end_time)
                break

        if schedule.audio_type == AudioType.FILE.value:
            from app.models import AudioFile

            audio = db.get(AudioFile, schedule.audio_file_id) if schedule.audio_file_id else None
            if audio is None:
                return None
            return PlaybackItem(
                schedule_id=schedule.id,
                audio_file_id=audio.id,
                voice_cache_id=None,
                path=audio.playback_path or audio.original_path,
                priority=schedule.priority,
                scheduled_at=target,
                audio_device=audio_device,
                loop_until=loop_until,
            )

        # VOICEVOX template: reuse the prefetched cache. Do not generate on the
        # critical path at playback time.
        if schedule.voice_template_id:
            from app.models import VoiceCache, VoiceTemplate

            template = db.get(VoiceTemplate, schedule.voice_template_id)
            if template is None:
                return None
            try:
                expanded_text = expand_template_text(db, template, self.provider.now_local())
                version = await voicevox_client.version()
            except Exception:  # noqa: BLE001
                version = ""
            parameters = {
                "speed": template.speed,
                "pitch": template.pitch,
                "intonation": template.intonation,
                "volume": template.volume,
                "pre_silence_ms": template.pre_silence_ms,
                "post_silence_ms": template.post_silence_ms,
            }
            cache_key = cache_mod.compute_cache_key(
                template.speaker_id, template.style_id, parameters, expanded_text, version
            )
            entry = db.query(VoiceCache).filter(VoiceCache.cache_key == cache_key).one_or_none()
            if entry is None or not cache_mod.cache_path_for_key(cache_key).exists():
                logger.error("Voice cache miss for schedule %s at playback time", schedule.name)
                return None
            return PlaybackItem(
                schedule_id=schedule.id,
                audio_file_id=None,
                voice_cache_id=entry.id,
                path=entry.wav_path,
                priority=schedule.priority,
                scheduled_at=target,
                audio_device=audio_device,
                loop_until=loop_until,
            )

        return None

    async def run_now(self, schedule_id: str) -> bool:
        """Immediately queue a schedule for playback (used by the run endpoint)."""
        now = self.provider.now_local()
        db = SessionLocal()
        try:
            schedule = db.get(Schedule, schedule_id)
            if schedule is None:
                return False
            item = await self._build_item(db, schedule, now)
            if item is None:
                return False
            await playback_executor.submit(item, ConflictPolicy(schedule.conflict_policy))
            return True
        finally:
            db.close()


scheduler = Scheduler(time_provider)
