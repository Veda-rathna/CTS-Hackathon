"""PA Requests endpoint — manual form intake pipeline.

POST /api/v1/pa-requests

Accepts a full structured CanonicalPARequest, runs it through the
normalization and triage pipeline, and returns a TriageResponse.

The existing POST /api/v1/triage endpoint is NOT modified.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.repositories import get_triage_service
from app.schemas.pa_request import CanonicalPARequest
from app.schemas.triage import TriageResponse
from app.services.normalization import NormalizationService
from app.services.pa_request import PARequestService
from app.services.triage_service import TriageService

router = APIRouter(prefix="/pa-requests", tags=["PA Requests"])

_DISCLAIMER = (
    "**IMPORTANT**: The triage result reflects Medicare policy-matching only. "
    "It does NOT constitute clinical advice, guarantee of coverage, or a prior "
    "authorization decision. Always verify with the applicable Medicare "
    "Administrative Contractor (MAC) before proceeding with treatment."
)


def get_pa_request_service(
    triage_service: Annotated[TriageService, Depends(get_triage_service)],
) -> PARequestService:
    """Dependency: build PARequestService with injected TriageService."""
    return PARequestService(
        normalization_service=NormalizationService(),
        triage_service=triage_service,
    )


@router.post(
    "",
    response_model=TriageResponse,
    summary="Submit a structured PA request for policy evaluation",
    description=(
        "Accepts a fully structured Prior Authorization request (patient, coverage, "
        "provider, service, diagnoses). The backend normalizes the data and "
        "routes it through the existing triage engine.\n\n"
        "**Normalization applied:**\n"
        "- State full names converted to 2-letter abbreviations (e.g. Massachusetts -> MA)\n"
        "- Dates normalized to YYYY-MM-DD\n"
        "- `request_date` auto-populated from server date if absent\n"
        "- `pa_request_id` auto-generated if absent\n"
        "- All diagnosis ICD-10 codes preserved and passed to triage\n\n"
        + _DISCLAIMER
    ),
    responses={
        400: {"description": "Validation error or missing required clinical fields"},
        422: {"description": "Request body validation error"},
    },
    status_code=status.HTTP_200_OK,
)
def create_pa_request(
    payload: CanonicalPARequest,
    service: Annotated[PARequestService, Depends(get_pa_request_service)],
) -> TriageResponse:
    """Process a structured PA request through normalization and triage."""
    try:
        return service.create_pa_request(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
