"""Structured Evaluator.

Evaluates STRUCTURED criteria deterministically using exact code matches,
SQL lookups, and existing repository logic.
"""
from __future__ import annotations

import logging
from typing import Any

from app.schemas.evaluation import CriterionEvaluation
from app.schemas.triage import TriageRequest

logger = logging.getLogger(__name__)


class StructuredEvaluator:
    """Evaluates STRUCTURED criteria."""

    def evaluate(
        self,
        criterion: CriterionEvaluation,
        request: TriageRequest,
        policy_data: Any,
    ) -> CriterionEvaluation:
        """Evaluate a single structured criterion."""
        if criterion.criterion_type != "STRUCTURED":
            return criterion
            
        # Ensure we only evaluate if it hasn't been deterministically evaluated yet
        # (Though usually it starts as UNKNOWN)

        c_text = criterion.criterion.lower()
        
        # NCD Decision hint
        if "policy explicit decision indicates:" in c_text:
            decision = c_text.split(":")[-1].strip()
            if decision in ("covered", "covered_with_conditions"):
                criterion.status = "SATISFIED"
                criterion.explanation = f"Policy explicitly states: {decision.upper()}"
            elif decision in ("non_covered", "excluded"):
                criterion.status = "NOT_SATISFIED"
                criterion.explanation = f"Policy explicitly states: {decision.upper()}"
            else:
                criterion.status = "UNKNOWN"
            return criterion

        # Procedure Code Match
        if "procedure code" in c_text and hasattr(policy_data, "hcpcs_codes"):
            covered = any(
                c.code == request.procedure_code for c in policy_data.hcpcs_codes
            )
            if covered:
                criterion.status = "SATISFIED"
                criterion.patient_evidence.append(f"Submitted procedure: {request.procedure_code}")
                criterion.policy_evidence.append(f"{request.procedure_code} is listed as a covered HCPCS code.")
                criterion.explanation = "Exact HCPCS code match."
            else:
                # Typically, if it's not in the covered list for an LCD that explicitly lists them, it's not covered.
                criterion.status = "NOT_SATISFIED"
                criterion.patient_evidence.append(f"Submitted procedure: {request.procedure_code}")
                criterion.explanation = "HCPCS code not found in covered list."
            return criterion

        # ICD-10 Covered Match
        if "diagnosis code must be in" in c_text and "non-covered" not in c_text and hasattr(policy_data, "icd10_covered"):
            if not policy_data.icd10_covered:
                # No specific covered list, assume covered unless excluded
                criterion.status = "SATISFIED"
                return criterion
                
            covered = any(
                dx in [c.code for c in policy_data.icd10_covered]
                for dx in request.diagnosis_codes
            )
            if covered:
                criterion.status = "SATISFIED"
                criterion.explanation = "Diagnosis code found in covered ICD-10 list."
            else:
                criterion.status = "NOT_SATISFIED"
                criterion.explanation = "No submitted diagnosis code found in covered ICD-10 list."
            return criterion

        # ICD-10 Non-Covered Match
        if "not be in the lcd non-covered" in c_text and hasattr(policy_data, "icd10_noncovered"):
            if not policy_data.icd10_noncovered:
                criterion.status = "SATISFIED"
                return criterion
                
            excluded = any(
                dx in [c.code for c in policy_data.icd10_noncovered]
                for dx in request.diagnosis_codes
            )
            if excluded:
                criterion.status = "NOT_SATISFIED"
                criterion.explanation = "Diagnosis code found in explicit non-covered ICD-10 list."
            else:
                criterion.status = "SATISFIED"
                criterion.explanation = "No submitted diagnosis code found in non-covered list."
            return criterion

        return criterion
