"""System endpoints: health and event logs."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.audio.client import audio_agent_client
from app.database.session import get_db
from app.models import NtpState, PlaybackHistory, Schedule, SystemEvent
from app.schemas.system import HealthResponse
from app.scheduler.rules import next_occurrence
from app.scheduler.scheduler import scheduler
from app.time.time_provider import time_provider
from app.voice.voicevox import voicevox_client

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    audio_agent_ok = await audio_agent_client.health()
    voicevox_ok = await voicevox_client.health()
    ntp_ok = time_provider.state != NtpState.UNSYNCHRONIZED
    ok = audio_agent_ok and voicevox_ok and ntp_ok
    return HealthResponse(
        status="ok" if ok else "degraded",
        scheduler=scheduler._running,
        ntp=ntp_ok,
        audio_agent=audio_agent_ok,
        voicevox=voicevox_ok,
    )


@router.get("/events")
def list_events(
    limit: int = 200, db: Session = Depends(get_db)
) -> list[dict]:
    events = db.query(SystemEvent).order_by(SystemEvent.created_at.desc()).limit(limit).all()
    return [
        {
            "id": e.id,
            "level": e.level,
            "category": e.category,
            "message": e.message,
            "created_at": e.created_at,
        }
        for e in events
    ]


@router.get("/history")
def playback_history(limit: int = 50, db: Session = Depends(get_db)) -> list[dict]:
    rows = (
        db.query(PlaybackHistory)
        .order_by(PlaybackHistory.started_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "schedule_id": r.schedule_id,
            "scheduled_at": r.scheduled_at,
            "started_at": r.started_at,
            "finished_at": r.finished_at,
            "delay_ms": r.delay_ms,
            "audio_device": r.audio_device,
            "result": r.result,
            "error_message": r.error_message,
        }
        for r in rows
    ]


@router.get("/next-playback")
def next_playback(db: Session = Depends(get_db)) -> dict | None:
    now = time_provider.now()
    best_schedule: Schedule | None = None
    best_time = None
    for schedule in db.query(Schedule).filter(Schedule.enabled.is_(True)).all():
        for rule in schedule.rules:
            t = next_occurrence(rule, now)
            if t and (best_time is None or t < best_time):
                best_time = t
                best_schedule = schedule
    if best_schedule is None or best_time is None:
        return None
    return {
        "schedule_id": best_schedule.id,
        "name": best_schedule.name,
        "scheduled_at": best_time,
    }
