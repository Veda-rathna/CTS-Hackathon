"""Multi-Evaluator executing Structured (SQL) and Semantic (LLM/Agentic) evaluation with EvidenceFusion."""
from __future__ import annotations

from app.schemas.evaluation import CriterionType, EvaluatedCriterion, EvaluationStatus, EvaluatorType, PolicyCriterion
from app.schemas.triage import TriageRequest
from .structured_evaluator import StructuredEvaluator
from .semantic_evaluator import SemanticEvaluator
from .evidence_fusion import EvidenceFusion


class MultiEvaluator:
    """Executes both StructuredEvaluator and SemanticEvaluator and fuses results."""

    def __init__(
        self,
        structured_evaluator: StructuredEvaluator,
        semantic_evaluator: SemanticEvaluator | None = None,
    ):
        self._structured = structured_evaluator
        self._semantic = semantic_evaluator

    def evaluate(self, criterion: PolicyCriterion, request: TriageRequest) -> EvaluatedCriterion:
        """Execute both structured and semantic evaluation, then fuse with EvidenceFusion.

        Every criterion is evaluated by both Structured and Semantic pipelines,
        passing both results into EvidenceFusion for deterministic authority resolution.
        """
        # 1. Always execute Structured / SQL Evaluation
        structured_result = self._structured.evaluate(criterion, request)

        # 2. Always execute Semantic / Agentic Evaluation
        if self._semantic is not None:
            semantic_result = self._semantic.evaluate(criterion, request)
        else:
            semantic_result = EvaluatedCriterion(
                criterion_id=criterion.criterion_id,
                policy_type=criterion.policy_type,
                policy_id=criterion.policy_id,
                criterion=criterion.criterion,
                requirement=criterion.criterion,
                criterion_type=CriterionType.SEMANTIC,
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

        # 3. Consolidate via EvidenceFusion
        return EvidenceFusion.fuse_criterion(structured_result, semantic_result, criterion)
