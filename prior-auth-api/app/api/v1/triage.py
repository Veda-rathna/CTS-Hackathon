"""Triage endpoint — the primary integration point for the frontend."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.repositories import get_triage_service
from app.schemas.triage import TriageRequest, TriageResponse
from app.services.triage_service import TriageService

router = APIRouter(prefix="/triage", tags=["Triage"])

_DISCLAIMER = (
    "**IMPORTANT**: The triage result reflects Medicare policy-matching only. "
    "It does NOT constitute clinical advice, guarantee of coverage, or a prior "
    "authorization decision.  Always verify with the applicable Medicare "
    "Administrative Contractor (MAC) before proceeding with treatment."
)


@router.post(
    "",
    response_model=TriageResponse,
    summary="Run prior authorization triage",
    description=(
        "Submit a procedure code, one or more diagnosis codes, and optional state/payer "
        "context to receive a structured, explainable policy-matching result.\n\n"
        "The response includes:\n"
        "- A **decision** (e.g. `LIKELY_COVERED`, `POLICY_NOT_FOUND`)\n"
        "- A **confidence** score (0.0–1.0, deterministic completeness — not ML)\n"
        "- **Evidence** items explaining each matching step\n"
        "- Per-diagnosis **evaluation** results\n"
        "- Matched **policies** (LCD/NCD/Article)\n"
        "- **Missing information** and **warnings**\n\n"
        + _DISCLAIMER
    ),
    responses={
        400: {"description": "Invalid input"},
        422: {"description": "Validation error"},
    },
)
def run_triage(
    request: TriageRequest,
    service: Annotated[TriageService, Depends(get_triage_service)],
) -> TriageResponse:
    return service.evaluate(request)
