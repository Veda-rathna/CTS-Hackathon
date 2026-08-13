"""SQLAlchemy models for LCD and its code tables.

Supports composite version primary keys.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKeyConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class LCD(Base):
    __tablename__ = "lcds"

    lcd_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    lcd_version: Mapped[int] = mapped_column(Integer, primary_key=True)

    display_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)

    cms_cov_policy: Mapped[str | None] = mapped_column(Text, nullable=True)
    indication: Mapped[str | None] = mapped_column(Text, nullable=True)

    diagnoses_support: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnoses_dont_support: Mapped[str | None] = mapped_column(Text, nullable=True)
    coding_guidelines: Mapped[str | None] = mapped_column(Text, nullable=True)
    doc_reqs: Mapped[str | None] = mapped_column(Text, nullable=True)

    summary_of_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_of_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    associated_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    bibliography: Mapped[str | None] = mapped_column(Text, nullable=True)
    appendices: Mapped[str | None] = mapped_column(Text, nullable=True)
    util_guide: Mapped[str | None] = mapped_column(Text, nullable=True)

    orig_det_eff_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    rev_eff_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    rev_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_retired: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    icd10_doc: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Note: associated_article_ids is kept as a comma-separated text list of article_ids
    # as an easy-access field populated by Related_Documents.csv
    associated_article_ids: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
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

    lcd_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    lcd_version: Mapped[int] = mapped_column(Integer, primary_key=True)
    hcpcs_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["lcd_id", "lcd_version"],
            ["lcds.lcd_id", "lcds.lcd_version"],
        ),
    )

    lcd: Mapped["LCD"] = relationship("LCD", back_populates="hcpcs_codes")


class LCDIcd10Covered(Base):
    __tablename__ = "lcd_icd10_covered"

    lcd_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    lcd_version: Mapped[int] = mapped_column(Integer, primary_key=True)
    icd10_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["lcd_id", "lcd_version"],
            ["lcds.lcd_id", "lcds.lcd_version"],
        ),
    )

    lcd: Mapped["LCD"] = relationship("LCD", back_populates="icd10_covered")


class LCDIcd10NonCovered(Base):
    __tablename__ = "lcd_icd10_noncovered"

    lcd_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    lcd_version: Mapped[int] = mapped_column(Integer, primary_key=True)
    icd10_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["lcd_id", "lcd_version"],
            ["lcds.lcd_id", "lcds.lcd_version"],
        ),
    )

    lcd: Mapped["LCD"] = relationship("LCD", back_populates="icd10_noncovered")
