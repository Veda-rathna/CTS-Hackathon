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
from app.repositories.synthea_repository import SyntheaRepository

logger = logging.getLogger(__name__)


class PARequestService:
    """Orchestrates the manual-form PA intake pipeline."""

    def __init__(
        self,
        normalization_service: NormalizationService,
        triage_service: TriageService,
        synthea_repository: SyntheaRepository = None,
    ) -> None:
        self._normalizer = normalization_service
        self._triage = triage_service
        self._synthea_repo = synthea_repository

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

        # Crosswalk SNOMED codes if Synthea integration is active
        if self._synthea_repo:
            if triage_dict.get("procedure_code"):
                triage_dict["procedure_code"] = self._synthea_repo.crosswalk_code(triage_dict["procedure_code"])
            
            if triage_dict.get("diagnosis_codes"):
                triage_dict["diagnosis_codes"] = [
                    self._synthea_repo.crosswalk_code(dx, target_system="ICD10")
                    for dx in triage_dict["diagnosis_codes"]
                ]

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

        # Step 3 — Fetch patient history and append to clinical notes
        patient_id = triage_dict.get("patient_id")
        clinical_notes = triage_dict.get("clinical_notes") or ""
        
        if patient_id and self._synthea_repo:
            logger.info("PARequestService | Fetching Synthea history for patient_id=%s", patient_id)
            history = self._synthea_repo.get_patient_history(patient_id)
            if history:
                # Combine Synthea history with any provider-supplied free text notes
                clinical_notes = f"{history}\n\nPROVIDER NOTES:\n{clinical_notes}".strip()
                
        triage_request = TriageRequest(
            procedure_code=triage_dict["procedure_code"],
            diagnosis_codes=triage_dict["diagnosis_codes"],
            state=triage_dict.get("state"),
            patient_age=triage_dict.get("patient_age"),
            service_date=triage_dict.get("service_date"),
            patient_id=patient_id,
            clinical_notes=clinical_notes if clinical_notes else None,
        )

        # Step 4 — return result
        return self._triage.evaluate(triage_request)
