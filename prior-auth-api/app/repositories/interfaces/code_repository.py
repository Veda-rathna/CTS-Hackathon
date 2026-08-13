"""Abstract interface (Protocol) for raw code lookups.

This interface is used when a service needs to verify whether a given code
exists in the code catalogue independently of a specific article.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.schemas.article import CodeEntry


@runtime_checkable
class CodeRepository(Protocol):
    """Read operations for the combined code catalogue."""

    def find_hcpcs(self, code: str) -> CodeEntry | None:
        """Return a HCPCS/CPT code entry, or ``None`` if not found."""
        ...

    def find_icd10(self, code: str) -> CodeEntry | None:
        """Return an ICD-10 code entry, or ``None`` if not found."""
        ...
