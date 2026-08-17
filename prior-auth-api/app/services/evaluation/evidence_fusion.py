"""Evidence Fusion."""
from __future__ import annotations

import logging
from typing import List

from app.schemas.evaluation import (
    CriterionType,
    EvaluatedCriterion,
    EvaluationStatus,
    EvaluatorType,
    EvidenceMatrix,
    PolicyCriterion,
)

logger = logging.getLogger(__name__)


class EvidenceFusion:
    """Consolidates evidence and enforces the Authority Layer."""

    @staticmethod
    def fuse_criterion(
        structured_res: EvaluatedCriterion,
        semantic_res: EvaluatedCriterion,
        criterion: PolicyCriterion,
    ) -> EvaluatedCriterion:
        """Fuse structured evaluation and semantic evaluation for a single criterion.

        Enforces the deterministic authority truth table:
          - Structured NOT_SATISFIED (code excluded) ➔ NOT_SATISFIED
          - Semantic NOT_SATISFIED (clinical contradiction) ➔ NOT_SATISFIED
          - Structured SATISFIED + Semantic SATISFIED ➔ SATISFIED
          - Structured SATISFIED + Semantic UNKNOWN on clinical requirement ➔ UNKNOWN
          - Structured SATISFIED + Semantic UNKNOWN on structured code check ➔ SATISFIED
          - Structured UNKNOWN + Semantic SATISFIED ➔ SATISFIED
          - Both UNKNOWN ➔ UNKNOWN
        """
        # 1. Collect and clean patient evidence
        raw_patient_ev = (structured_res.patient_evidence or []) + (semantic_res.patient_evidence or [])
        clean_patient_ev: List[str] = []
        _ignore_tokens = {
            "could not match any requested codes",
            "llm evaluation disabled",
            "semantic evaluation unavailable",
            "no semantic evaluator",
            "no clinical information provided",
            "no clinical notes provided",
        }
        for ev in raw_patient_ev:
            if not ev or not str(ev).strip():
                continue
            ev_str = str(ev).strip()
            if any(ign in ev_str.lower() for ign in _ignore_tokens):
                continue
            if ev_str not in clean_patient_ev:
                clean_patient_ev.append(ev_str)

        # 2. Collect and clean policy evidence
        raw_policy_ev = (structured_res.policy_evidence or []) + (semantic_res.policy_evidence or [])
        clean_policy_ev = list(dict.fromkeys(str(p).strip() for p in raw_policy_ev if p and str(p).strip()))
        if not clean_policy_ev:
            clean_policy_ev = [criterion.criterion]

        # 3. Determine fused status according to authority ladder
        is_code_check = criterion.type == CriterionType.STRUCTURED

        # Rule 1: Explicit deterministic exclusion or failure
        if structured_res.status == EvaluationStatus.NOT_SATISFIED:
            fused_status = EvaluationStatus.NOT_SATISFIED
            evaluator = EvaluatorType.SQL
            explanation = (
                structured_res.explanation
                or "The submitted procedure code or diagnosis does not meet policy requirements (deterministic check)."
            )

        # Rule 2: Explicit clinical contradiction / failure in clinical notes
        elif semantic_res.status == EvaluationStatus.NOT_SATISFIED:
            fused_status = EvaluationStatus.NOT_SATISFIED
            evaluator = EvaluatorType.AGENTIC_QWEN
            explanation = (
                semantic_res.explanation
                or "The submitted clinical documentation explicitly contradicts or fails to meet this policy requirement."
            )

        # Rule 3: Both evaluators satisfied
        elif (
            structured_res.status == EvaluationStatus.SATISFIED
            and semantic_res.status == EvaluationStatus.SATISFIED
        ):
            fused_status = EvaluationStatus.SATISFIED
            evaluator = EvaluatorType.SQL if is_code_check else EvaluatorType.AGENTIC_QWEN
            explanation = (
                semantic_res.explanation
                if not is_code_check and semantic_res.explanation
                else structured_res.explanation
                or "The submitted clinical documentation and structured coverage data confirm that this policy requirement is satisfied."
            )

        # Rule 4: Structured satisfied, Semantic unknown
        elif (
            structured_res.status == EvaluationStatus.SATISFIED
            and semantic_res.status == EvaluationStatus.UNKNOWN
        ):
            if is_code_check or not criterion.mandatory:
                # Deterministic code list match or informational criterion
                fused_status = EvaluationStatus.SATISFIED
                evaluator = EvaluatorType.SQL
                explanation = structured_res.explanation or "Requirement is satisfied."
            else:
                # Mandatory clinical requirement: Structured cannot override missing clinical evidence
                fused_status = EvaluationStatus.UNKNOWN
                evaluator = EvaluatorType.AGENTIC_QWEN
                explanation = (
                    "The submitted documentation does not establish whether this clinical requirement is met. "
                    "Additional clinical documentation is needed."
                )

        # Rule 5: Structured unknown, Semantic satisfied
        elif (
            structured_res.status == EvaluationStatus.UNKNOWN
            and semantic_res.status == EvaluationStatus.SATISFIED
        ):
            fused_status = EvaluationStatus.SATISFIED
            evaluator = EvaluatorType.AGENTIC_QWEN
            explanation = (
                semantic_res.explanation
                or "The submitted clinical documentation confirms that this policy requirement is satisfied."
            )

        # Rule 6: Both unknown
        else:
            fused_status = EvaluationStatus.UNKNOWN
            evaluator = EvaluatorType.AGENTIC_QWEN if not is_code_check else EvaluatorType.SQL
            explanation = (
                "The submitted documentation does not establish whether this policy requirement is met. "
                "Additional clinical documentation is needed."
            )

        return EvaluatedCriterion(
            criterion_id=criterion.criterion_id,
            policy_type=criterion.policy_type,
            policy_id=criterion.policy_id,
            criterion=criterion.criterion,
            requirement=criterion.criterion,
            criterion_type=criterion.type,
            evaluator=evaluator,
            status=fused_status,
            patient_evidence=clean_patient_ev,
            policy_evidence=clean_policy_ev,
            explanation=explanation,
            mandatory=criterion.mandatory,
            authoritative=True,
        )

    @staticmethod
    def fuse(criteria: List[EvaluatedCriterion]) -> EvidenceMatrix:
        """Fuse multiple criteria evaluations into a single EvidenceMatrix."""
        matrix = EvidenceMatrix(criteria=criteria)
        for crit in criteria:
            logger.info(
                f"Fusion Log | Criterion: {crit.criterion_id} | Type: {crit.criterion_type.value} "
                f"| Evaluator: {crit.evaluator.value} | Status: {crit.status.value} | Mandatory: {crit.mandatory}"
            )
        return matrix

    @staticmethod
    def resolve_decision(matrix: EvidenceMatrix) -> str:
        """Resolve coverage decision from an EvidenceMatrix.

        Returns: "COVERED", "EXCLUDED", "UNKNOWN", or "NOT_ADDRESSED".
        """
        if not matrix.criteria:
            return "NOT_ADDRESSED"

        mandatory_criteria = [c for c in matrix.criteria if c.mandatory]
        if not mandatory_criteria:
            if any(c.status == EvaluationStatus.SATISFIED for c in matrix.criteria):
                return "COVERED"
            return "NOT_ADDRESSED"

        has_not_satisfied = any(c.status == EvaluationStatus.NOT_SATISFIED for c in mandatory_criteria)
        has_unknown = any(c.status == EvaluationStatus.UNKNOWN for c in mandatory_criteria)
        has_satisfied = any(c.status == EvaluationStatus.SATISFIED for c in mandatory_criteria)

        # 1. Any mandatory NOT_SATISFIED ➔ EXCLUDED
        if has_not_satisfied:
            return "EXCLUDED"

        # 2. Any mandatory UNKNOWN ➔ UNKNOWN
        if has_unknown:
            return "UNKNOWN"

        # 3. All mandatory SATISFIED ➔ COVERED
        if has_satisfied and not has_not_satisfied and not has_unknown:
            return "COVERED"

        return "NOT_ADDRESSED"

