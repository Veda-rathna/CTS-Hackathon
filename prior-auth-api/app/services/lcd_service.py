"""LCD service — business logic for LCD-related operations."""
from __future__ import annotations

from app.exceptions.handlers import ResourceNotFoundError
from app.repositories.interfaces.lcd_repository import LCDRepository
from app.schemas.lcd import LCDResponse


class LCDService:
    """Orchestrates LCD retrieval and delegates to the repository."""

    def __init__(self, repository: LCDRepository) -> None:
        self._repo = repository

    def get_lcd(self, lcd_id: str) -> LCDResponse:
        """Return the LCD or raise ``ResourceNotFoundError``."""
        lcd = self._repo.get_by_id(lcd_id.strip().upper())
        if lcd is None:
            raise ResourceNotFoundError(
                f"LCD '{lcd_id}' was not found.",
                details={"lcd_id": lcd_id},
            )
        return lcd
