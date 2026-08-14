"""Multi-Evaluator using the Strategy Pattern."""
from __future__ import annotations

from app.schemas.evaluation import CriterionType, EvaluatedCriterion, PolicyCriterion
from app.schemas.triage import TriageRequest
from .structured_evaluator import StructuredEvaluator
from .rule_evaluator import RuleEvaluator
from .semantic_evaluator import SemanticEvaluator

class MultiEvaluator:
    """Routes evaluation to the correct specialized evaluator."""
    
    def __init__(self, 
                 structured_evaluator: StructuredEvaluator,
                 rule_evaluator: RuleEvaluator,
                 semantic_evaluator: SemanticEvaluator):
        self._structured = structured_evaluator
        self._rule = rule_evaluator
        self._semantic = semantic_evaluator
        
    def evaluate(self, criterion: PolicyCriterion, request: TriageRequest) -> EvaluatedCriterion:
        """Route the criterion to the correct evaluator."""
        
        if criterion.type == CriterionType.STRUCTURED:
            return self._structured.evaluate(criterion, request)
            
        elif criterion.type == CriterionType.RULE_BASED:
            return self._rule.evaluate(criterion, request)
            
        elif criterion.type == CriterionType.SEMANTIC:
            return self._semantic.evaluate(criterion, request)
            
        raise ValueError(f"Unknown criterion type: {criterion.type}")
