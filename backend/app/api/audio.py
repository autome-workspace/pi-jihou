"""Audio file endpoints: upload, list, delete, play."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import AudioFile
from app.schemas.audio import AudioFileOut, AudioPlayResult
from app.scheduler.executor import PlaybackItem, playback_executor
from app.services import audio_service

router = APIRouter(prefix="/audio", tags=["audio"])


@router.get("", response_model=list[AudioFileOut])
def list_audio(db: Session = Depends(get_db)) -> list[AudioFile]:
    return db.query(AudioFile).order_by(AudioFile.created_at.desc()).all()


@router.post("", response_model=AudioFileOut, status_code=201)
async def upload_audio(
    file: UploadFile = File(...), name: str | None = None, db: Session = Depends(get_db)
) -> AudioFile:
    try:
        return await audio_service.store_upload(db, file, name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{audio_id}")
def delete_audio(audio_id: str, db: Session = Depends(get_db)) -> dict:
    record = db.get(AudioFile, audio_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Audio not found")
    audio_service.delete_audio(db, record)
    return {"deleted": audio_id}


@router.post("/{audio_id}/play", response_model=AudioPlayResult)
async def play_audio(audio_id: str, db: Session = Depends(get_db)) -> AudioPlayResult:
    record = db.get(AudioFile, audio_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Audio not found")
    item = PlaybackItem(
        schedule_id=None,
        audio_file_id=record.id,
        voice_cache_id=None,
        path=record.playback_path or record.original_path,
        priority=10,
    )
    await playback_executor.submit(item)
    return AudioPlayResult(audio_id=audio_id, status="queued")
