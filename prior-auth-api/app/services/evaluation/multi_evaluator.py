"""Multi-Evaluator using the Strategy Pattern."""
from __future__ import annotations

from typing import Any

from app.schemas.evaluation import CriterionType, EvaluatedCriterion, PolicyCriterion
from app.schemas.triage import TriageRequest
from .structured_evaluator import StructuredEvaluator
from .rule_evaluator import RuleEvaluator
from .semantic_evaluator import SemanticEvaluator

class MultiEvaluator:
    """Routes evaluation to StructuredEvaluator or SemanticEvaluator."""

    def __init__(
        self,
        structured_evaluator: StructuredEvaluator,
        semantic_evaluator: SemanticEvaluator | None = None,
        rule_evaluator: Any = None,
    ):
        if semantic_evaluator is None and isinstance(rule_evaluator, SemanticEvaluator):
            self._semantic = rule_evaluator
        else:
            self._semantic = semantic_evaluator
        self._structured = structured_evaluator

    def evaluate(self, criterion: PolicyCriterion, request: TriageRequest) -> EvaluatedCriterion:
        """Route the criterion to the correct evaluator."""
        if criterion.type == CriterionType.STRUCTURED:
            return self._structured.evaluate(criterion, request)
        else:
            return self._semantic.evaluate(criterion, request)
            
        raise ValueError(f"Unknown criterion type: {criterion.type}")
