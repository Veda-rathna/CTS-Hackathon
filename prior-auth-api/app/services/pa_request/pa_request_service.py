"""PA Request Service.

Orchestrates the intake pipeline:

  PARequestService.create_pa_request(raw_canonical)
      |
      v
  NormalizationService.normalize_pa_request()
      |
      v
  build_triage_request()
      |
      v
  TriageService.evaluate()
      |
      v
  TriageResponse

Keeps the API router thin. All business logic lives here.
"""
from __future__ import annotations

import logging

from app.schemas.pa_request import CanonicalPARequest
from app.schemas.triage import TriageRequest, TriageResponse
from app.services.normalization.normalization_service import (
    NormalizationService,
    build_triage_request,
)
from app.services.triage_service import TriageService

logger = logging.getLogger(__name__)


class PARequestService:
    """Orchestrates the manual-form PA intake pipeline."""

    def __init__(
        self,
        normalization_service: NormalizationService,
        triage_service: TriageService,
    ) -> None:
        self._normalizer = normalization_service
        self._triage = triage_service

    def create_pa_request(self, raw: CanonicalPARequest) -> TriageResponse:
        """Process a canonical PA request through normalization and triage.

        Steps
        -----
        1. Normalize the raw PA request (state, dates, procedure code, ICD-10 codes).
        2. Build a minimal TriageRequest from the normalized canonical data.
        3. Pass the TriageRequest to the existing TriageService.
        4. Return the TriageResponse.
        """
        # Step 1 — normalize
        canonical = self._normalizer.normalize_pa_request(raw)

        # Step 2 — build triage payload
        triage_dict = build_triage_request(canonical)

        logger.info(
            "PARequestService | pa_request_id=%s -> triage payload: procedure=%s diagnoses=%s state=%s",
            triage_dict.get("pa_request_id"),
            triage_dict.get("procedure_code"),
            triage_dict.get("diagnosis_codes"),
            triage_dict.get("state"),
        )

        # Validate that the minimum required triage fields are present
        if not triage_dict.get("procedure_code"):
            raise ValueError(
                "service.procedure_code is required for triage evaluation."
            )
        if not triage_dict.get("diagnosis_codes"):
            raise ValueError(
                "At least one diagnosis with a valid ICD-10 code is required."
            )

        # Step 3 — call existing triage service (unchanged)
        triage_request = TriageRequest(
            procedure_code=triage_dict["procedure_code"],
            diagnosis_codes=triage_dict["diagnosis_codes"],
            state=triage_dict.get("state"),
            patient_age=triage_dict.get("patient_age"),
            service_date=triage_dict.get("service_date"),
        )

        # Step 4 — return result
        return self._triage.evaluate(triage_request)
