"""Database session and engine management."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings


def _make_engine():
    if settings.resolved_database_url.startswith("sqlite"):
        return create_engine(
            settings.resolved_database_url,
            connect_args={"check_same_thread": False},
        )
    return create_engine(settings.resolved_database_url)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
