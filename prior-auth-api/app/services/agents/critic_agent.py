"""Critic Agent — Agent 4 of the Agentic Semantic Evaluation pipeline.

Purpose:
    Validate Qwen's semantic conclusion before it enters the evidence pipeline.

Input:
    - PolicyCriterion
    - RequiredEvidence (from Policy Agent)
    - ClinicalEvidenceResult (from Clinical Evidence Agent)
    - QwenSemanticResult

Output:
    CriticResult — VALIDATED or REJECTED.

Validation Checks:
    1. Is the conclusion consistent with available evidence?
    2. Is patient evidence actually present in the request?
    3. Did Qwen invent evidence (hallucination check)?
    4. Did Qwen confuse absence of evidence with evidence of absence?
    5. Did Qwen interpret the allowed result correctly?

If REJECTED:
    - The semantic result becomes UNKNOWN.
    - The system does NOT crash.
    - The authorization request continues through EvidenceFusion.
    - This NEVER causes an automatic APPROVE.

The Critic Agent is DETERMINISTIC for most checks — it uses the LLM
only for the hallucination check (verifying cited evidence exists).
"""
from __future__ import annotations

import logging
import re
import time
from typing import List

from app.services.agents.schemas import (
    AgentStatus,
    AgentTraceEntry,
    ClinicalEvidenceResult,
    CriticResult,
    CriticVerdict,
    QwenSemanticResult,
    RequiredEvidence,
    SemanticResult,
)
from app.services.agents.clinical_evidence_agent import _expand_medical_synonyms

logger = logging.getLogger(__name__)

# Evidence cited by Qwen is considered hallucinated if fewer than this fraction
# of its key words appear in the original clinical notes.
_HALLUCINATION_WORD_MATCH_THRESHOLD = 0.35


def _word_presence_ratio(cited: str, source_text: str) -> float:
    """Return the fraction of meaningful words in `cited` that appear in `source_text`."""
    source_lower = _expand_medical_synonyms(source_text or "").lower()
    words = [w.lower() for w in re.findall(r'\b\w{4,}\b', cited)]
    if not words:
        return 1.0  # Very short/no meaningful words — don't penalize
    matches = sum(1 for w in words if w in source_lower)
    return matches / len(words)


