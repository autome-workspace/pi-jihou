"""VOICEVOX status / speaker, voice template and variable endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import VoiceTemplate, VoiceVariable
from app.scheduler.executor import PlaybackItem, playback_executor
from app.schemas.voice import (
    GenerateResponse,
    PreviewRequest,
    PreviewResponse,
    VoiceTemplateCreate,
    VoiceTemplateOut,
    VoiceTemplateUpdate,
    VoiceVariableBase,
    VoiceVariableOut,
    VoiceVariableUpdate,
)
from app.services.voice_service import expand_template_text, generate_for_template
from app.time.time_provider import time_provider
from app.voice import cache as cache_mod
from app.voice.voicevox import voicevox_client

router = APIRouter(tags=["voicevox"])


# --- VOICEVOX engine status / speakers ---

@router.get("/voicevox/status")
async def voicevox_status() -> dict:
    healthy = await voicevox_client.health()
    version = ""
    if healthy:
        try:
            version = await voicevox_client.version()
        except Exception:  # noqa: BLE001
            pass
    return {"available": healthy, "version": version}


@router.get("/voicevox/speakers")
async def voicevox_speakers() -> list[dict]:
    try:
        return await voicevox_client.speakers()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"voicevox unavailable: {exc}")


# --- Voice templates ---

@router.get("/voice/templates", response_model=list[VoiceTemplateOut])
def list_templates(db: Session = Depends(get_db)) -> list[VoiceTemplate]:
    return db.query(VoiceTemplate).order_by(VoiceTemplate.created_at.desc()).all()


@router.post("/voice/templates", response_model=VoiceTemplateOut, status_code=201)
def create_template(
    data: VoiceTemplateCreate, db: Session = Depends(get_db)
) -> VoiceTemplate:
    template = VoiceTemplate(**data.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/voice/templates/{template_id}", response_model=VoiceTemplateOut)
def get_template(template_id: str, db: Session = Depends(get_db)) -> VoiceTemplate:
    template = db.get(VoiceTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put("/voice/templates/{template_id}", response_model=VoiceTemplateOut)
def update_template(
    template_id: str, data: VoiceTemplateUpdate, db: Session = Depends(get_db)
) -> VoiceTemplate:
    template = db.get(VoiceTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(template, field, value)
    db.commit()
    db.refresh(template)
    return template


@router.delete("/voice/templates/{template_id}")
def delete_template(template_id: str, db: Session = Depends(get_db)) -> dict:
    template = db.get(VoiceTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()
    return {"deleted": template_id}


@router.post("/voice/templates/{template_id}/preview", response_model=PreviewResponse)
async def preview_template(
    template_id: str, data: PreviewRequest, db: Session = Depends(get_db)
) -> PreviewResponse:
    template = db.get(VoiceTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    effective = VoiceTemplateCreate(
        name=template.name,
        template_text=data.text if data.text is not None else template.template_text,
        speaker_id=data.speaker_id if data.speaker_id is not None else template.speaker_id,
        style_id=data.style_id if data.style_id is not None else template.style_id,
        speed=data.speed if data.speed is not None else template.speed,
        pitch=data.pitch if data.pitch is not None else template.pitch,
        intonation=data.intonation if data.intonation is not None else template.intonation,
        volume=data.volume if data.volume is not None else template.volume,
        pre_silence_ms=template.pre_silence_ms,
        post_silence_ms=template.post_silence_ms,
    )
    preview_template = VoiceTemplate(**effective.model_dump())
    expanded_text = expand_template_text(db, preview_template, time_provider.now_local())
    cache_key, wav_path = await generate_for_template(db, preview_template, time_provider.now_local())

    # Play the generated audio through the Audio Agent (device playback).
    await playback_executor.submit(
        PlaybackItem(
            schedule_id=None,
            audio_file_id=None,
            voice_cache_id=None,
            path=wav_path,
            priority=10,
        )
    )

    return PreviewResponse(
        expanded_text=expanded_text,
        wav_available=True,
        cache_key=cache_key,
        wav_url=f"/api/v1/voice/cache/{cache_key}/wav",
    )


@router.post("/voice/templates/{template_id}/generate", response_model=GenerateResponse)
async def generate_template(
    template_id: str, db: Session = Depends(get_db)
) -> GenerateResponse:
    template = db.get(VoiceTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    expanded_text = expand_template_text(db, template, time_provider.now_local())
    cache_key, wav_path = await generate_for_template(db, template, time_provider.now_local())
    return GenerateResponse(
        cache_key=cache_key,
        wav_path=wav_path,
        expanded_text=expanded_text,
        wav_url=f"/api/v1/voice/cache/{cache_key}/wav",
    )


@router.get("/voice/cache/{cache_key}/wav")
def serve_cache_wav(cache_key: str) -> FileResponse:
    path = cache_mod.cache_path_for_key(cache_key)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Cache not found")
    return FileResponse(path, media_type="audio/wav")


# --- Variables ---

@router.get("/variables", response_model=list[VoiceVariableOut])
def list_variables(db: Session = Depends(get_db)) -> list[VoiceVariable]:
    return db.query(VoiceVariable).order_by(VoiceVariable.name.asc()).all()


@router.post("/variables", response_model=VoiceVariableOut, status_code=201)
def create_variable(data: VoiceVariableBase, db: Session = Depends(get_db)) -> VoiceVariable:
    variable = VoiceVariable(
        name=data.name, value_type=data.value_type.value, value=data.value
    )
    db.add(variable)
    db.commit()
    db.refresh(variable)
    return variable


@router.put("/variables/{variable_id}", response_model=VoiceVariableOut)
def update_variable(
    variable_id: str, data: VoiceVariableUpdate, db: Session = Depends(get_db)
) -> VoiceVariable:
    variable = db.get(VoiceVariable, variable_id)
    if variable is None:
        raise HTTPException(status_code=404, detail="Variable not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "value_type" and value is not None:
            value = value.value
        setattr(variable, field, value)
    db.commit()
    db.refresh(variable)
    return variable


@router.delete("/variables/{variable_id}")
def delete_variable(variable_id: str, db: Session = Depends(get_db)) -> dict:
    variable = db.get(VoiceVariable, variable_id)
    if variable is None:
        raise HTTPException(status_code=404, detail="Variable not found")
    db.delete(variable)
    db.commit()
    return {"deleted": variable_id}
