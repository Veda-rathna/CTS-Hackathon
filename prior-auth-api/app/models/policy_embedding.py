"""SQLAlchemy model for policy text embeddings (pgvector).

Stores chunked and embedded policy content for the RAG retrieval pipeline.
The embedding dimension is configurable via EMBEDDING_DIMENSION setting.

NOTE: Requires the ``vector`` extension in PostgreSQL:
    CREATE EXTENSION IF NOT EXISTS vector;
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PolicyEmbedding(Base):
    """Chunked policy text with vector embedding for semantic retrieval."""

    __tablename__ = "policy_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    policy_type: Mapped[str] = mapped_column(String(10), nullable=False)
    policy_id: Mapped[str] = mapped_column(String(50), nullable=False)
    policy_version: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[str] = mapped_column(String(100), nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)

    # The embedding column is created dynamically by Alembic migration
    # using the configured EMBEDDING_DIMENSION.  We store it as a generic
    # column here; the actual pgvector type is applied in the migration.
    # For ORM usage, we access it via raw SQL or pgvector SQLAlchemy type.

    effective_date: Mapped[date | None] = mapped_column(nullable=True)
    end_date: Mapped[date | None] = mapped_column(nullable=True)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    jurisdiction_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contractor_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )

    __table_args__ = (
        Index("ix_policy_embeddings_type_id", "policy_type", "policy_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<PolicyEmbedding(id={self.id}, "
            f"policy_type={self.policy_type!r}, "
            f"policy_id={self.policy_id!r}, "
            f"section={self.section!r})>"
        )
