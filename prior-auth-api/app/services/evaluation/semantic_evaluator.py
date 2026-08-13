"""Semantic Evaluator.

Evaluates SEMANTIC criteria using the LLM Client.
If the LLM is unavailable or disabled, gracefully degrades by returning UNKNOWN
for these criteria without crashing the overall evaluation pipeline.
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.config import Settings
from app.schemas.evaluation import CriterionEvaluation
from app.schemas.triage import TriageRequest
from app.services.llm.llm_client import LLMClient

logger = logging.getLogger(__name__)


class SemanticEvaluator:
    """Evaluates SEMANTIC criteria."""

    def __init__(self, llm_client: LLMClient, settings: Settings) -> None:
        self._llm_client = llm_client
        self._settings = settings

    def evaluate(
        self,
        criterion: CriterionEvaluation,
        request: TriageRequest,
        policy_sections: list[Any],
    ) -> CriterionEvaluation:
        """Evaluate a single semantic criterion using the LLM."""
        if criterion.criterion_type != "SEMANTIC":
            return criterion

        # Check if LLM is enabled
        if not self._settings.llm_enabled:
            criterion.status = "UNKNOWN"
            criterion.explanation = "LLM evaluation is disabled. Semantic criteria cannot be evaluated."
            return criterion

        # Check if we have clinical notes to evaluate against
        if not request.clinical_notes:
            criterion.status = "UNKNOWN"
            criterion.explanation = "No clinical notes provided for semantic evaluation."
            return criterion

        # Build policy context from relevant RAG sections (if available)
        policy_context = ""
        if policy_sections:
            # We want to provide the LLM with the context from the policy where this criterion came from
            source_section = criterion.source.section
            relevant_chunks = [
                s.content for s in policy_sections 
                if getattr(s, "section", getattr(s, "section_type", "")) == source_section
            ]
            if relevant_chunks:
                policy_context = "\n\n".join(relevant_chunks)
            else:
                # Fallback to all sections if we can't match exactly
                policy_context = "\n\n".join([s.content for s in policy_sections])
                
        if not policy_context:
            policy_context = "No specific policy text context provided."

        # Call the LLM
        result = self._llm_client.evaluate_criterion(criterion, request, policy_context)
        
        criterion.status = result.get("status", "UNKNOWN")
        criterion.patient_evidence = result.get("patient_evidence", [])
        criterion.policy_evidence = result.get("policy_evidence", [])
        # No explanation generated for semantic criteria per requirements.

        return criterion
