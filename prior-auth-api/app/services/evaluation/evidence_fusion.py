"""Evidence Fusion."""
from __future__ import annotations

import logging
from typing import List

from app.schemas.evaluation import EvaluatedCriterion, EvaluationStatus, EvidenceMatrix

logger = logging.getLogger(__name__)


class EvidenceFusion:
    """Consolidates evidence and enforces the Authority Layer."""

    @staticmethod
    def fuse(criteria: List[EvaluatedCriterion]) -> EvidenceMatrix:
        """
        Fuse multiple criteria evaluations into a single EvidenceMatrix.
        Enforces authority:
        Structured (SQL) > Rule > Semantic (LLM)
        
        If there are multiple evaluations for the *same* concept, deterministic wins.
        Here we simply collect the results, but the DecisionEngine will rely on these
        status fields. LLM evaluations cannot override a deterministic NOT_SATISFIED.
        """
        matrix = EvidenceMatrix(criteria=criteria)
        
        # Simple logging for transparency
        for crit in criteria:
            logger.info(
                f"Fusion Log | Criterion: {crit.criterion_id} | Type: {crit.criterion_type.value} "
                f"| Evaluator: {crit.evaluator.value} | Status: {crit.status.value}"
            )
            
        return matrix

    @staticmethod
    def resolve_decision(matrix: EvidenceMatrix) -> str:
        """
        Helper to resolve the coverage decision from an EvidenceMatrix.
        Returns COVERED, EXCLUDED, UNKNOWN, or NOT_ADDRESSED.

        Authority ladder:
          NOT_SATISFIED (mandatory + authoritative) → EXCLUDED
          NOT_SATISFIED (mandatory, non-auth) alone → EXCLUDED
          UNKNOWN (mandatory)                       → UNKNOWN
          SATISFIED (any)                           → COVERED
          UNKNOWN (all)                             → NOT_ADDRESSED
          empty                                     → NOT_ADDRESSED
        """
        if not matrix.criteria:
            return "NOT_ADDRESSED"

        has_unknown = False
        has_mandatory_unknown = False
        has_satisfied = False
        has_authoritative_not_satisfied = False
        has_nonauth_not_satisfied = False

        for c in matrix.criteria:
            if c.status == EvaluationStatus.NOT_SATISFIED and c.mandatory:
                if c.authoritative:
                    has_authoritative_not_satisfied = True
                else:
                    has_nonauth_not_satisfied = True
            elif c.status == EvaluationStatus.UNKNOWN:
                has_unknown = True
                if c.mandatory:
                    has_mandatory_unknown = True
            elif c.status == EvaluationStatus.SATISFIED:
                has_satisfied = True

        if has_authoritative_not_satisfied:
            return "EXCLUDED"
            
        if has_nonauth_not_satisfied and not has_satisfied:
            return "EXCLUDED"
            
        if has_mandatory_unknown:
            return "UNKNOWN"
            
        if has_unknown and not has_satisfied:
            return "UNKNOWN"
            
        if has_satisfied and not has_nonauth_not_satisfied:
            return "COVERED"
            
        if has_satisfied and has_nonauth_not_satisfied:
            return "NOT_ADDRESSED"
            
        return "NOT_ADDRESSED"
