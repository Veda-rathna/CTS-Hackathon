"""Embedding service — generates vector embeddings for policy text.

Uses sentence-transformers (local, no API cost) by default.
The model and dimension are configurable via settings.

When the embedding service is unavailable, callers receive
an ``LLMServiceError`` which the RAG pipeline handles gracefully
via the RETRIEVAL_UNAVAILABLE status.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from app.core.config import Settings
from app.exceptions.handlers import LLMServiceError

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generates text embeddings using a configurable model.

    Default: ``all-MiniLM-L6-v2`` (384-dim, runs on CPU, ~22 MB).
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._model = None
        self._model_name = settings.embedding_model
        self._dimension = settings.embedding_dimension

    def _load_model(self) -> None:
        """Lazy-load the embedding model on first use."""
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model: %s", self._model_name)
            self._model = SentenceTransformer(self._model_name)
            logger.info("Embedding model loaded (dimension=%d)", self._dimension)
        except Exception as exc:
            logger.error("Failed to load embedding model %s: %s", self._model_name, exc)
            raise LLMServiceError(
                f"Failed to load embedding model: {self._model_name}",
                details={"model": self._model_name, "error": str(exc)},
            ) from exc

    def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text string.

        Returns a list of floats with length ``EMBEDDING_DIMENSION``.
        Raises ``LLMServiceError`` if the model is unavailable.
        """
        self._load_model()
        try:
            embedding = self._model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as exc:
            raise LLMServiceError(
                "Failed to generate embedding",
                details={"error": str(exc)},
            ) from exc

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in a batch.

        Returns a list of embedding vectors.
        """
        if not texts:
            return []
        self._load_model()
        try:
            embeddings = self._model.encode(texts, normalize_embeddings=True)
            return embeddings.tolist()
        except Exception as exc:
            raise LLMServiceError(
                "Failed to generate batch embeddings",
                details={"count": len(texts), "error": str(exc)},
            ) from exc

    @property
    def dimension(self) -> int:
        """Return the configured embedding dimension."""
        return self._dimension
