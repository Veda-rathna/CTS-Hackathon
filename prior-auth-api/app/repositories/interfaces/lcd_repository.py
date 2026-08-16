"""Abstract interface (Protocol) for the LCD repository.

Cleaned up and decluttered by Vedarathna.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.schemas.lcd import LCDResponse


@runtime_checkable
class LCDRepository(Protocol):
    """Read operations for Local Coverage Determination (LCD) entities."""

    def get_by_id(self, lcd_id: str) -> LCDResponse | None:
        """Return the LCD matching *lcd_id*, or ``None`` if not found."""
        ...

    def get_hcpcs(self, lcd_id: str) -> list:
        """Return HCPCS/CPT codes listed under this LCD."""
        ...

    def get_icd10_covered(self, lcd_id: str) -> list:
        """Return covered ICD-10 codes for this LCD."""
        ...

    def get_icd10_noncovered(self, lcd_id: str) -> list:
        """Return non-covered ICD-10 codes for this LCD."""
        ...
