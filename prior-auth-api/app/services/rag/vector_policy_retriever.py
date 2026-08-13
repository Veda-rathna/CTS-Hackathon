"""Policy Retriever Protocol and pgvector implementation."""
from __future__ import annotations

import logging
from typing import Protocol

from sqlalchemy import select

from app.core.config import Settings
from app.exceptions.handlers import LLMServiceError
from app.models.policy_embedding import PolicyEmbedding
from app.schemas.evaluation import PolicySection, RetrievalResult, RetrievalStatus, RetrievedSection
from app.services.rag.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class PolicyRetriever(Protocol):
    """Protocol for RAG policy retrieval."""

    def retrieve(
        self, query: str, candidate_sections: list[PolicySection], min_score: float,
    ) -> RetrievalResult:
        """Retrieve relevant sections for the query.

        Args:
            query: The search query (usually extracted facts).
            candidate_sections: The universe of valid sections to search within.
            min_score: Minimum similarity score threshold.

        Returns:
            RetrievalResult containing status and matching sections.
        """
        ...


class VectorPolicyRetriever:
    """pgvector implementation of PolicyRetriever.

    Uses cosine distance to find semantically similar policy chunks.
    Constrains the search space to the provided candidate sections to
    prevent cross-policy leakage.
    """

    def __init__(
        self,
        db_session_factory,
        embedding_service: EmbeddingService,
        settings: Settings,
    ) -> None:
        self._db_session_factory = db_session_factory
        self._embedding_service = embedding_service
        self._top_k = settings.vector_top_k

    def retrieve(
        self, query: str, candidate_sections: list[PolicySection], min_score: float,
    ) -> RetrievalResult:
        """Execute constrained vector search."""
        if not candidate_sections:
            return RetrievalResult(status=RetrievalStatus.NO_MATCH, sections=[])

        try:
            query_embedding = self._embedding_service.embed_text(query)
        except LLMServiceError as exc:
            return RetrievalResult(
                status=RetrievalStatus.UNAVAILABLE, error=str(exc)
            )

        # Build candidate filter
        candidate_keys = {(s.policy_type, s.policy_id, s.section_type) for s in candidate_sections}

        with self._db_session_factory() as db:
            # Note: We need to adapt this query depending on how pgvector is integrated.
            # Assuming standard pgvector SQLAlchemy integration:
            # chunk.embedding.cosine_distance(query_embedding)
            # The lower the distance, the higher the similarity.
            # similarity = 1 - distance
            try:
                # We do a basic select here and filter in Python if we can't easily build the OR filter,
                # but it's better to build the OR filter.
                
                # For simplicity and given the constraint of small candidate sets per policy,
                # we can fetch all candidate chunks and sort them, or use the DB.
                # Let's use the DB.
                
                from sqlalchemy import or_, tuple_
                
                filter_conditions = [
                    (PolicyEmbedding.policy_type == pt) & 
                    (PolicyEmbedding.policy_id == pi) & 
                    (PolicyEmbedding.section == st)
                    for pt, pi, st in candidate_keys
                ]
                
                if not filter_conditions:
                    return RetrievalResult(status=RetrievalStatus.NO_MATCH, sections=[])
                
                stmt = select(PolicyEmbedding).where(or_(*filter_conditions))
                
                # Fetch candidate chunks from DB
                candidate_chunks = db.scalars(stmt).all()
                
                if not candidate_chunks:
                    return RetrievalResult(status=RetrievalStatus.NO_MATCH, sections=[])
                    
                # We can calculate similarity in Python or DB. DB is better.
                # In standard pgvector:
                # stmt = stmt.order_by(PolicyEmbedding.embedding.cosine_distance(query_embedding)).limit(self._top_k)
                # For now, let's just do a simple implementation using numpy since pgvector integration might vary
                import numpy as np
                
                query_vec = np.array(query_embedding)
                scored_chunks = []
                for chunk in candidate_chunks:
                    if chunk.embedding is None:
                        continue
                    # Ensure embedding is a list/array
                    chunk_vec = np.array(chunk.embedding)
                    
                    # Cosine similarity
                    similarity = np.dot(query_vec, chunk_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec))
                    if similarity >= min_score:
                        scored_chunks.append((similarity, chunk))
                        
                scored_chunks.sort(key=lambda x: x[0], reverse=True)
                top_chunks = scored_chunks[:self._top_k]

                if not top_chunks:
                    return RetrievalResult(status=RetrievalStatus.NO_MATCH, sections=[])

                results = []
                for score, chunk in top_chunks:
                    results.append(
                        RetrievedSection(
                            policy_type=chunk.policy_type,
                            policy_id=chunk.policy_id,
                            policy_version=str(chunk.policy_version),
                            section=chunk.section,
                            chunk_id=str(chunk.id),
                            content=chunk.chunk_text,
                            score=float(score),
                            metadata={"jurisdiction_id": chunk.jurisdiction_id}
                        )
                    )

                return RetrievalResult(status=RetrievalStatus.MATCHED, sections=results)

            except Exception as exc:
                logger.error("Database error during retrieval: %s", exc, exc_info=True)
                return RetrievalResult(
                    status=RetrievalStatus.UNAVAILABLE, error=str(exc)
                )
