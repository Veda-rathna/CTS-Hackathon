"""LCD endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.repositories import get_lcd_service
from app.schemas.common import ErrorResponse
from app.schemas.lcd import LCDResponse
from app.services.lcd_service import LCDService

router = APIRouter(prefix="/lcds", tags=["LCDs"])


@router.get(
    "/{lcd_id}",
    response_model=LCDResponse,
    responses={404: {"model": ErrorResponse, "description": "LCD not found"}},
    summary="Get LCD by ID",
    description=(
        "Returns the full Local Coverage Determination (LCD) record including "
        "jurisdiction, contractor, associated articles, and code lists. "
        "Returns **404** if the LCD does not exist."
    ),
)
def get_lcd(
    lcd_id: str,
    service: Annotated[LCDService, Depends(get_lcd_service)],
) -> LCDResponse:
    return service.get_lcd(lcd_id)
