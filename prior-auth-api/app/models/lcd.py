"""SQLAlchemy models for LCD and its code tables.

⚠️  SCHEMA NOTE: Update when the data team delivers the final schema.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class LCD(Base):
    __tablename__ = "lcds"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    jurisdiction_id: Mapped[str | None] = mapped_column(
        ForeignKey("jurisdictions.id"), nullable=True, index=True
    )
    contractor_id: Mapped[str | None] = mapped_column(
        ForeignKey("contractors.id"), nullable=True, index=True
    )
    # Article IDs stored as comma-separated string; update if data team uses a join table
    associated_article_ids: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    jurisdiction: Mapped["Jurisdiction | None"] = relationship("Jurisdiction")  # type: ignore[name-defined]
    contractor: Mapped["Contractor | None"] = relationship("Contractor")  # type: ignore[name-defined]
    hcpcs_codes: Mapped[list["LCDHCPCSCode"]] = relationship(
        "LCDHCPCSCode", back_populates="lcd", cascade="all, delete-orphan"
    )
    icd10_covered: Mapped[list["LCDIcd10Covered"]] = relationship(
        "LCDIcd10Covered", back_populates="lcd", cascade="all, delete-orphan"
    )
    icd10_noncovered: Mapped[list["LCDIcd10NonCovered"]] = relationship(
        "LCDIcd10NonCovered", back_populates="lcd", cascade="all, delete-orphan"
    )


class LCDHCPCSCode(Base):
    __tablename__ = "lcd_hcpcs_codes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lcd_id: Mapped[str] = mapped_column(ForeignKey("lcds.id"), index=True)
    hcpcs_code: Mapped[str] = mapped_column(String(20), index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    lcd: Mapped["LCD"] = relationship("LCD", back_populates="hcpcs_codes")


class LCDIcd10Covered(Base):
    __tablename__ = "lcd_icd10_covered"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lcd_id: Mapped[str] = mapped_column(ForeignKey("lcds.id"), index=True)
    icd10_code: Mapped[str] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    lcd: Mapped["LCD"] = relationship("LCD", back_populates="icd10_covered")


class LCDIcd10NonCovered(Base):
    __tablename__ = "lcd_icd10_noncovered"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lcd_id: Mapped[str] = mapped_column(ForeignKey("lcds.id"), index=True)
    icd10_code: Mapped[str] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    lcd: Mapped["LCD"] = relationship("LCD", back_populates="icd10_noncovered")
