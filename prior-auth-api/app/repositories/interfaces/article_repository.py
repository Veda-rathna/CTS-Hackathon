"""Abstract interface (Protocol) for the Article repository.

Any concrete implementation — mock or PostgreSQL — must satisfy this interface.
The service layer depends only on this protocol, never on a concrete class.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.schemas.article import ArticleResponse, CodeEntry


@runtime_checkable
class ArticleRepository(Protocol):
    """Read operations for Article entities."""

    def get_by_id(self, article_id: str) -> ArticleResponse | None:
        """Return the article matching *article_id*, or ``None`` if not found."""
        ...

    def get_icd10_covered(self, article_id: str) -> list[CodeEntry]:
        """Return all ICD-10 covered codes for the given article."""
        ...

    def get_icd10_noncovered(self, article_id: str) -> list[CodeEntry]:
        """Return all ICD-10 non-covered codes for the given article."""
        ...

    def get_hcpcs(self, article_id: str) -> list[CodeEntry]:
        """Return all HCPCS/CPT codes for the given article."""
        ...
