"""SQLAlchemy declarative base shared across all models."""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared base for all SQLAlchemy ORM models.

    All models inherit from this class so Alembic can discover them via
    ``app.db.base`` which imports every model module.
    """
    pass
