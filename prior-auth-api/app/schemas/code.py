"""Schemas for code-specific endpoints (codes sub-resource)."""
from __future__ import annotations

from pydantic import BaseModel


class CodeLookupEntry(BaseModel):
    """Single code entry for code lookup responses."""

    code: str
    description: str | None = None
