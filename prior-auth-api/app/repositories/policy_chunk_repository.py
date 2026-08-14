"""Repository for vector-based policy chunks search."""
from __future__ import annotations

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.policy_chunk import PolicyChunk


class PolicyChunkRepository:
    """Repository for PolicyChunk."""

    def __init__(self, session: Session):
        self._session = session

    def search_similar(
        self,
        query_embedding: list[float],
        policy_type: str,
        candidate_policy_ids: list[str] | None = None,
        top_k: int = 5,
        threshold: float = 0.5,
    ) -> list[tuple[PolicyChunk, float]]:
        """
        Search for similar policy chunks using pgvector L2 distance.
        Must strictly restrict to candidate_policy_ids if provided.
        """
        # Using L2 distance (`l2_distance`) for similarity.
        # pgvector uses `<->` for L2, `<#>` for inner product, `<=>` for cosine
        
        # We'll use cosine distance since all-MiniLM-L6-v2 embeddings are normalized
        # and cosine similarity is typically preferred for sentence transformers.
        distance_col = PolicyChunk.embedding.cosine_distance(query_embedding)
        
        stmt = select(PolicyChunk, distance_col.label("distance"))
        
        # Filter by policy type
        stmt = stmt.where(PolicyChunk.policy_type == policy_type)
        
        # Candidate restriction (CRITICAL SAFETY BOUNDARY)
        if candidate_policy_ids:
            stmt = stmt.where(PolicyChunk.policy_id.in_(candidate_policy_ids))
            
        # Add distance filter
        stmt = stmt.where(distance_col < threshold)
        
        # Order by closest and limit
        stmt = stmt.order_by(distance_col).limit(top_k)
        
        return self._session.execute(stmt).all()

    def add_chunks(self, chunks_data: list[dict]) -> None:
        """Bulk insert chunks."""
        chunks = [PolicyChunk(**data) for data in chunks_data]
        self._session.add_all(chunks)
        self._session.flush()
