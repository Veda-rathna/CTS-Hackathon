"""Criteria Extractor.

Extracts criteria from policy structured fields and RAG sections.
Prioritizes structured metadata, applies deterministic parsing, and uses
LLM only for unstructured narrative text.
"""
from __future__ import annotations

import logging
from typing import Any

from app.schemas.evaluation import CriterionEvaluation, CriterionSource
from app.schemas.triage import TriageRequest
from app.services.evaluation.criterion_classifier import CriterionClassifier

logger = logging.getLogger(__name__)


class CriteriaExtractor:
    """Extracts and classifies criteria from policies."""

    def __init__(
        self,
        classifier: CriterionClassifier,
        # llm_client will be added later for unstructured extraction
    ) -> None:
        self._classifier = classifier

    def extract(
        self,
        structured_data: Any,
        policy_sections: list[Any],
        request_facts: TriageRequest,
    ) -> list[CriterionEvaluation]:
        """Extract criteria from a policy.
        
        Args:
            structured_data: The ORM/schema model (NCDResponse/LCDResponse).
            policy_sections: Retrieved RAG sections (if any).
            request_facts: The submitted TriageRequest.
            
        Returns:
            List of classified CriterionEvaluation objects.
        """
        criteria: list[CriterionEvaluation] = []
        criterion_idx = 1
        
        policy_type = "NCD" if hasattr(structured_data, "decision") else "LCD"
        policy_id = structured_data.id
        
        # 1. Extract from Structured Fields
        
        # NCD Decision Field (Used as a hint)
        if policy_type == "NCD" and getattr(structured_data, "decision", None):
            decision = structured_data.decision.upper()
            if decision in ("COVERED", "COVERED_WITH_CONDITIONS", "NON_COVERED", "EXCLUDED"):
                source = CriterionSource(
                    policy_type=policy_type,
                    policy_id=policy_id,
                    section="decision",
                    extraction_method="STRUCTURED_FIELD",
                )
                c_type = self._classifier.classify(f"Policy decision is {decision}", source)
                
                criteria.append(CriterionEvaluation(
                    criterion_id=f"C{criterion_idx}",
                    criterion=f"Policy explicit decision indicates: {decision}",
                    criterion_type=c_type,
                    source=source,
                    evaluator="SQL", # Will be handled by structured evaluator
                    status="UNKNOWN", # Default before evaluation
                    mandatory=True,
                ))
                criterion_idx += 1
                
        # LCD Structured Code Relationships (ICD-10, HCPCS)
        if policy_type == "LCD":
            # HCPCS Codes
            if hasattr(structured_data, "hcpcs_codes") and structured_data.hcpcs_codes:
                source = CriterionSource(
                    policy_type=policy_type,
                    policy_id=policy_id,
                    section="hcpcs_codes",
                    extraction_method="CODE_RELATIONSHIP",
                )
                criteria.append(CriterionEvaluation(
                    criterion_id=f"C{criterion_idx}",
                    criterion="Procedure code must be in the LCD covered list",
                    criterion_type="STRUCTURED",
                    source=source,
                    evaluator="SQL",
                    status="UNKNOWN",
                    mandatory=True,
                ))
                criterion_idx += 1
                
            # ICD-10 Covered
            if hasattr(structured_data, "icd10_covered") and structured_data.icd10_covered:
                source = CriterionSource(
                    policy_type=policy_type,
                    policy_id=policy_id,
                    section="icd10_covered",
                    extraction_method="CODE_RELATIONSHIP",
                )
                criteria.append(CriterionEvaluation(
                    criterion_id=f"C{criterion_idx}",
                    criterion="Diagnosis code must be in the LCD covered list",
                    criterion_type="STRUCTURED",
                    source=source,
                    evaluator="SQL",
                    status="UNKNOWN",
                    mandatory=True,
                ))
                criterion_idx += 1
                
            # ICD-10 Non-Covered
            if hasattr(structured_data, "icd10_noncovered") and structured_data.icd10_noncovered:
                source = CriterionSource(
                    policy_type=policy_type,
                    policy_id=policy_id,
                    section="icd10_noncovered",
                    extraction_method="CODE_RELATIONSHIP",
                )
                criteria.append(CriterionEvaluation(
                    criterion_id=f"C{criterion_idx}",
                    criterion="Diagnosis code must NOT be in the LCD non-covered list",
                    criterion_type="STRUCTURED",
                    source=source,
                    evaluator="SQL",
                    status="UNKNOWN",
                    mandatory=True,
                ))
                criterion_idx += 1
                
        # 2. Extract from unstructured text (RAG sections)
        # This will be done via LLM in a later step if needed, or by deterministic parsing.
        # For now, we mock/stub unstructured extraction, or delegate to LLM client.
        
        # If we have RAG sections, and LLM is enabled, we could extract semantic criteria here.
        # This implementation will be expanded when LLM client is integrated.

        return criteria
