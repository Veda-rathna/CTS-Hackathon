"""SQLAlchemy models for Article and its associated code tables.

⚠️  SCHEMA NOTE: Update table/column names when the data team delivers
    the final PostgreSQL schema.  Only this file and the corresponding
    PostgreSQL repository need to change.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    display_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    publication_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    icd10_covered: Mapped[list["ArticleIcd10Covered"]] = relationship(
        "ArticleIcd10Covered", back_populates="article", cascade="all, delete-orphan"
    )
    icd10_noncovered: Mapped[list["ArticleIcd10NonCovered"]] = relationship(
        "ArticleIcd10NonCovered", back_populates="article", cascade="all, delete-orphan"
    )
    hcpcs_codes: Mapped[list["ArticleHcpcsCode"]] = relationship(
        "ArticleHcpcsCode", back_populates="article", cascade="all, delete-orphan"
    )


class ArticleIcd10Covered(Base):
    """ICD-10 codes that ARE covered under an article."""

    __tablename__ = "article_icd10_covered"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    article_id: Mapped[str] = mapped_column(ForeignKey("articles.id"), index=True)
    icd10_code: Mapped[str] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    article: Mapped["Article"] = relationship("Article", back_populates="icd10_covered")


class ArticleIcd10NonCovered(Base):
    """ICD-10 codes that are explicitly NOT covered under an article."""

    __tablename__ = "article_icd10_noncovered"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    article_id: Mapped[str] = mapped_column(ForeignKey("articles.id"), index=True)
    icd10_code: Mapped[str] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    article: Mapped["Article"] = relationship("Article", back_populates="icd10_noncovered")


class ArticleHcpcsCode(Base):
    """HCPCS/CPT procedure codes referenced in an article."""

    __tablename__ = "article_hcpcs_codes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    article_id: Mapped[str] = mapped_column(ForeignKey("articles.id"), index=True)
    hcpcs_code: Mapped[str] = mapped_column(String(20), index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    article: Mapped["Article"] = relationship("Article", back_populates="hcpcs_codes")
