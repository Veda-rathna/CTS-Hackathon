"""Semantic Evaluator."""
from __future__ import annotations

from app.schemas.evaluation import EvaluatedCriterion, EvaluationStatus, EvaluatorType, PolicyCriterion
from app.schemas.triage import TriageRequest
from app.services.llm.client import LLMClient

class SemanticEvaluator:
    """Evaluates SEMANTIC criteria using an LLM."""
    
    def __init__(self, llm_client: LLMClient):
        self._client = llm_client
    
    def evaluate(self, criterion: PolicyCriterion, request: TriageRequest) -> EvaluatedCriterion:
        # Note: TriageRequest doesn't explicitly have clinical_notes in the base schema 
        # but the prompt requires clinical facts. 
        # We will attempt to get clinical_notes if it exists, otherwise empty.
        clinical_notes = getattr(request, "clinical_notes", "")
        
        # Call LLM
        response = self._client.evaluate_criterion(
            criterion_text=criterion.criterion,
            clinical_notes=clinical_notes
        )
        
        status_map = {
            "SATISFIED": EvaluationStatus.SATISFIED,
            "NOT_SATISFIED": EvaluationStatus.NOT_SATISFIED,
            "UNKNOWN": EvaluationStatus.UNKNOWN,
        }
        
        status = status_map.get(response.status, EvaluationStatus.UNKNOWN)
        
        # For a purely semantic criterion, the LLM result is authoritative over itself (no SQL layer).
        # But in Evidence Fusion, it will have lower priority than deterministic layers.
        
        return EvaluatedCriterion(
            criterion_id=criterion.criterion_id,
            policy_type=criterion.policy_type,
            policy_id=criterion.policy_id,
            criterion=criterion.criterion,
            criterion_type=criterion.type,
            evaluator=EvaluatorType.LLM,
            status=status,
            patient_evidence=response.patient_evidence,
            policy_evidence=[criterion.source_text] if criterion.source_text else [criterion.criterion],
            authoritative=False, # LLM is never authoritative over explicit logic
            mandatory=True
        )
