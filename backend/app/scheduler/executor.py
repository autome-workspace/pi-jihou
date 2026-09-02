"""Playback executor: a single unified playback queue.

Handles conflict policy (queue / interrupt / skip) and dispatches audio to the
Audio Agent, recording playback history.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime

from app.audio.client import audio_agent_client
from app.database.session import SessionLocal
from app.models import (
    ConflictPolicy,
    PlaybackHistory,
    PlaybackQueue,
    PlaybackResult,
    QueueStatus,
)

logger = logging.getLogger(__name__)


def _now() -> datetime:
    """Naive local timestamp (schedules/timestamps are local wall-clock)."""
    return datetime.now().astimezone().replace(tzinfo=None)


@dataclass
class PlaybackItem:
    schedule_id: str | None
    audio_file_id: str | None
    voice_cache_id: str | None
    path: str
    priority: int = 10
    scheduled_at: datetime | None = None
    queue_record_id: str | None = None
    audio_device: str = ""
    # Continuous (絶え間なく) playback: loop until this time.
    loop_until: datetime | None = None
    created_at: datetime = field(default_factory=_now)


class PlaybackExecutor:
    def __init__(self) -> None:
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._playing = False
        self._current: PlaybackItem | None = None
        self._worker_task: asyncio.Task | None = None
        self._stop_requested = False
        self._seq = 0

    async def start(self) -> None:
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

    @property
    def is_playing(self) -> bool:
        return self._playing

    async def submit(
        self,
        item: PlaybackItem,
        conflict_policy: ConflictPolicy = ConflictPolicy.QUEUE,
    ) -> str:
        """Enqueue an item according to the conflict policy."""
        db = SessionLocal()
        try:
            record = PlaybackQueue(
                schedule_id=item.schedule_id,
                audio_file_id=item.audio_file_id,
                voice_cache_id=item.voice_cache_id,
                priority=item.priority,
                status=QueueStatus.PENDING.value,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            item.queue_record_id = record.id
        finally:
            db.close()

        self._seq += 1
        if conflict_policy == ConflictPolicy.INTERRUPT:
            await self._request_stop()
            # Higher-priority items jump the queue; use a very negative
            # sequence so they are handled before anything already queued.
            await self._queue.put((-10_000_000 - item.priority, self._seq, item))
            return record.id

        if conflict_policy == ConflictPolicy.SKIP and self._playing:
            self._mark_queue(record.id, QueueStatus.SKIPPED)
            return record.id

        # QUEUE (default): lower sequence number = higher priority. The
        # monotonic counter guarantees a total order when priorities tie.
        sequence = -item.priority
        await self._queue.put((sequence, self._seq, item))
        return record.id

    async def _request_stop(self) -> None:
        self._stop_requested = True

    async def _worker(self) -> None:
        while True:
            _, _, item = await self._queue.get()
            self._stop_requested = False
            await self._play(item)

    async def _play(self, item: PlaybackItem) -> None:
        self._playing = True
        self._current = item
        started_at = _now()
        delay_ms = 0.0
        if item.scheduled_at:
            delay_ms = (started_at - item.scheduled_at).total_seconds() * 1000.0

        self._mark_queue(item.queue_record_id, QueueStatus.PLAYING)
        result = PlaybackResult.SUCCESS.value
        error = ""

        try:
            if item.loop_until is not None:
                # 絶え間なく repeat: replay back-to-back until loop_until. Each
                # /play call blocks until the audio finishes, so this loops
                # without dead time being added by us.
                while _now() < item.loop_until:
                    await audio_agent_client.play(item.path, item.audio_device or None)
                    await asyncio.sleep(0.2)
            else:
                await audio_agent_client.play(item.path, item.audio_device or None)
        except Exception as exc:  # noqa: BLE001
            result = PlaybackResult.FAILED.value
            error = str(exc)
            logger.error("Playback failed: %s", exc)

        finished_at = _now()
        self._record_history(item, started_at, finished_at, delay_ms, result, error)
        self._mark_queue(item.queue_record_id, QueueStatus.DONE)
        self._playing = False
        self._current = None

    def _mark_queue(self, queue_id: str | None, status: QueueStatus) -> None:
        if not queue_id:
            return
        db = SessionLocal()
        try:
            record = db.get(PlaybackQueue, queue_id)
            if record:
                record.status = status.value
                db.commit()
        finally:
            db.close()

    def _record_history(
        self,
        item: PlaybackItem,
        started_at: datetime,
        finished_at: datetime,
        delay_ms: float,
        result: str,
        error: str,
    ) -> None:
        db = SessionLocal()
        try:
            db.add(
                PlaybackHistory(
                    schedule_id=item.schedule_id,
                    audio_file_id=item.audio_file_id,
                    voice_cache_id=item.voice_cache_id,
                    scheduled_at=item.scheduled_at or started_at,
                    started_at=started_at,
                    finished_at=finished_at,
                    delay_ms=delay_ms,
                    audio_device=item.audio_device,
                    result=result,
                    error_message=error,
                )
            )
            db.commit()
        finally:
            db.close()


playback_executor = PlaybackExecutor()
