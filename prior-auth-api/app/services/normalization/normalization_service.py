"""PA Request Normalization Service.

The single, reusable normalization layer for all intake sources (manual form,
and in future, PDF extraction).

Responsibilities
----------------
- State normalization: full name -> 2-letter abbreviation
- Date normalization: ensure YYYY-MM-DD
- Procedure code normalization: strip/uppercase
- Diagnosis normalization: preserve all diagnoses, extract ICD-10 list
- Patient ID extraction
- request_date auto-generation when absent
"""
from __future__ import annotations

import logging
import re
from datetime import date
from typing import Optional

from app.schemas.pa_request import CanonicalPARequest

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# State name -> 2-letter abbreviation mapping
# ---------------------------------------------------------------------------

_STATE_NAME_TO_ABBR: dict[str, str] = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN",
    "mississippi": "MS", "missouri": "MO", "montana": "MT", "nebraska": "NE",
    "nevada": "NV", "newhampshire": "NH", "newjersey": "NJ", "newmexico": "NM",
    "newyork": "NY", "northcarolina": "NC", "northdakota": "ND", "ohio": "OH",
    "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA", "rhodeisland": "RI",
    "southcarolina": "SC", "southdakota": "SD", "tennessee": "TN", "texas": "TX",
    "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA",
    "westvirginia": "WV", "wisconsin": "WI", "wyoming": "WY",
    # District of Columbia
    "districtofcolumbia": "DC", "dc": "DC",
}

_VALID_ABBRS: set[str] = set(_STATE_NAME_TO_ABBR.values())


class NormalizationService:
    """Stateless normalization service.

    Usage
    -----
        svc = NormalizationService()
        canonical = svc.normalize_pa_request(raw_input)
    """

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def normalize_pa_request(self, raw: CanonicalPARequest) -> CanonicalPARequest:
        """Normalize and fill in derived fields on a CanonicalPARequest.

        Returns a *new* CanonicalPARequest with all values cleaned.
        The original object is not mutated.
        """
        data = raw.model_dump()

        # 1. Ensure pa_request_id exists
        if not data.get("pa_request_id"):
            from uuid import uuid4
            data["pa_request_id"] = f"PA-{uuid4().hex[:8].upper()}"
            logger.debug("NormalizationService | Auto-generated pa_request_id=%s", data["pa_request_id"])

        # 2. Normalize request_date
        req = data.get("request") or {}
        if not req.get("request_date"):
            req["request_date"] = date.today().isoformat()
            logger.debug("NormalizationService | Auto-generated request_date=%s", req["request_date"])
        else:
            req["request_date"] = self._normalize_date(req["request_date"])
        data["request"] = req

        # 3. Normalize patient state
        patient = data.get("patient") or {}
        if patient.get("state"):
            patient["state"] = self._normalize_state(patient["state"])
        data["patient"] = patient

        # 4. Normalize provider state
        provider = data.get("provider") or {}
        if provider.get("state"):
            provider["state"] = self._normalize_state(provider["state"])
        data["provider"] = provider

        # 5. Normalize service dates and procedure code
        service = data.get("service") or {}
        if service.get("start_date"):
            service["start_date"] = self._normalize_date(service["start_date"])
        if service.get("end_date"):
            service["end_date"] = self._normalize_date(service["end_date"])
        if service.get("procedure_code"):
            service["procedure_code"] = service["procedure_code"].strip().upper()
        data["service"] = service

        # 6. Normalize diagnoses — uppercase ICD-10 codes
        diagnoses = data.get("diagnoses") or []
        for dx in diagnoses:
            if dx.get("icd10_code"):
                dx["icd10_code"] = dx["icd10_code"].strip().upper()
        data["diagnoses"] = diagnoses

        normalized = CanonicalPARequest.model_validate(data)
        logger.info(
            "NormalizationService | Normalized pa_request_id=%s procedure=%s diagnoses=%s state=%s",
            normalized.pa_request_id,
            normalized.service.procedure_code if normalized.service else None,
            [d.icd10_code for d in normalized.diagnoses],
            (normalized.patient.state if normalized.patient else None)
            or (normalized.provider.state if normalized.provider else None),
        )
        return normalized

    # ------------------------------------------------------------------
    # State normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_state(value: Optional[str]) -> Optional[str]:
        """Convert a full US state name or abbreviation to a 2-letter abbreviation.

        Examples
        --------
        "Massachusetts" -> "MA"
        "TEXAS"         -> "TX"
        "ma"            -> "MA"
        "CA"            -> "CA"
        None / ""       -> None
        """
        if not value or not value.strip():
            return None

        # Remove whitespace, normalize to lowercase for lookup
        normalized_key = re.sub(r"\s+", "", value.strip().lower())

        # If already a 2-letter abbreviation (case-insensitive)
        upper = value.strip().upper()
        if len(upper) == 2 and upper in _VALID_ABBRS:
            return upper

        # Try full-name lookup
        if normalized_key in _STATE_NAME_TO_ABBR:
            return _STATE_NAME_TO_ABBR[normalized_key]

        # Fallback: return cleaned uppercase as-is (may still be valid for edge cases)
        logger.warning("NormalizationService | Could not normalize state='%s', returning as-is.", value)
        return upper[:2] if len(upper) >= 2 else upper

    # ------------------------------------------------------------------
    # Date normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_date(value: Optional[str]) -> Optional[str]:
        """Ensure a date string is in YYYY-MM-DD format.

        Accepts ISO-8601 strings (with optional time component).
        Returns None if value is empty or unparseable.
        """
        if not value or not value.strip():
            return None
        try:
            # Handle "2026-08-15T00:00:00" or "2026-08-15"
            return value.strip()[:10]
        except Exception:
            logger.warning("NormalizationService | Could not normalize date='%s'.", value)
            return None


def build_triage_request(canonical: CanonicalPARequest) -> dict:
    """Convert a normalized CanonicalPARequest into a minimal TriageRequest dict.

    Only the fields required by the triage engine are included.

    Mapping
    -------
    canonical.service.procedure_code  -> procedure_code
    canonical.diagnoses[*].icd10_code -> diagnosis_codes (list, non-null only)
    patient.state or provider.state   -> state
    patient.age                       -> patient_age
    pa_request_id                     -> pa_request_id
    patient.patient_id                -> patient_id
    service.start_date                -> service_date
    """
    # Procedure code
    procedure_code: Optional[str] = None
    if canonical.service and canonical.service.procedure_code:
        procedure_code = canonical.service.procedure_code

    # Diagnosis codes — preserve all ICD-10 codes from the diagnoses list
    diagnosis_codes: list[str] = [
        dx.icd10_code
        for dx in canonical.diagnoses
        if dx.icd10_code and dx.icd10_code.strip()
    ]

    # State — patient first, provider as fallback
    state: Optional[str] = None
    if canonical.patient and canonical.patient.state:
        state = canonical.patient.state
    elif canonical.provider and canonical.provider.state:
        state = canonical.provider.state

    # Age
    patient_age: Optional[int] = None
    if canonical.patient and canonical.patient.age is not None:
        patient_age = canonical.patient.age

    # Service date
    service_date: Optional[str] = None
    if canonical.service and canonical.service.start_date:
        service_date = canonical.service.start_date

    return {
        "pa_request_id": canonical.pa_request_id,
        "patient_id": canonical.patient.patient_id if canonical.patient else None,
        "procedure_code": procedure_code,
        "diagnosis_codes": diagnosis_codes,
        "state": state,
        "patient_age": patient_age,
        "service_date": service_date,
        "clinical_notes": canonical.clinical_notes,
    }
