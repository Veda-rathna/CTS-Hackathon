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
        """
        if not matrix.criteria:
            return "NOT_ADDRESSED"
            
        has_unknown = False
        has_satisfied = False
        
        for c in matrix.criteria:
            if c.status == EvaluationStatus.NOT_SATISFIED:
                # If a mandatory criterion is not satisfied, it's excluded
                if c.mandatory:
                    return "EXCLUDED"
            elif c.status == EvaluationStatus.UNKNOWN:
                has_unknown = True
            elif c.status == EvaluationStatus.SATISFIED:
                has_satisfied = True

        if has_unknown:
            return "UNKNOWN"
            
        if has_satisfied:
            return "COVERED"
            
        return "NOT_ADDRESSED"
