"""Time endpoints."""

from fastapi import APIRouter

from app.schemas.system import TimeStatus
from app.time.clock_monitor import clock_monitor

router = APIRouter(prefix="/time", tags=["time"])


@router.get("", response_model=TimeStatus)
async def get_time() -> TimeStatus:
    return TimeStatus(**clock_monitor.status())


@router.get("/status", response_model=TimeStatus)
async def get_status() -> TimeStatus:
    return TimeStatus(**clock_monitor.status())


@router.post("/sync", response_model=TimeStatus)
async def sync_now() -> TimeStatus:
    await clock_monitor.sync_once()
    return TimeStatus(**clock_monitor.status())
