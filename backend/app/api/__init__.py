"""API routers aggregated under /api/v1."""

from fastapi import APIRouter

from app.api import audio, devices, schedules, settings, system, time, voicevox

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(system.router)
api_router.include_router(schedules.router)
api_router.include_router(audio.router)
api_router.include_router(devices.router)
api_router.include_router(voicevox.router)
api_router.include_router(time.router)
api_router.include_router(settings.router)
