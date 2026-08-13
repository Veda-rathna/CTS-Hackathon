"""SQLAlchemy model for the Contractor (Medicare Administrative Contractor / MAC).

⚠️  SCHEMA NOTE: Column names reflect a best-guess mapping to the CMS data
    the data team is preparing.  Update this model when the final PostgreSQL
    schema is available — services and API routers will NOT need to change.
"""
from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Contractor(Base):
    __tablename__ = "contractors"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    jurisdictions: Mapped[list["Jurisdiction"]] = relationship(  # type: ignore[name-defined]
        "Jurisdiction", back_populates="contractor"
    )
