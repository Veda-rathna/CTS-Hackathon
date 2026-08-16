"""Semantic Evaluator — enhanced with Agentic Semantic Evaluation pipeline.

This evaluator handles SEMANTIC policy criteria by routing them through
the AgentOrchestrator (4-agent pipeline: PolicyAgent → ClinicalEvidenceAgent
→ EvaluationAgent → Qwen → CriticAgent).

External interface UNCHANGED:
    evaluate(criterion: PolicyCriterion, request: TriageRequest) → EvaluatedCriterion

The MultiEvaluator and TriageService require zero modification.
EvidenceFusion and DecisionEngine remain the sole authority over coverage decisions.

Authority:
    - agentic_semantic result is NEVER authoritative (authoritative=False)
    - SQL / Rule-Based results can always override it in EvidenceFusion
    - DecisionEngine remains the only component producing APPROVE/PEND/RMI

Failure Safety:
    - AgentOrchestrator failure → UNKNOWN
    - Propagates correctly through EvidenceFusion → NOT_ADDRESSED
    - Never crashes the authorization request
"""
from __future__ import annotations

import logging

from app.schemas.evaluation import (
    EvaluatedCriterion,
    EvaluationStatus,
    EvaluatorType,
    PolicyCriterion,
)
from app.schemas.triage import TriageRequest
from app.services.llm.client import LLMClient
from app.services.agents.agent_orchestrator import AgentOrchestrator
from app.services.agents.schemas import SemanticResult

logger = logging.getLogger(__name__)


class SemanticEvaluator:
    """Evaluates SEMANTIC criteria using the Agentic Semantic Evaluation pipeline.

    Replaces the flat LLM call with a controlled 4-agent orchestration:

        PolicyAgent → ClinicalEvidenceAgent → EvaluationAgent → Qwen → CriticAgent

    The external interface is unchanged — MultiEvaluator calls evaluate() identically.
    """

    def __init__(self, llm_client: LLMClient) -> None:
        self._client = llm_client
        self._orchestrator = AgentOrchestrator(llm_client)

    def evaluate(
        self,
        criterion: PolicyCriterion,
        request: TriageRequest,
    ) -> EvaluatedCriterion:
        """Route SEMANTIC criterion through the agentic pipeline.

        Returns an EvaluatedCriterion with:
          - evaluator = AGENTIC_QWEN
          - authoritative = False  (LLM never overrides deterministic evidence)
          - status from {SATISFIED, NOT_SATISFIED, UNKNOWN}
          - structured patient_evidence and policy_evidence lists
          - human-readable explanation with agent trace summary

        This method never raises — all failures produce UNKNOWN.
        """
        logger.info(
            "SemanticEvaluator | criterion=%s | policy=%s/%s",
            criterion.criterion_id,
            criterion.policy_type,
            criterion.policy_id,
        )

        # Run the agentic pipeline
        orchestration = self._orchestrator.run(criterion, request)

        # Map semantic result to EvaluationStatus
        status_map = {
            SemanticResult.SATISFIED: EvaluationStatus.SATISFIED,
            SemanticResult.NOT_SATISFIED: EvaluationStatus.NOT_SATISFIED,
            SemanticResult.UNKNOWN: EvaluationStatus.UNKNOWN,
        }
        status = status_map.get(orchestration.final_result, EvaluationStatus.UNKNOWN)

        # Clean nurse/provider-facing explanation (no raw traces or internal tags)
        full_explanation = orchestration.explanation.strip()
        if not full_explanation:
            if status == EvaluationStatus.SATISFIED:
                full_explanation = "Clinical documentation satisfies the semantic policy requirements."
            elif status == EvaluationStatus.NOT_SATISFIED:
                full_explanation = "Clinical documentation does not meet the necessary criteria described in the policy."
            else:
                full_explanation = "Clinical documentation is insufficient or missing to confirm this requirement."


        # Policy evidence = source policy text + required evidence categories
        policy_evidence_items = []
        if criterion.source_text:
            policy_evidence_items.append(criterion.source_text[:500])  # Truncate for safety
        if orchestration.required_evidence:
            policy_evidence_items.extend(
                [f"Required: {r}" for r in orchestration.required_evidence[:5]]
            )
        if not policy_evidence_items:
            policy_evidence_items = [criterion.criterion]

        logger.info(
            "SemanticEvaluator | criterion=%s | final_status=%s | "
            "qwen=%s | critic=%s",
            criterion.criterion_id,
            status.value,
            orchestration.qwen_result.value,
            orchestration.critic_result.value,
        )

        return EvaluatedCriterion(
            criterion_id=criterion.criterion_id,
            policy_type=criterion.policy_type,
            policy_id=criterion.policy_id,
            criterion=criterion.criterion,
            criterion_type=criterion.type,
            evaluator=EvaluatorType.AGENTIC_QWEN,
            status=status,
            patient_evidence=orchestration.patient_evidence,
            policy_evidence=policy_evidence_items,
            explanation=full_explanation,
            authoritative=False,   # LLM/agents are NEVER authoritative over deterministic evidence
            mandatory=criterion.mandatory,
        )
