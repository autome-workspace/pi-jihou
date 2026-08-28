"""Schedule endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Schedule
from app.schemas.schedule import ScheduleCreate, ScheduleOut, ScheduleRunResult, ScheduleUpdate
from app.scheduler.scheduler import scheduler
from app.services import schedule_service

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("", response_model=list[ScheduleOut])
def list_schedules(db: Session = Depends(get_db)) -> list[Schedule]:
    return db.query(Schedule).order_by(Schedule.created_at.desc()).all()


@router.post("", response_model=ScheduleOut, status_code=201)
def create_schedule(data: ScheduleCreate, db: Session = Depends(get_db)) -> Schedule:
    return schedule_service.create_schedule(db, data)


@router.get("/{schedule_id}", response_model=ScheduleOut)
def get_schedule(schedule_id: str, db: Session = Depends(get_db)) -> Schedule:
    schedule = db.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.put("/{schedule_id}", response_model=ScheduleOut)
def update_schedule(
    schedule_id: str, data: ScheduleUpdate, db: Session = Depends(get_db)
) -> Schedule:
    schedule = db.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule_service.update_schedule(db, schedule, data)


@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: str, db: Session = Depends(get_db)) -> dict:
    schedule = db.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(schedule)
    db.commit()
    return {"deleted": schedule_id}


def _set_enabled(schedule_id: str, enabled: bool, db: Session) -> dict:
    schedule = db.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    schedule.enabled = enabled
    db.commit()
    return {"id": schedule_id, "enabled": enabled}


@router.post("/{schedule_id}/enable")
def enable_schedule(schedule_id: str, db: Session = Depends(get_db)) -> dict:
    return _set_enabled(schedule_id, True, db)


@router.post("/{schedule_id}/disable")
def disable_schedule(schedule_id: str, db: Session = Depends(get_db)) -> dict:
    return _set_enabled(schedule_id, False, db)


@router.post("/{schedule_id}/run", response_model=ScheduleRunResult)
async def run_schedule(schedule_id: str) -> ScheduleRunResult:
    ok = await scheduler.run_now(schedule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Schedule not found or has no audio")
    return ScheduleRunResult(schedule_id=schedule_id, status="queued")
