"""SQLAlchemy model for Jurisdictions.

Maps to Jurisdiction_With_States.csv fields.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Jurisdiction(Base):
    __tablename__ = "jurisdictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lcd_id: Mapped[str] = mapped_column(String(50), index=True)
    lcd_version: Mapped[int] = mapped_column(Integer)
    state_id: Mapped[int] = mapped_column(ForeignKey("states.state_id"), index=True)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    article_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    article_version: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationship to States
    state: Mapped["State"] = relationship("State")  # type: ignore[name-defined]
