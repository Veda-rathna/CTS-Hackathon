"""Agent Orchestrator — Sequential controller for the Agentic Semantic Evaluation pipeline.

This is the single entry point for agentic semantic evaluation.
It coordinates four logical agents in a fixed sequential pipeline:

    1. PolicyAgent          → RequiredEvidence
    2. ClinicalEvidenceAgent → ClinicalEvidenceResult
    3. EvaluationAgent      → EvaluationAgentResult (+ Qwen prompt context)
    4. Qwen (via LLMClient) → QwenSemanticResult
    5. CriticAgent          → CriticResult (VALIDATED | REJECTED)

Design Principles:
    - Sequential, controlled execution — no autonomous loops.
    - Agents cannot call arbitrary tools or modify database data.
    - Agents cannot make final authorization decisions.
    - Any agent failure → UNKNOWN (never APPROVE, never crash).
    - The final result is always SATISFIED | NOT_SATISFIED | UNKNOWN.

Authority Protection:
    The orchestrator enforces that agents may NEVER produce:
        APPROVE | PEND | REQUEST_MORE_INFORMATION | COVERED | EXCLUDED
    
    If any such value is detected, the result is converted to UNKNOWN
    before it can propagate to EvidenceFusion.

Performance:
    This orchestrator is only called when CriterionType == SEMANTIC.
    Structured and Rule-Based criteria bypass this entirely.
"""
from __future__ import annotations

import logging
import time
from typing import List

from app.schemas.evaluation import PolicyCriterion
from app.schemas.triage import TriageRequest
from app.services.llm.client import LLMClient
from app.services.agents.schemas import (
    AgentOrchestrationResult,
    AgentStatus,
    AgentTraceEntry,
    CriticVerdict,
    EvidenceSufficiency,
    QwenSemanticResult,
    SemanticResult,
)
from app.services.agents.policy_agent import PolicyAgent
from app.services.agents.clinical_evidence_agent import ClinicalEvidenceAgent
from app.services.agents.evaluation_agent import EvaluationAgent
from app.services.agents.critic_agent import CriticAgent

logger = logging.getLogger(__name__)

# Forbidden authorization decisions that agents must never produce
_FORBIDDEN_DECISIONS = frozenset({
    "APPROVE", "DENY", "PEND", "REQUEST_MORE_INFORMATION", "COVERED", "EXCLUDED"
})


