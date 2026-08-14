"""SQLAlchemy model for pgvector policy chunks."""
from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

from app.models.base import Base


class PolicyChunk(Base):
    __tablename__ = "policy_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    policy_type: Mapped[str] = mapped_column(String(20), index=True)
    policy_id: Mapped[str] = mapped_column(String(50), index=True)
    policy_version: Mapped[int] = mapped_column(Integer, index=True)
    section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    chunk_text: Mapped[str] = mapped_column(Text)
    
    # 384 dimensions for sentence-transformers/all-MiniLM-L6-v2
    embedding: Mapped[Vector] = mapped_column(Vector(384))
    
    chunk_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
