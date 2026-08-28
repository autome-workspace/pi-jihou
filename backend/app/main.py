"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import api_router
from app.config import settings
from app.scheduler.executor import playback_executor
from app.scheduler.scheduler import scheduler
from app.time.clock_monitor import clock_monitor
from app.time.time_provider import time_provider
from app.voice.prefetch import prefetch_scheduler

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def _prepare_database() -> None:
    """Create data directories and apply pending migrations.

    Runs before the scheduler starts so the SQLite database and its parent
    directory always exist, regardless of how the container was started.
    """
    for directory in (
        settings.database_dir,
        settings.audio_dir,
        settings.voice_cache_dir,
        settings.backup_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    from alembic import command
    from alembic.config import Config as AlembicConfig

    base = Path(__file__).resolve().parent.parent
    cfg = AlembicConfig(str(base / "alembic.ini"))
    cfg.set_main_option("script_location", str(base / "alembic"))
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _prepare_database()
    await playback_executor.start()
    await scheduler.start()
    await prefetch_scheduler.start()
    await clock_monitor.start()
    logger.info("Application started (v%s)", __version__)
    yield
    await clock_monitor.stop()
    await prefetch_scheduler.stop()
    await scheduler.stop()
    await playback_executor.stop()


app = FastAPI(title="Raspberry Pi Audio Scheduler", version=__version__, lifespan=lifespan)

# MVP assumes LAN-only usage; CORS is open to simplify local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root() -> dict:
    return {"name": "raspi-audio-scheduler", "version": __version__}


async def _build_status() -> dict:
    return {
        "time": time_provider.now().isoformat(),
        "ntp": clock_monitor.status(),
        "scheduler_running": scheduler._running,
        "playing": playback_executor.is_playing,
    }


@app.websocket("/ws")
async def websocket_status(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(await _build_status())
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
