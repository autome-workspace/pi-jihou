"""Settings endpoints (key/value settings table)."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Setting

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingIn(BaseModel):
    value: str


@router.get("")
def get_settings(db: Session = Depends(get_db)) -> dict[str, str]:
    rows = db.query(Setting).all()
    return {row.key: row.value for row in rows}


@router.put("/{key}")
def set_setting(key: str, data: SettingIn, db: Session = Depends(get_db)) -> dict[str, str]:
    row = db.get(Setting, key)
    if row is None:
        row = Setting(key=key, value=data.value)
        db.add(row)
    else:
        row.value = data.value
    db.commit()
    return {"key": key, "value": data.value}


@router.delete("/{key}")
def delete_setting(key: str, db: Session = Depends(get_db)) -> dict[str, str]:
    row = db.get(Setting, key)
    if row is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    db.delete(row)
    db.commit()
    return {"deleted": key}
