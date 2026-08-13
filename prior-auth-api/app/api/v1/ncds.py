"""NCD endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.repositories import get_ncd_service
from app.schemas.common import ErrorResponse
from app.schemas.ncd import NCDResponse
from app.services.ncd_service import NCDService

router = APIRouter(prefix="/ncds", tags=["NCDs"])


@router.get(
    "/{ncd_id}",
    response_model=NCDResponse,
    responses={404: {"model": ErrorResponse, "description": "NCD not found"}},
    summary="Get NCD by ID",
    description=(
        "Returns the full National Coverage Determination (NCD) record. "
        "Returns **404** if the NCD does not exist."
    ),
)
def get_ncd(
    ncd_id: str,
    service: Annotated[NCDService, Depends(get_ncd_service)],
) -> NCDResponse:
    return service.get_ncd(ncd_id)
