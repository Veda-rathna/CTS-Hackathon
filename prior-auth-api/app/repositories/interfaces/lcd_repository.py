"""Abstract interface (Protocol) for the LCD repository."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.schemas.lcd import LCDResponse


@runtime_checkable
class LCDRepository(Protocol):
    """Read operations for Local Coverage Determination (LCD) entities."""

    def get_by_id(self, lcd_id: str) -> LCDResponse | None:
        """Return the LCD matching *lcd_id*, or ``None`` if not found."""
        ...

    def find_by_hcpcs_code(self, hcpcs_code: str) -> list[LCDResponse]:
        """Return all LCDs that reference the given HCPCS/CPT code."""
        ...

    def find_by_jurisdiction(self, jurisdiction_id: str) -> list[LCDResponse]:
        """Return all LCDs within a given jurisdiction."""
        ...
