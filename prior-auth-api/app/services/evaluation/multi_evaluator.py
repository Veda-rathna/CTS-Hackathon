"""Multi-Evaluator using the Strategy Pattern.

Routes evaluation criteria to the correct evaluator:
  - STRUCTURED → StructuredEvaluator (deterministic SQL)
  - SEMANTIC   → SemanticEvaluator   (4-agent Qwen pipeline)

RULE_BASED has been removed; all non-structured criteria go to SemanticEvaluator.
"""
from __future__ import annotations

from app.schemas.evaluation import CriterionType, EvaluatedCriterion, PolicyCriterion
from app.schemas.triage import TriageRequest
from .structured_evaluator import StructuredEvaluator
from .semantic_evaluator import SemanticEvaluator


class MultiEvaluator:
    """Routes evaluation to StructuredEvaluator or SemanticEvaluator."""

    def __init__(
        self,
        structured_evaluator: StructuredEvaluator,
        semantic_evaluator: SemanticEvaluator | None = None,
    ):
        self._structured = structured_evaluator
        self._semantic = semantic_evaluator

    def evaluate(self, criterion: PolicyCriterion, request: TriageRequest) -> EvaluatedCriterion:
        """Route the criterion to the correct evaluator.

        STRUCTURED → StructuredEvaluator (authoritative, deterministic)
        SEMANTIC   → SemanticEvaluator   (non-authoritative, agentic)

        If no SemanticEvaluator is configured, semantic criteria return UNKNOWN.
        """
        if criterion.type == CriterionType.STRUCTURED:
            return self._structured.evaluate(criterion, request)

        # SEMANTIC path — route through agentic pipeline if available
        if self._semantic is not None:
            return self._semantic.evaluate(criterion, request)

        # Fallback: no semantic evaluator configured → UNKNOWN
        from app.schemas.evaluation import EvaluatedCriterion, EvaluationStatus, EvaluatorType
        return EvaluatedCriterion(
            criterion_id=criterion.criterion_id,
            policy_type=criterion.policy_type,
            policy_id=criterion.policy_id,
            criterion=criterion.criterion,
            criterion_type=criterion.type,
            evaluator=EvaluatorType.AGENTIC_QWEN,
            status=EvaluationStatus.UNKNOWN,
            patient_evidence=[],
            policy_evidence=[criterion.criterion],
            explanation=(
                "No semantic evaluator is configured. "
                "The criterion cannot be evaluated — result is UNKNOWN."
            ),
            authoritative=False,
            mandatory=criterion.mandatory,
        )
