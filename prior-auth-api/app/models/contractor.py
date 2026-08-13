"""SQLAlchemy model for Contractors.

Maps exactly to Contractor.csv fields.
"""
from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Contractor(Base):
    __tablename__ = "contractors"

    contractor_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    contract_type_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contract_subtype_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contractor_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contract_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contractor_name: Mapped[str | None] = mapped_column(Text, nullable=True)