class CriticAgent:
    """Agent 4: Validates Qwen's semantic conclusion.

    This agent answers: 'Is Qwen's conclusion trustworthy given the evidence?'
    If the conclusion fails validation, it becomes UNKNOWN — never APPROVE.
    """

    def run(
        self,
        required_evidence: RequiredEvidence,
        clinical_evidence: ClinicalEvidenceResult,
        qwen_result: QwenSemanticResult,
    ) -> tuple[CriticResult, AgentTraceEntry]:
        """Validate Qwen's semantic result.

        Returns:
            Tuple of (CriticResult, AgentTraceEntry)
        """
        start = time.monotonic()
        checks_performed: List[str] = []
        rejection_reasons: List[str] = []
        clinical_text = clinical_evidence.raw_clinical_text

        # ── Check 0: Forbidden result values ─────────────────────────────────
        forbidden = {"APPROVE", "DENY", "PEND", "REQUEST_MORE_INFORMATION", "COVERED", "EXCLUDED"}
        if qwen_result.result.value.upper() in forbidden:
            rejection_reasons.append(
                f"Qwen returned a forbidden authorization decision: '{qwen_result.result.value}'. "
                f"Agents may only return SATISFIED / NOT_SATISFIED / UNKNOWN."
            )
            checks_performed.append("CHECK_0: Forbidden result value — FAILED")
        else:
            checks_performed.append("CHECK_0: Result value is allowed — PASSED")

        # ── Check 1: SATISFIED requires supporting evidence ───────────────────
        if qwen_result.result == SemanticResult.SATISFIED:
            if not clinical_evidence.supporting_evidence and not qwen_result.evidence_cited:
                rejection_reasons.append(
                    "Qwen returned SATISFIED but no supporting evidence was identified "
                    "by the Clinical Evidence Agent or cited by Qwen itself."
                )
                checks_performed.append("CHECK_1: SATISFIED requires supporting evidence — FAILED")
            else:
                checks_performed.append("CHECK_1: SATISFIED has supporting evidence — PASSED")
        else:
            checks_performed.append("CHECK_1: Result is not SATISFIED — skipped")

        # ── Check 2: NOT_SATISFIED requires contradicting or missing evidence ─
        if qwen_result.result == SemanticResult.NOT_SATISFIED:
            has_contradicting = bool(clinical_evidence.contradicting_evidence)
            has_missing = bool(clinical_evidence.missing_evidence)
            if not has_contradicting and not has_missing and clinical_evidence.supporting_evidence:
                # Qwen said NOT_SATISFIED but we have supporting evidence and nothing missing
                rejection_reasons.append(
                    "Qwen returned NOT_SATISFIED but supporting evidence was found "
                    "and no evidence is missing. Conclusion may be inconsistent."
                )
                checks_performed.append(
                    "CHECK_2: NOT_SATISFIED inconsistent with supporting evidence — FAILED"
                )
            else:
                checks_performed.append("CHECK_2: NOT_SATISFIED has justification — PASSED")
        else:
            checks_performed.append("CHECK_2: Result is not NOT_SATISFIED — skipped")

        # ── Check 3: Hallucination check on cited evidence ────────────────────
        fabricated_citations: List[str] = []
        for cited in qwen_result.evidence_cited:
            ratio = _word_presence_ratio(cited, clinical_text)
            if ratio < _HALLUCINATION_WORD_MATCH_THRESHOLD:
                fabricated_citations.append(cited)

        if fabricated_citations:
            rejection_reasons.append(
                f"Qwen cited {len(fabricated_citations)} evidence item(s) that cannot "
                f"be verified in the request: {fabricated_citations[:2]}. "
                f"Potential hallucination detected."
            )
            checks_performed.append(
                f"CHECK_3: Hallucination check — FAILED ({len(fabricated_citations)} suspicious citations)"
            )
        else:
            checks_performed.append("CHECK_3: Hallucination check — PASSED")

        # ── Check 4: Absence-of-evidence vs evidence-of-absence ───────────────
        # If Qwen says NOT_SATISFIED based purely on missing clinical documentation or unperformed tests,
        # it must be converted to UNKNOWN (prompting for records) rather than an outright DENY.
        # However, an explicit clinical contradiction (e.g. "has not attempted conservative therapy",
        # "without documented trigger points", "acupuncture-related") remains NOT_SATISFIED.
        if qwen_result.result == SemanticResult.NOT_SATISFIED:
            no_clinical_notes = not (clinical_evidence.raw_clinical_text or "").strip()

            has_explicit_contradiction = False
            for c in clinical_evidence.contradicting_evidence:
                c_lower = c.lower()
                if any(k in c_lower for k in ("has not attempted", "has not tried", "refuses", "without documented trigger points", "acupuncture-related", "trigger point exclusions")):
                    has_explicit_contradiction = True
                    break

            if no_clinical_notes or not has_explicit_contradiction:
                rejection_reasons.append(
                    "Qwen returned NOT_SATISFIED when required clinical documentation or trials are missing. "
                    "In prior authorization, missing documentation resolves to UNKNOWN "
                    "(prompting for additional information) rather than an outright denial."
                )
                checks_performed.append(
                    "CHECK_4: Absence vs negative evidence — FAILED (converted to UNKNOWN)"
                )
            else:
                checks_performed.append("CHECK_4: Absence vs negative evidence — PASSED")
        else:
            checks_performed.append("CHECK_4: Not applicable for this result — skipped")

        # ── Check 5: Consistency with pre-agent evidence ──────────────────────
        if (
            qwen_result.result == SemanticResult.SATISFIED
            and not clinical_evidence.supporting_evidence
            and clinical_evidence.missing_evidence
            and not clinical_evidence.contradicting_evidence
        ):
            rejection_reasons.append(
                "Qwen returned SATISFIED despite missing required evidence and "
                "no supporting evidence being found by the Clinical Evidence Agent."
            )
            checks_performed.append(
                "CHECK_5: Consistency with clinical evidence — FAILED"
            )
        else:
            checks_performed.append("CHECK_5: Consistency with clinical evidence — PASSED")

        # ── Determine verdict ─────────────────────────────────────────────────
        latency = round((time.monotonic() - start) * 1000)

        if rejection_reasons:
            validated_result = SemanticResult.UNKNOWN
            verdict = CriticVerdict.REJECTED
            rejection_summary = " | ".join(rejection_reasons)
            summary = (
                f"Critic REJECTED Qwen's result ({qwen_result.result.value}). "
                f"Final result: UNKNOWN. Reasons: {rejection_reasons[0]}"
            )
            logger.warning(
                "CriticAgent | verdict=REJECTED | original=%s | reasons=%d | latency_ms=%d | %s",
                qwen_result.result.value, len(rejection_reasons), latency, rejection_summary,
            )
        else:
            validated_result = qwen_result.result
            verdict = CriticVerdict.VALIDATED
            rejection_summary = None
            summary = (
                f"Critic VALIDATED Qwen's result: {qwen_result.result.value}. "
                f"All {len(checks_performed)} checks passed."
            )
            logger.info(
                "CriticAgent | verdict=VALIDATED | result=%s | latency_ms=%d",
                qwen_result.result.value, latency,
            )

        critic_result = CriticResult(
            verdict=verdict,
            checks_performed=checks_performed,
            rejection_reason=rejection_summary,
            validated_result=validated_result,
        )

        trace = AgentTraceEntry(
            agent="CRITIC_AGENT",
            status=AgentStatus.COMPLETED,
            output_summary=summary,
            result=verdict.value,
        )

        return critic_result, trace
