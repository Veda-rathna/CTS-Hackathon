"""SQLAlchemy model for Jurisdiction.

⚠️  SCHEMA NOTE: Update when final PostgreSQL schema is delivered.
"""
from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Jurisdiction(Base):
    __tablename__ = "jurisdictions"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Comma-separated state abbreviations — will be normalised by the data team
    states: Mapped[str | None] = mapped_column(Text, nullable=True)
    contractor_id: Mapped[str | None] = mapped_column(
        ForeignKey("contractors.id"), nullable=True
    )

    # Relationships
    contractor: Mapped["Contractor | None"] = relationship(  # type: ignore[name-defined]
        "Contractor", back_populates="jurisdictions"
    )
