"""Policy Agent — Agent 1 of the Agentic Semantic Evaluation pipeline.

Purpose:
    Understand the semantic policy criterion and determine what evidence
    is required to evaluate it.

Input:
    - PolicyCriterion (criterion text, policy ID, policy type, source text)
    - TriageRequest facts (procedure, diagnosis, patient_age, state)

Output:
    RequiredEvidence — structured description of what the policy requires.

Constraints:
    - Does NOT evaluate the patient.
    - Does NOT make coverage decisions.
    - Does NOT access the database independently.
    - Only reasons over the retrieved policy evidence passed to it.
    - Fails safely: any failure returns a minimal RequiredEvidence.

Prompt injection protection:
    Patient-provided text is never passed to this agent.
    Only policy text and structured request facts are used.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Optional

from app.schemas.evaluation import PolicyCriterion
from app.schemas.triage import TriageRequest
from app.services.llm.client import LLMClient
from app.services.agents.schemas import (
    AgentStatus,
    AgentTraceEntry,
    RequiredEvidence,
    RequiredEvidenceItem,
)

logger = logging.getLogger(__name__)

# Policy Agent system prompt — patient text is NOT included here
_POLICY_AGENT_SYSTEM = (
    "You are a healthcare policy analyst. "
    "Your task is to analyze a specific Medicare policy criterion and identify "
    "what categories of clinical evidence would be required to evaluate it. "
    "Output only valid JSON. Do not invent evidence. Do not make coverage decisions."
)


class PolicyAgent:
    """Agent 1: Identifies required evidence from policy criterion text.

    This agent answers: 'What does the policy require us to look for?'
    It does NOT evaluate the patient.
    """

    def __init__(self, llm_client: LLMClient) -> None:
        self._client = llm_client

    def run(
        self,
        criterion: PolicyCriterion,
        request: TriageRequest,
    ) -> tuple[RequiredEvidence, AgentTraceEntry]:
        """Analyze the policy criterion and return required evidence categories.

        Returns:
            Tuple of (RequiredEvidence, AgentTraceEntry)
        """
        start = time.monotonic()
        criterion_id = criterion.criterion_id

        # Build structured context — NO patient clinical notes here
        # Only policy text and structured code facts
        request_facts = (
            f"Procedure: {request.procedure_code}. "
            f"Diagnoses: {', '.join(request.diagnosis_codes)}. "
            f"State: {request.state or 'not specified'}. "
            f"Patient age: {request.patient_age or 'not specified'}."
        )

        source_policy_text = criterion.source_text or criterion.criterion

        prompt = (
            f"Analyze this Medicare policy criterion and identify what clinical "
            f"evidence categories are required to evaluate it.\n\n"
            f"POLICY CRITERION:\n{criterion.criterion}\n\n"
            f"POLICY SOURCE TEXT:\n{source_policy_text}\n\n"
            f"REQUEST FACTS (structured codes only — not clinical notes):\n{request_facts}\n\n"
            f"Respond with a JSON object matching this schema exactly:\n"
            f"{{\n"
            f'  "requirement": "brief plain-english summary of what the policy requires",\n'
            f'  "required_evidence": [\n'
            f'    {{"category": "short_label", "description": "what to look for"}}\n'
            f'  ]\n'
            f"}}\n\n"
            f"Rules:\n"
            f"- Do not evaluate the patient.\n"
            f"- Do not make coverage decisions.\n"
            f"- List only evidence categories the policy explicitly requires.\n"
            f"- If uncertain, return an empty required_evidence list."
        )

        try:
            if not self._client.enabled:
                return self._fallback(criterion_id, criterion.criterion, "LLM disabled", start)

            raw = self._client.raw_chat(
                system=_POLICY_AGENT_SYSTEM,
                user=prompt,
            )
            parsed = json.loads(raw)

            requirement = parsed.get("requirement", criterion.criterion)
            items_raw = parsed.get("required_evidence", [])

            required_items = []
            for item in items_raw:
                if isinstance(item, dict) and "category" in item and "description" in item:
                    required_items.append(
                        RequiredEvidenceItem(
                            category=str(item["category"]),
                            description=str(item["description"]),
                        )
                    )

            result = RequiredEvidence(
                criterion_id=criterion_id,
                requirement=requirement,
                required_evidence=required_items,
            )

            latency = round((time.monotonic() - start) * 1000)
            summary = (
                f"Identified {len(required_items)} required evidence "
                f"categories in {latency}ms."
            )
            logger.info(
                "PolicyAgent | criterion=%s | required_evidence=%d | latency_ms=%d",
                criterion_id, len(required_items), latency,
            )

            trace = AgentTraceEntry(
                agent="POLICY_AGENT",
                status=AgentStatus.COMPLETED,
                output_summary=summary,
            )
            return result, trace

        except Exception as exc:
            logger.warning(
                "PolicyAgent failed for criterion=%s: %s",
                criterion_id, exc,
            )
            return self._fallback(criterion_id, criterion.criterion, str(exc), start)

    def _fallback(
        self,
        criterion_id: str,
        criterion_text: str,
        reason: str,
        start: float,
    ) -> tuple[RequiredEvidence, AgentTraceEntry]:
        """Safe fallback: return minimal RequiredEvidence so pipeline continues."""
        latency = round((time.monotonic() - start) * 1000)
        result = RequiredEvidence(
            criterion_id=criterion_id,
            requirement=criterion_text,
            required_evidence=[],
        )
        trace = AgentTraceEntry(
            agent="POLICY_AGENT",
            status=AgentStatus.FAILED,
            output_summary=f"Policy Agent failed ({reason}). Using criterion text as requirement.",
        )
        return result, trace
