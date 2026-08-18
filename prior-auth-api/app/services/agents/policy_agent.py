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
    "You are a healthcare policy analyst for Medicare prior authorization review. "
    "Your task is to analyze a specific Medicare policy criterion and identify "
    "what categories of clinical evidence would be required to evaluate it. "
    "Output only valid JSON. Do not invent evidence. Do not make coverage decisions.\n"
    "CRITICAL RULES:\n"
    "1. List ONLY evidence categories that are EXPLICITLY stated in the policy criterion text. "
    "Do NOT invent, infer, or extrapolate sub-requirements.\n"
    "2. CONSOLIDATE COMPOSITE CRITERIA: When a criterion describes a clinical diagnosis supported by exam/imaging "
    "(e.g., 'Diagnosis of X supported by physical exam and concordant imaging'), create ONE unified evidence category for "
    "'diagnostic_confirmation' (diagnosis of X supported by clinical presentation or imaging).\n"
    "3. When the policy criterion contains an OR list (e.g., 'condition A or condition B or condition C'), "
    "create ONE combined evidence item covering all the OR alternatives together — "
    "do NOT create a separate item for each alternative.\n"
    "4. Generate at most 2 required_evidence items per criterion. If you have more, consolidate them.\n"
    "5. If the policy criterion is simple and self-contained (e.g., single condition), "
    "return 1 item."
)


class PolicyAgent:
    """Agent 1: Identifies required evidence from policy criterion text.

    This agent answers: 'What does the policy require us to look for?'
    It does NOT evaluate the patient.
    """

    def __init__(self, llm_client: LLMClient) -> None:
        self._client = llm_client
        self._policy_cache: dict[str, RequiredEvidence] = {}

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

        # Cache check for static CMS policy criteria
        cache = getattr(self, "_policy_cache", None)
        if cache is None:
            self._policy_cache = {}
            cache = self._policy_cache

        cache_key = f"{criterion_id}::{criterion.criterion}"
        if cache_key in cache:
            cached_result = cache[cache_key]
            logger.info("PolicyAgent | cache hit for criterion=%s", criterion_id)
            trace = AgentTraceEntry(
                agent="POLICY_AGENT",
                status=AgentStatus.COMPLETED,
                output_summary=f"Cached {len(cached_result.required_evidence)} required evidence categories (0ms).",
                result=cached_result.requirement,
                duration_ms=0.0,
            )
            return cached_result, trace

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
            f"STRICT RULES — READ CAREFULLY:\n"
            f"1. Do NOT evaluate the patient.\n"
            f"2. Do NOT make coverage decisions.\n"
            f"3. ONLY list evidence categories that the policy criterion EXPLICITLY states. "
            f"Do NOT invent sub-requirements, implicit assumptions, or administrative details "
            f"(e.g., do not add 'documented treatment plan' or 'disease severity logs' unless the criterion text explicitly names them).\n"
            f"4. If the criterion is a single condition or state (e.g. 'Patient has symptomatic osteoarthritis of the knee' or 'Diagnosis of radiculopathy'), "
            f"return EXACTLY 1 required_evidence item describing that condition. Do NOT split it into multiple sub-items.\n"
            f"5. OR-LISTS: If the criterion says 'A or B or C', write ONE evidence item "
            f"that says 'Patient must have ONE of: A, B, or C' — not three separate items.\n"
            f"6. Return at most 2 required_evidence items total. Consolidate if needed.\n"
            f"7. If uncertain about whether something is explicitly required, return an empty "
            f"required_evidence list rather than guessing."
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

            if not required_items:
                c_lower = criterion.criterion.lower()
                if any(k in c_lower for k in ("conservative", "physical therapy", "trial", "failed", "drug", "nsaid")):
                    required_items.append(
                        RequiredEvidenceItem(
                            category="conservative_therapy",
                            description="Documentation of completed conservative therapy, physical therapy, or medication trial.",
                        )
                    )
                if any(k in c_lower for k in ("mri", "imaging", "x-ray", "radiograph", "scan")):
                    required_items.append(
                        RequiredEvidenceItem(
                            category="diagnostic_imaging",
                            description="Diagnostic imaging reports or radiographic confirmation of the condition.",
                        )
                    )
                if any(k in c_lower for k in ("symptom", "pain", "indication", "radiculopathy", "osteoarthritis", "exam", "trigger point", "joint", "disc")):
                    required_items.append(
                        RequiredEvidenceItem(
                            category="clinical_indication",
                            description="Documentation of documented symptoms, clinical indication, and physical examination findings.",
                        )
                    )

            # Hard cap: never more than 3 required evidence items.
            if len(required_items) > 3:
                logger.warning(
                    "PolicyAgent | criterion=%s | LLM returned %d required_evidence items — "
                    "capping to 3 to prevent hallucinated sub-requirements.",
                    criterion_id, len(required_items),
                )
                required_items = required_items[:3]

            result = RequiredEvidence(
                criterion_id=criterion_id,
                requirement=requirement,
                required_evidence=required_items,
            )
            cache[cache_key] = result

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
        """Safe fallback: extract structured RequiredEvidence deterministically from criterion text."""
        latency = round((time.monotonic() - start) * 1000)
        c_lower = criterion_text.lower()
        required_items: list[RequiredEvidenceItem] = []

        if any(k in c_lower for k in ("conservative", "physical therapy", "trial", "failed", "drug", "nsaid", "conventional", "refractory", "contraindicated")):
            required_items.append(
                RequiredEvidenceItem(
                    category="conservative_therapy",
                    description="Documentation of completed conservative therapy, physical therapy, or conventional medication trial failure/contraindication.",
                )
            )
        if any(k in c_lower for k in ("mri", "imaging", "x-ray", "radiograph", "scan")):
            required_items.append(
                RequiredEvidenceItem(
                    category="diagnostic_imaging",
                    description="Diagnostic imaging reports or radiographic confirmation of the condition.",
                )
            )
        if any(k in c_lower for k in ("biopsy", "pemphigus", "blistering", "pathology")):
            required_items.append(
                RequiredEvidenceItem(
                    category="diagnostic_confirmation",
                    description="Biopsy-proven pathology confirmation or confirmed clinical diagnosis of pemphigus vulgaris/blistering disease.",
                )
            )
        if any(k in c_lower for k in ("symptom", "pain", "indication", "radiculopathy", "osteoarthritis", "exam", "trigger point", "joint")):
            required_items.append(
                RequiredEvidenceItem(
                    category="clinical_indication",
                    description="Documentation of documented symptoms, clinical indication, and physical examination findings.",
                )
            )

        if not required_items:
            required_items.append(
                RequiredEvidenceItem(
                    category="clinical_documentation",
                    description=f"Supporting clinical documentation for: {criterion_text[:100]}",
                )
            )

        result = RequiredEvidence(
            criterion_id=criterion_id,
            requirement=criterion_text,
            required_evidence=required_items[:3],
        )
        trace = AgentTraceEntry(
            agent="POLICY_AGENT",
            status=AgentStatus.COMPLETED if reason == "LLM disabled" else AgentStatus.FAILED,
            output_summary=f"Identified {len(result.required_evidence)} required evidence categories (deterministic fallback).",
        )
        return result, trace
