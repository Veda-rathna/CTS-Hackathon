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

        Authority ladder (deterministic overrides LLM):
          NOT_SATISFIED (mandatory + authoritative)              → EXCLUDED
          NOT_SATISFIED (mandatory, non-auth, no satisfied)      → EXCLUDED
          UNKNOWN (mandatory + authoritative)                    → UNKNOWN (blocking)
          UNKNOWN (mandatory, non-auth only, auth SATISFIED)     → ignored (abstain)
          UNKNOWN (mandatory, non-auth only, no auth SATISFIED)  → UNKNOWN
          SATISFIED (authoritative, any)                         → COVERED
          empty / all NOT_ADDRESSED                              → NOT_ADDRESSED

        Key fix for Bug 5:
            Non-authoritative (LLM/agent) mandatory UNKNOWN criteria do NOT
            block a COVERED decision when at least one authoritative criterion
            is SATISFIED. They simply abstain.
        """
        if not matrix.criteria:
            return "NOT_ADDRESSED"

        has_authoritative_mandatory_unknown = False
        has_nonauth_mandatory_unknown = False
        has_authoritative_satisfied = False
        has_any_satisfied = False
        has_authoritative_not_satisfied = False
        has_nonauth_not_satisfied = False

        for c in matrix.criteria:
            if c.status == EvaluationStatus.NOT_SATISFIED and c.mandatory:
                if c.authoritative:
                    has_authoritative_not_satisfied = True
                else:
                    has_nonauth_not_satisfied = True
            elif c.status == EvaluationStatus.UNKNOWN and c.mandatory:
                if c.authoritative:
                    has_authoritative_mandatory_unknown = True
                else:
                    has_nonauth_mandatory_unknown = True
            elif c.status == EvaluationStatus.SATISFIED:
                has_any_satisfied = True
                if c.authoritative:
                    has_authoritative_satisfied = True

        # 1. Authoritative explicit exclusion always wins
        if has_authoritative_not_satisfied:
            return "EXCLUDED"

        # 2. Non-authoritative not-satisfied without any satisfied → EXCLUDED
        if has_nonauth_not_satisfied and not has_any_satisfied:
            return "EXCLUDED"

        # 3. Authoritative mandatory UNKNOWN → block (cannot approve without deterministic clarity)
        if has_authoritative_mandatory_unknown:
            return "UNKNOWN"

        # 4. If we have satisfied evidence and no authoritative exclusion/unknown:
        #    Non-authoritative UNKNOWN criteria abstain — they do not block COVERED.
        if has_any_satisfied and not has_authoritative_not_satisfied and not has_authoritative_mandatory_unknown:
            if has_nonauth_not_satisfied:
                # Mixed: some non-auth criteria unsatisfied alongside satisfied ones
                return "NOT_ADDRESSED"
            return "COVERED"

        # 5. Non-authoritative mandatory UNKNOWN with no satisfied criteria → UNKNOWN
        if has_nonauth_mandatory_unknown and not has_any_satisfied:
            return "UNKNOWN"

        # 6. Nothing satisfied and no exclusions
        return "NOT_ADDRESSED"

