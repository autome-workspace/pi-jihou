"""Audio device endpoints (proxied to the Audio Agent)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.audio.client import audio_agent_client
from app.schemas.system import AudioDeviceList

router = APIRouter(prefix="/devices", tags=["devices"])


class DeviceId(BaseModel):
    id: str


@router.get("", response_model=AudioDeviceList)
async def list_devices() -> AudioDeviceList:
    try:
        devices = await audio_agent_client.get_devices()
        current = await audio_agent_client.get_current_device()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"audio agent unavailable: {exc}")
    return AudioDeviceList(
        devices=devices,
        current=current.get("id") if current else None,
    )


@router.post("/test")
async def test_device(data: DeviceId) -> dict:
    try:
        return await audio_agent_client.test(data.id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"test failed: {exc}")


@router.get("/current")
async def current_device() -> dict:
    try:
        return await audio_agent_client.get_current_device() or {}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"audio agent unavailable: {exc}")


@router.put("/current")
async def set_current_device(data: DeviceId) -> dict:
    try:
        return await audio_agent_client.set_current_device(data.id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"set device failed: {exc}")
