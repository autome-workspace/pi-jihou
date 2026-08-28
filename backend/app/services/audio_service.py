"""Audio file service: upload, normalize, list, delete."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.audio import normalization
from app.config import settings
from app.models import AudioFile


def _audio_dir_for(audio_id: str) -> Path:
    return settings.audio_dir / audio_id


async def store_upload(db: Session, file: UploadFile, name: str | None = None) -> AudioFile:
    if not normalization.is_supported(file.filename or ""):
        raise ValueError(f"unsupported audio format: {file.filename}")

    audio_id = str(uuid.uuid4())
    directory = _audio_dir_for(audio_id)
    directory.mkdir(parents=True, exist_ok=True)

    original_path = directory / f"original{Path(file.filename).suffix.lower()}"
    playback_path = directory / "playback.wav"

    with original_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    metadata = await normalization.normalize(original_path, playback_path)

    record = AudioFile(
        id=audio_id,
        name=name or Path(file.filename).stem,
        original_filename=file.filename or "",
        original_path=str(original_path),
        playback_path=str(playback_path),
        format="wav",
        sample_rate=metadata.get("sample_rate", 0),
        channels=metadata.get("channels", 0),
        bit_depth=metadata.get("bit_depth", 0),
        duration_seconds=metadata.get("duration_seconds", 0.0),
        size_bytes=metadata.get("size_bytes", 0),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def delete_audio(db: Session, record: AudioFile) -> None:
    directory = Path(record.original_path).parent
    db.delete(record)
    db.commit()
    if directory.exists():
        shutil.rmtree(directory, ignore_errors=True)
