"""SQLAlchemy models for Article and its associated code tables.

Supports composite version primary keys.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKeyConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Article(Base):
    __tablename__ = "articles"

    article_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    article_version: Mapped[int] = mapped_column(Integer, primary_key=True)

    display_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    article_type: Mapped[int | None] = mapped_column(Integer, nullable=True)
    article_type_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cms_cov_policy: Mapped[str | None] = mapped_column(Text, nullable=True)
    icd10_doc: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    article_eff_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    article_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    article_pub_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    date_retired: Mapped[date | None] = mapped_column(Date, nullable=True)
    reference_article: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Relationships
    icd10_covered: Mapped[list["ArticleIcd10Covered"]] = relationship(
        "ArticleIcd10Covered",
        back_populates="article",
        cascade="all, delete-orphan",
    )
    icd10_noncovered: Mapped[list["ArticleIcd10NonCovered"]] = relationship(
        "ArticleIcd10NonCovered",
        back_populates="article",
        cascade="all, delete-orphan",
    )
    hcpcs_codes: Mapped[list["ArticleHcpcsCode"]] = relationship(
        "ArticleHcpcsCode",
        back_populates="article",
        cascade="all, delete-orphan",
    )


class ArticleIcd10Covered(Base):
    """ICD-10 codes covered under a specific article version."""

    __tablename__ = "article_icd10_covered"

    article_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    article_version: Mapped[int] = mapped_column(Integer, primary_key=True)
    icd10_code_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    icd10_code_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    coverage_group: Mapped[int | None] = mapped_column(Integer, nullable=True)
    range_flag: Mapped[str | None] = mapped_column(String(1), nullable=True)
    sort_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    asterisk: Mapped[str | None] = mapped_column(String(10), nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["article_id", "article_version"],
            ["articles.article_id", "articles.article_version"],
        ),
    )

    article: Mapped["Article"] = relationship("Article", back_populates="icd10_covered")


class ArticleIcd10NonCovered(Base):
    """ICD-10 codes explicitly non-covered under a specific article version."""

    __tablename__ = "article_icd10_noncovered"

    article_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    article_version: Mapped[int] = mapped_column(Integer, primary_key=True)
    icd10_code_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    icd10_code_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    noncovered_group: Mapped[int | None] = mapped_column(Integer, nullable=True)
    range_flag: Mapped[str | None] = mapped_column(String(1), nullable=True)
    sort_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    asterisk: Mapped[str | None] = mapped_column(String(10), nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["article_id", "article_version"],
            ["articles.article_id", "articles.article_version"],
        ),
    )

    article: Mapped["Article"] = relationship("Article", back_populates="icd10_noncovered")


class ArticleHcpcsCode(Base):
    """HCPCS/CPT codes associated with a specific article version."""

    __tablename__ = "article_hcpcs"

    article_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    article_version: Mapped[int] = mapped_column(Integer, primary_key=True)
    hcpcs_code_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    hcpcs_code_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    code_group: Mapped[int | None] = mapped_column(Integer, nullable=True)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    range_flag: Mapped[str | None] = mapped_column(String(1), nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["article_id", "article_version"],
            ["articles.article_id", "articles.article_version"],
        ),
    )

    article: Mapped["Article"] = relationship("Article", back_populates="hcpcs_codes")
