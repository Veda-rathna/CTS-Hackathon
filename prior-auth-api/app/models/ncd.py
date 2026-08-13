"""SQLAlchemy models for NCD.

Supports composite version primary keys.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKeyConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class NCD(Base):
    __tablename__ = "ncds"

    document_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    document_version: Mapped[int] = mapped_column(Integer, primary_key=True)

    document_display_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    publication_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    benefit_category: Mapped[str | None] = mapped_column(Text, nullable=True)

    item_service_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    indications_limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    reasons_for_denial: Mapped[str | None] = mapped_column(Text, nullable=True)
    cross_reference: Mapped[str | None] = mapped_column(Text, nullable=True)

    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    implementation_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    revision_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    other_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Added decision parsed value for policy engine
    decision: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    hcpcs_codes: Mapped[list["NCDHCPCSCode"]] = relationship(
        "NCDHCPCSCode", back_populates="ncd", cascade="all, delete-orphan"
    )


class LCDNCDAssociation(Base):
    __tablename__ = "lcd_ncd_associations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lcd_id: Mapped[str] = mapped_column(String(50))
    lcd_version: Mapped[int] = mapped_column(Integer)
    ncd_id: Mapped[str] = mapped_column(String(50))
    ncd_version: Mapped[int] = mapped_column(Integer)

    __table_args__ = (
        ForeignKeyConstraint(
            ["lcd_id", "lcd_version"],
            ["lcds.lcd_id", "lcds.lcd_version"],
        ),
        ForeignKeyConstraint(
            ["ncd_id", "ncd_version"],
            ["ncds.document_id", "ncds.document_version"],
        ),
    )


class NCDHCPCSCode(Base):
    __tablename__ = "ncd_hcpcs_codes"

    ncd_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    ncd_version: Mapped[int] = mapped_column(Integer, primary_key=True)
    hcpcs_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["ncd_id", "ncd_version"],
            ["ncds.document_id", "ncds.document_version"],
        ),
    )

    ncd: Mapped["NCD"] = relationship("NCD", back_populates="hcpcs_codes")
