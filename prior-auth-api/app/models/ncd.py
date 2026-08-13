"""SQLAlchemy model for NCD.

⚠️  SCHEMA NOTE: Update when the data team delivers the final schema.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class NCD(Base):
    __tablename__ = "ncds"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    manual_section: Mapped[str | None] = mapped_column(String(50), nullable=True)
    decision: Mapped[str | None] = mapped_column(String(100), nullable=True)
