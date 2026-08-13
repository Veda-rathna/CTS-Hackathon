"""Policy search endpoint."""
from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies.repositories import get_policy_service
from app.schemas.policy import PolicySearchResponse
from app.services.policy_service import PolicyService

router = APIRouter(prefix="/policies", tags=["Policies"])


@router.get(
    "/search",
    response_model=PolicySearchResponse,
    summary="Search policies by procedure and optional filters",
    description=(
        "Search for applicable Medicare coverage policies (LCD/NCD/Article) "
        "using a procedure code and optional diagnosis, state, payer, and date filters.\n\n"
        "Example: `/api/v1/policies/search?procedure_code=64483&diagnosis_code=M54.16&state=TX`\n\n"
        "All match flags (``procedure_match``, ``diagnosis_match``, ``jurisdiction_match``, "
        "``effective``) are populated on each result to aid the caller in filtering."
    ),
)
def search_policies(
    procedure_code: Annotated[
        str,
        Query(description="HCPCS or CPT procedure code (required).", min_length=1),
    ],
    service: Annotated[PolicyService, Depends(get_policy_service)],
    diagnosis_code: Annotated[
        str | None,
        Query(description="ICD-10 diagnosis code to filter by."),
    ] = None,
    state: Annotated[
        str | None,
        Query(description="Two-letter US state abbreviation.", max_length=2),
    ] = None,
    payer: Annotated[
        str | None,
        Query(description="Payer name (e.g. 'Medicare')."),
    ] = None,
    policy_type: Annotated[
        str | None,
        Query(description="Filter by policy type: LCD, NCD, or ARTICLE."),
    ] = None,
    effective_date: Annotated[
        date | None,
        Query(description="Check policy effectiveness as of this date (ISO 8601)."),
    ] = None,
) -> PolicySearchResponse:
    return service.search(
        procedure_code=procedure_code,
        diagnosis_code=diagnosis_code,
        state=state,
        payer=payer,
        policy_type=policy_type,
        effective_date=effective_date,
    )
