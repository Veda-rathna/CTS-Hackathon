"""Multi-Evaluator Orchestrator.

Orchestrates the evaluation of a list of criteria through the various evaluators.
"""
from __future__ import annotations

import logging
from typing import Any

from app.schemas.evaluation import CriterionEvaluation, EvidenceMatrix
from app.schemas.triage import TriageRequest
from app.services.evaluation.rule_evaluator import RuleEvaluator
from app.services.evaluation.semantic_evaluator import SemanticEvaluator
from app.services.evaluation.structured_evaluator import StructuredEvaluator

logger = logging.getLogger(__name__)


class MultiEvaluator:
    """Orchestrates the evaluation of criteria through all evaluators."""

    def __init__(
        self,
        structured_evaluator: StructuredEvaluator,
        rule_evaluator: RuleEvaluator,
        semantic_evaluator: SemanticEvaluator,
    ) -> None:
        self._structured = structured_evaluator
        self._rule = rule_evaluator
        self._semantic = semantic_evaluator

    def evaluate_all(
        self,
        criteria: list[CriterionEvaluation],
        request: TriageRequest,
        policy_data: Any,
        policy_sections: list[Any],
    ) -> EvidenceMatrix:
        """Run criteria through the appropriate evaluators."""
        evaluated_criteria = []

        for criterion in criteria:
            if criterion.criterion_type == "STRUCTURED":
                c = self._structured.evaluate(criterion, request, policy_data)
                evaluated_criteria.append(c)
                
            elif criterion.criterion_type == "RULE_BASED":
                c = self._rule.evaluate(criterion, request)
                evaluated_criteria.append(c)
                
            elif criterion.criterion_type == "SEMANTIC":
                c = self._semantic.evaluate(criterion, request, policy_sections)
                evaluated_criteria.append(c)
                
            elif criterion.criterion_type == "DOCUMENT":
                # For document criteria, could have a specific evaluator.
                # Default to UNKNOWN if not handled by LLM.
                c = self._semantic.evaluate(criterion, request, policy_sections)
                evaluated_criteria.append(c)
                
            else:
                evaluated_criteria.append(criterion)

        return EvidenceMatrix(criteria=evaluated_criteria)
