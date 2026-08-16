"""Canonical PA Request Pydantic schemas.

These models define the structured clinical PA request that flows from the
frontend form -> NormalizationService -> PARequestService -> TriageService.

They are intentionally separate from TriageRequest so the intake layer can
evolve independently of the triage engine.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# -- Enums ---------------------------------------------------------------------


class ReviewType(str, Enum):
    URGENT = "URGENT"
    NON_URGENT = "NON_URGENT"


class RequestType(str, Enum):
    INITIAL = "INITIAL"
    REAUTHORIZATION = "REAUTHORIZATION"


class Gender(str, Enum):
    M = "M"
    F = "F"
    O = "O"
    U = "U"


# -- Sub-models ----------------------------------------------------------------


class PAPatient(BaseModel):
    """Patient demographic information."""

    patient_id: Optional[str] = None
    date_of_birth: Optional[str] = Field(
        default=None,
        description="Date of birth in YYYY-MM-DD format.",
    )
    age: Optional[int] = Field(default=None, ge=0, le=130)
    gender: Optional[Gender] = None
    state: Optional[str] = Field(
        default=None,
        description="Patient's US state (full name or 2-letter abbreviation).",
    )


class PACoverage(BaseModel):
    """Insurance coverage details."""

    payer: Optional[str] = None
    plan_id: Optional[str] = None
    plan_name: Optional[str] = None


class PARequestMeta(BaseModel):
    """Request-level metadata (review type, urgency, dates)."""

    request_date: Optional[str] = Field(
        default=None,
        description="Request submission date (YYYY-MM-DD). Auto-generated if null.",
    )
    review_type: ReviewType = ReviewType.NON_URGENT
    request_type: RequestType = RequestType.INITIAL
    urgency_reason: Optional[str] = None
    previous_authorization_number: Optional[str] = None


class PAProvider(BaseModel):
    """Requesting provider / organization details."""

    provider_id: Optional[str] = None
    specialty: Optional[str] = None
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    state: Optional[str] = Field(
        default=None,
        description="Provider's US state (full name or 2-letter abbreviation). "
        "Used as fallback when patient.state is absent.",
    )


class PAService(BaseModel):
    """Requested clinical service details."""

    service_description: str = Field(
        default="",
        description="Human-readable description of the requested service.",
    )
    procedure_code: Optional[str] = Field(
        default=None,
        description="CPT / HCPCS procedure code.",
    )
    start_date: Optional[str] = Field(
        default=None, description="Service start date (YYYY-MM-DD)."
    )
    end_date: Optional[str] = Field(
        default=None, description="Service end date (YYYY-MM-DD)."
    )
    place_of_service: Optional[str] = None
    number_of_sessions: Optional[int] = Field(default=None, ge=1)
    duration: Optional[str] = None
    frequency: Optional[str] = None


class PADiagnosis(BaseModel):
    """A single diagnosis entry -- PA can have multiple."""

    description: str = ""
    icd10_code: Optional[str] = Field(
        default=None,
        description="ICD-10-CM code (e.g. 'K06.8').",
    )


# -- Top-level canonical request -----------------------------------------------


class CanonicalPARequest(BaseModel):
    """Full structured PA request as submitted from the manual form.

    This is the canonical intake model. The NormalizationService transforms
    and validates values before a TriageRequest is built from it.
    """

    pa_request_id: Optional[str] = Field(
        default=None,
        description="Unique PA request identifier. Auto-generated if absent.",
    )
    patient: Optional[PAPatient] = None
    coverage: Optional[PACoverage] = None
    request: Optional[PARequestMeta] = None
    provider: Optional[PAProvider] = None
    service: Optional[PAService] = None
    diagnoses: list[PADiagnosis] = Field(
        default_factory=list,
        description="One or more diagnoses associated with the PA request.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "pa_request_id": "PA-001",
                    "patient": {
                        "patient_id": "p001",
                        "date_of_birth": "1979-02-20",
                        "age": 47,
                        "gender": "M",
                        "state": "Massachusetts",
                    },
                    "coverage": {
                        "payer": "Medicare",
                        "plan_id": "MED-MA-001",
                        "plan_name": "Medicare Advantage Example Plan",
                    },
                    "request": {
                        "request_date": None,
                        "review_type": "NON_URGENT",
                        "request_type": "INITIAL",
                        "urgency_reason": None,
                        "previous_authorization_number": None,
                    },
                    "provider": {
                        "provider_id": "prov018",
                        "specialty": "GENERAL PRACTICE",
                        "organization_id": "org018",
                        "organization_name": "FENWAY COMMUNITY HEALTH CENTER INC",
                        "state": "MA",
                    },
                    "service": {
                        "service_description": "Gingivectomy or gingivoplasty",
                        "procedure_code": "D4210",
                        "start_date": "2026-08-15",
                        "end_date": "2026-08-15",
                        "place_of_service": "Outpatient Dental Surgical Suite",
                        "number_of_sessions": 1,
                        "duration": "1 day",
                        "frequency": "Once",
                    },
                    "diagnoses": [
                        {"description": "Gingival disease", "icd10_code": "K06.8"},
                        {"description": "Chronic gingivitis", "icd10_code": "K05.10"},
                    ],
                }
            ]
        }
    }
