"""Database session factory.

Creates a single SQLAlchemy engine and sessionmaker at module import time.
Repository classes receive a session via the ``get_db`` FastAPI dependency.

NOTE: This module is only used when ``USE_MOCK_REPOSITORIES=false``.
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_settings = get_settings()

engine = create_engine(
    _settings.database_url_normalized,
    pool_pre_ping=True,        # detect stale connections
    pool_recycle=300,          # recycle connections every 5 min for Neon / RDS Postgres pooler
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    echo=False,                # set True to see SQL in development
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session.

    Ensures the session is always closed even if an exception is raised.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Verify that the database is reachable.

    Returns True on success, False on failure.
    Used by the health/db endpoint.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("Database connectivity check failed: %s", exc)
        return False
