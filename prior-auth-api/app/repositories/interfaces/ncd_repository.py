"""Abstract interface (Protocol) for the NCD repository."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.schemas.ncd import NCDResponse


@runtime_checkable
class NCDRepository(Protocol):
    """Read operations for National Coverage Determination (NCD) entities."""

    def get_by_id(self, ncd_id: str) -> NCDResponse | None:
        """Return the NCD matching *ncd_id*, or ``None`` if not found."""
        ...
