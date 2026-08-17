"""Evaluation Agent — Agent 3 of the Agentic Semantic Evaluation pipeline.

Purpose:
    Compare the policy requirement against patient/request evidence and
    prepare a structured, deterministic evaluation context for Qwen.

This agent is PURELY DETERMINISTIC — it makes NO LLM calls.
It produces a pre-assessment and structures the prompt context for Qwen.

Input:
    - PolicyCriterion (criterion text, source policy text)
    - RequiredEvidence (from Policy Agent)
    - ClinicalEvidenceResult (from Clinical Evidence Agent)

Output:
    EvaluationAgentResult — structured context + pre-assessment for Qwen.

Key Behaviors:
    - If supporting_evidence is non-empty and missing_evidence is empty →
      pre-assessment = SUPPORTED
    - If contradicting_evidence is non-empty →
      pre-assessment = CONTRADICTED
    - If missing_evidence is non-empty and supporting_evidence is empty →
      pre-assessment = INSUFFICIENT_EVIDENCE
    - Mixed cases → INSUFFICIENT_EVIDENCE (conservative)

The Evaluation Agent does NOT make the final criterion decision.
Qwen makes the semantic judgment using the prepared context.
"""
from __future__ import annotations

import logging
import time

from app.schemas.evaluation import PolicyCriterion
from app.services.agents.schemas import (
    AgentStatus,
    AgentTraceEntry,
    ClinicalEvidenceResult,
    EvaluationAgentResult,
    EvidenceSufficiency,
    RequiredEvidence,
)

logger = logging.getLogger(__name__)


# ── Qwen prompt template ──────────────────────────────────────────────────────
# Structured context sent to Qwen.
# Patient text appears ONLY as pre-extracted evidence lists — NOT as raw notes.
# This prevents Qwen from treating patient instructions as execution targets.

_QWEN_PROMPT_TEMPLATE = """\
POLICY REQUIREMENT:
{requirement}

POLICY EVIDENCE:
{policy_source}

REQUIRED EVIDENCE CATEGORIES:
{required_list}

SUPPORTING PATIENT EVIDENCE:
{supporting_list}

CONTRADICTING PATIENT EVIDENCE:
{contradicting_list}

MISSING EVIDENCE:
{missing_list}

DETERMINISTIC EVIDENCE PRE-ASSESSMENT:
{pre_assessment}

TASK:
Determine whether the available patient evidence satisfies this specific policy criterion.

ALLOWED RESULTS (respond with exactly one):
SATISFIED — the available evidence clearly satisfies the policy requirement
NOT_SATISFIED — the evidence clearly contradicts or negates the requirement
UNKNOWN — evidence is insufficient, ambiguous, or not available

FORBIDDEN RESULTS (do not use):
APPROVE, DENY, PEND, REQUEST_MORE_INFORMATION, COVERED, EXCLUDED

Respond with a JSON object:
{{
  "result": "SATISFIED" | "NOT_SATISFIED" | "UNKNOWN",
  "evidence_cited": ["specific evidence from the supporting list"],
  "explanation": "one concise sentence explaining your conclusion"
}}"""


class EvaluationAgent:
    """Agent 3: Prepares structured evaluation context for Qwen.

    This agent is deterministic — no LLM calls.
    It answers: 'Does the evidence appear to support the policy requirement?'
    and prepares the Qwen prompt context.
    """

    def run(
        self,
        criterion: PolicyCriterion,
        required_evidence: RequiredEvidence,
        clinical_evidence: ClinicalEvidenceResult,
    ) -> tuple[EvaluationAgentResult, AgentTraceEntry]:
        """Produce a pre-assessment and Qwen prompt context.

        Returns:
            Tuple of (EvaluationAgentResult, AgentTraceEntry)
        """
        start = time.monotonic()

        supporting = clinical_evidence.supporting_evidence
        contradicting = clinical_evidence.contradicting_evidence
        missing = clinical_evidence.missing_evidence

        # ── Deterministic pre-assessment ──────────────────────────────────────
        if contradicting:
            pre_assessment = EvidenceSufficiency.CONTRADICTED
            assessment_summary = (
                f"Contradicting evidence found ({len(contradicting)} items). "
                f"Policy requirement appears NOT satisfied."
            )
        elif supporting and not missing:
            pre_assessment = EvidenceSufficiency.SUPPORTED
            assessment_summary = (
                f"Supporting evidence found ({len(supporting)} items). "
                f"No missing evidence categories. Policy requirement may be satisfied."
            )
        elif supporting and missing:
            # Mixed: some support, some missing — conservative assessment
            pre_assessment = EvidenceSufficiency.INSUFFICIENT_EVIDENCE
            assessment_summary = (
                f"Partial evidence: {len(supporting)} supporting items found, "
                f"but {len(missing)} required evidence categories are missing. "
                f"Evidence is insufficient for a definitive conclusion."
            )
        else:
            pre_assessment = EvidenceSufficiency.INSUFFICIENT_EVIDENCE
            assessment_summary = (
                f"No supporting evidence found. "
                f"{len(missing)} required evidence categories are missing."
            )

        # ── Build Qwen prompt context ─────────────────────────────────────────
        required_list = "\n".join(
            f"  • [{item.category}] {item.description}"
            for item in required_evidence.required_evidence
        ) or "  • (No specific categories identified)"

        supporting_list = (
            "\n".join(f"  • {s}" for s in supporting)
            if supporting else "  • (None found)"
        )
        contradicting_list = (
            "\n".join(f"  • {c}" for c in contradicting)
            if contradicting else "  • (None found)"
        )
        missing_list = (
            "\n".join(f"  • {m}" for m in missing)
            if missing else "  • (None)"
        )

        policy_source = criterion.source_text or criterion.criterion

        qwen_context = _QWEN_PROMPT_TEMPLATE.format(
            requirement=required_evidence.requirement,
            policy_source=policy_source,
            required_list=required_list,
            supporting_list=supporting_list,
            contradicting_list=contradicting_list,
            missing_list=missing_list,
            pre_assessment=pre_assessment.value,
        )

        latency = round((time.monotonic() - start) * 1000)

        logger.info(
            "EvaluationAgent | criterion=%s | pre_assessment=%s | "
            "supporting=%d | contradicting=%d | missing=%d | latency_ms=%d",
            criterion.criterion_id, pre_assessment.value,
            len(supporting), len(contradicting), len(missing), latency,
        )

        result = EvaluationAgentResult(
            pre_assessment=pre_assessment,
            qwen_prompt_context=qwen_context,
            assessment_summary=assessment_summary,
        )

        trace = AgentTraceEntry(
            agent="EVALUATION_AGENT",
            status=AgentStatus.COMPLETED,
            output_summary=assessment_summary,
        )

        return result, trace