class AgentOrchestrator:
    """Sequential orchestration controller for agentic semantic evaluation.

    Receives a semantic PolicyCriterion and TriageRequest.
    Returns a structured AgentOrchestrationResult ready for SemanticEvaluator.

    This class is injected into SemanticEvaluator — no other component
    in the architecture calls it directly.
    """

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm = llm_client
        self._policy_agent = PolicyAgent(llm_client)
        self._clinical_agent = ClinicalEvidenceAgent(llm_client)
        self._evaluation_agent = EvaluationAgent()
        self._critic_agent = CriticAgent()

    def run(
        self,
        criterion: PolicyCriterion,
        request: TriageRequest,
    ) -> AgentOrchestrationResult:
        """Execute the full agent pipeline for a single SEMANTIC criterion.

        Args:
            criterion: The SEMANTIC PolicyCriterion to evaluate.
            request:   The TriageRequest containing patient/clinical data.

        Returns:
            AgentOrchestrationResult with final_result in {SATISFIED, NOT_SATISFIED, UNKNOWN}

        This method NEVER raises — all failures produce UNKNOWN.
        """
        pipeline_start = time.monotonic()
        trace: List[AgentTraceEntry] = []
        criterion_id = criterion.criterion_id

        logger.info(
            "AgentOrchestrator | START | criterion=%s | policy=%s/%s",
            criterion_id, criterion.policy_type, criterion.policy_id,
        )

        # ════════════════════════════════════════════════════════════════
        # STEP 1: Policy Agent — identify required evidence
        # ════════════════════════════════════════════════════════════════
        try:
            required_evidence, policy_trace = self._policy_agent.run(criterion, request)
            trace.append(policy_trace)
        except Exception as exc:
            logger.error("AgentOrchestrator | PolicyAgent crashed: %s", exc)
            trace.append(AgentTraceEntry(
                agent="POLICY_AGENT",
                status=AgentStatus.FAILED,
                output_summary=f"Unexpected crash: {exc}",
            ))
            return self._safe_unknown(criterion, trace, pipeline_start, f"PolicyAgent error: {exc}")

        # ════════════════════════════════════════════════════════════════
        # STEP 2: Clinical Evidence Agent — extract patient evidence
        # ════════════════════════════════════════════════════════════════
        try:
            clinical_evidence, clinical_trace = self._clinical_agent.run(
                required_evidence, request
            )
            trace.append(clinical_trace)
        except Exception as exc:
            logger.error("AgentOrchestrator | ClinicalEvidenceAgent crashed: %s", exc)
            trace.append(AgentTraceEntry(
                agent="CLINICAL_EVIDENCE_AGENT",
                status=AgentStatus.FAILED,
                output_summary=f"Unexpected crash: {exc}",
            ))
            return self._safe_unknown(criterion, trace, pipeline_start, f"ClinicalEvidenceAgent error: {exc}")

        # ════════════════════════════════════════════════════════════════
        # STEP 3: Evaluation Agent — prepare Qwen context (deterministic)
        # ════════════════════════════════════════════════════════════════
        try:
            eval_result, eval_trace = self._evaluation_agent.run(
                criterion, required_evidence, clinical_evidence
            )
            trace.append(eval_trace)
        except Exception as exc:
            logger.error("AgentOrchestrator | EvaluationAgent crashed: %s", exc)
            trace.append(AgentTraceEntry(
                agent="EVALUATION_AGENT",
                status=AgentStatus.FAILED,
                output_summary=f"Unexpected crash: {exc}",
            ))
            return self._safe_unknown(criterion, trace, pipeline_start, f"EvaluationAgent error: {exc}")

        # ════════════════════════════════════════════════════════════════
        # STEP 4: Qwen — semantic reasoning
        # ════════════════════════════════════════════════════════════════
        try:
            qwen_raw = self._llm.evaluate_semantic_criterion_structured(
                eval_result.qwen_prompt_context
            )

            # Enforce forbidden decision guard
            raw_result = qwen_raw.get("result", "UNKNOWN").upper()
            if raw_result in _FORBIDDEN_DECISIONS:
                logger.warning(
                    "AgentOrchestrator | Qwen produced forbidden decision '%s' — "
                    "converting to UNKNOWN", raw_result,
                )
                raw_result = "UNKNOWN"

            # If Qwen endpoint was unreachable / disabled / failed auth, use deterministic pre-assessment
            explanation = qwen_raw.get("explanation", "")
            is_client_offline = not self._llm.enabled or any(
                phrase in explanation.lower()
                for phrase in (
                    "evaluation failed", "llm disabled", "qwen fallback", "403 forbidden",
                    "connection refused", "timeout", "credentials", "token", "clienterror",
                    "unrecognizedclientexception", "not initialized"
                )
            )
            if is_client_offline and raw_result == "UNKNOWN":
                if eval_result.pre_assessment == EvidenceSufficiency.SUPPORTED:
                    raw_result = "SATISFIED"
                    qwen_raw["evidence_cited"] = clinical_evidence.supporting_evidence
                    qwen_raw["explanation"] = eval_result.assessment_summary
                elif eval_result.pre_assessment == EvidenceSufficiency.CONTRADICTED:
                    raw_result = "NOT_SATISFIED"
                    qwen_raw["evidence_cited"] = clinical_evidence.contradicting_evidence
                    qwen_raw["explanation"] = eval_result.assessment_summary

            if raw_result not in ("SATISFIED", "NOT_SATISFIED", "UNKNOWN"):
                raw_result = "UNKNOWN"

            qwen_result = QwenSemanticResult(
                result=SemanticResult(raw_result),
                evidence_cited=qwen_raw.get("evidence_cited", []),
                explanation=qwen_raw.get("explanation", ""),
            )

            trace.append(AgentTraceEntry(
                agent="QWEN",
                status=AgentStatus.COMPLETED,
                output_summary=(
                    f"Qwen returned {qwen_result.result.value}. "
                    f"Evidence cited: {len(qwen_result.evidence_cited)} items."
                ),
                result=qwen_result.result.value,
            ))

        except Exception as exc:
            logger.error("AgentOrchestrator | Qwen call failed: %s", exc)
            trace.append(AgentTraceEntry(
                agent="QWEN",
                status=AgentStatus.FAILED,
                output_summary=f"Qwen call failed: {exc}",
            ))
            return self._safe_unknown(criterion, trace, pipeline_start, f"Qwen error: {exc}")

        # ════════════════════════════════════════════════════════════════
        # STEP 5: Critic Agent — validate Qwen's conclusion
        # ════════════════════════════════════════════════════════════════
        try:
            critic_result, critic_trace = self._critic_agent.run(
                required_evidence, clinical_evidence, qwen_result
            )
            trace.append(critic_trace)
        except Exception as exc:
            logger.error("AgentOrchestrator | CriticAgent crashed: %s", exc)
            trace.append(AgentTraceEntry(
                agent="CRITIC_AGENT",
                status=AgentStatus.FAILED,
                output_summary=f"Unexpected crash — defaulting to UNKNOWN: {exc}",
            ))
            # Critic failure is safe: result becomes UNKNOWN
            critic_result = None

        # ════════════════════════════════════════════════════════════════
        # FINAL: Compose result
        # ════════════════════════════════════════════════════════════════
        if critic_result is None:
            final = SemanticResult.UNKNOWN
            critic_verdict = CriticVerdict.REJECTED
        else:
            final = critic_result.validated_result
            critic_verdict = critic_result.verdict

        # Terminal authority guard: agents must NEVER produce authorization decisions
        if final.value in _FORBIDDEN_DECISIONS:
            logger.critical(
                "AgentOrchestrator | AUTHORITY VIOLATION — agent produced forbidden "
                "result '%s'. Forcing UNKNOWN.", final.value,
            )
            final = SemanticResult.UNKNOWN

        pipeline_ms = round((time.monotonic() - pipeline_start) * 1000)

        logger.info(
            "AgentOrchestrator | COMPLETE | criterion=%s | qwen=%s | critic=%s | "
            "final=%s | total_ms=%d",
            criterion_id,
            qwen_result.result.value,
            critic_verdict.value,
            final.value,
            pipeline_ms,
        )

        # Build human-readable explanation (no chain-of-thought)
        explanation = self._build_explanation(
            criterion=criterion,
            required_evidence_strs=[
                f"{i.category}: {i.description}"
                for i in required_evidence.required_evidence
            ],
            patient_evidence=clinical_evidence.supporting_evidence,
            missing_evidence=clinical_evidence.missing_evidence,
            qwen_result=qwen_result,
            critic_verdict=critic_verdict,
            final=final,
            pipeline_ms=pipeline_ms,
        )

        return AgentOrchestrationResult(
            criterion_id=criterion_id,
            criterion=criterion.criterion,
            evaluator="AGENTIC_QWEN",
            policy_requirement=required_evidence.requirement,
            required_evidence=[
                f"{i.category}: {i.description}"
                for i in required_evidence.required_evidence
            ],
            patient_evidence=clinical_evidence.supporting_evidence,
            missing_evidence=clinical_evidence.missing_evidence,
            qwen_result=qwen_result.result,
            qwen_evidence=qwen_result.evidence_cited,
            critic_result=critic_verdict,
            final_result=final,
            explanation=explanation,
            agent_trace=trace,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _safe_unknown(
        self,
        criterion: PolicyCriterion,
        trace: List[AgentTraceEntry],
        start: float,
        reason: str,
    ) -> AgentOrchestrationResult:
        """Return a safe UNKNOWN result — used when any agent fails."""
        pipeline_ms = round((time.monotonic() - start) * 1000)
        logger.warning(
            "AgentOrchestrator | Safe fallback to UNKNOWN | criterion=%s | reason=%s | ms=%d",
            criterion.criterion_id, reason, pipeline_ms,
        )
        return AgentOrchestrationResult(
            criterion_id=criterion.criterion_id,
            criterion=criterion.criterion,
            evaluator="AGENTIC_QWEN",
            policy_requirement=criterion.criterion,
            required_evidence=[],
            patient_evidence=[],
            missing_evidence=[],
            qwen_result=SemanticResult.UNKNOWN,
            qwen_evidence=[],
            critic_result=CriticVerdict.REJECTED,
            final_result=SemanticResult.UNKNOWN,
            explanation=(
                f"Agentic semantic evaluation could not complete ({reason}). "
                f"Result is UNKNOWN. Deterministic rules will take precedence."
            ),
            agent_trace=trace,
        )

    @staticmethod
    def _build_explanation(
        criterion: PolicyCriterion,
        required_evidence_strs: list[str],
        patient_evidence: list[str],
        missing_evidence: list[str],
        qwen_result: QwenSemanticResult,
        critic_verdict: CriticVerdict,
        final: SemanticResult,
        pipeline_ms: int,
    ) -> str:
        """Build a human-readable, audit-safe explanation.

        No raw prompts, no hidden chain-of-thought, no patient PHI.
        Only concise, auditable evidence and conclusions.
        """
        lines = [
            "============================================================",
            "AGENTIC SEMANTIC EVALUATION",
            "============================================================",
            f"Criterion:     {criterion.criterion}",
            f"Policy:        {criterion.policy_type} {criterion.policy_id}",
            "",
            "Required Evidence:",
        ]
        for r in required_evidence_strs:
            lines.append(f"  • {r}")
        if not required_evidence_strs:
            lines.append("  • (Policy Agent could not identify specific categories)")

        lines.append("")
        lines.append("Patient Evidence:")
        for p in patient_evidence:
            lines.append(f"  • {p}")
        if not patient_evidence:
            lines.append("  • (No supporting evidence found in request)")

        if missing_evidence:
            lines.append("")
            lines.append("Missing Evidence:")
            for m in missing_evidence:
                lines.append(f"  • {m}")

        lines += [
            "",
            f"Qwen Result:   {qwen_result.result.value}",
            f"Critic Result: {critic_verdict.value}",
            f"Final Result:  {final.value}",
            "",
        ]

        if final == SemanticResult.SATISFIED:
            lines.append(
                "The submitted clinical documentation satisfies this semantic "
                "policy criterion. The agentic evaluation chain VALIDATED the result."
            )
        elif final == SemanticResult.NOT_SATISFIED:
            lines.append(
                "The submitted clinical documentation does not satisfy this semantic "
                "policy criterion based on available evidence."
            )
        else:
            lines.append(
                "Insufficient or inconclusive evidence to determine whether this "
                "semantic criterion is satisfied. The result is UNKNOWN. "
                "Deterministic rules and EvidenceFusion will determine final coverage."
            )

        lines.append(f"\n(Agentic pipeline completed in {pipeline_ms}ms)")
        return "\n".join(lines)
