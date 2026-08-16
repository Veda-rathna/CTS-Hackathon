"""LLM Client for semantic evaluation via LM Studio / Qwen.

Provides three call patterns:
1. evaluate_criterion()               — legacy flat prompt (backward compat)
2. raw_chat(system, user)             — low-level call used by individual agents
3. evaluate_semantic_criterion_structured() — structured Qwen call via AgentOrchestrator

Runtime model: qwen/qwen3-4b-2507 via LM Studio at http://127.0.0.1:1234/v1
"""
from __future__ import annotations

import json
import logging
import httpx
from pydantic import BaseModel, Field

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    """Structured response from the LLM (legacy evaluate_criterion path)."""
    status: str = Field(..., description="SATISFIED, NOT_SATISFIED, or UNKNOWN")
    patient_evidence: list[str] = Field(
        default_factory=list,
        description="Evidence found in patient clinical notes",
    )


def _strip_fences(content: str) -> str:
    """Strip markdown code fences from LLM output."""
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()


def _make_timeout() -> httpx.Timeout:
    return httpx.Timeout(connect=5.0, read=30.0, write=5.0, pool=5.0)


class LLMClient:
    """Client for LM Studio / AWS Bedrock (OpenAI-compatible).

    All methods fail safely — LLM failures always produce UNKNOWN results,
    never APPROVE/PEND/REQUEST_MORE_INFORMATION.
    """

    def __init__(self):
        self._settings = get_settings()
        self.provider = getattr(self._settings, "llm_provider", "bedrock").lower()
        self.api_key = getattr(self._settings, "llm_api_key", None)
        self.model = self._settings.llm_model
        self.temperature = self._settings.llm_temperature
        self.enabled = self._settings.llm_enabled

        base = self._settings.llm_base_url
        if self.provider == "bedrock" or (self.api_key and "127.0.0.1" in base):
            self.endpoint_url = f"https://bedrock-runtime.us-east-1.amazonaws.com/model/{self.model}/invoke"
        elif base.endswith("/chat/completions"):
            self.endpoint_url = base
        else:
            self.endpoint_url = f"{base.rstrip('/')}/chat/completions"

    # ── Low-level primitive ───────────────────────────────────────────────────

    def raw_chat(self, system: str, user: str) -> str:
        """Low-level LLM call used by individual agents.

        Sends a system + user message pair and returns the raw response
        content string with markdown fences stripped.
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        with httpx.Client(timeout=_make_timeout()) as client:
            response = client.post(
                self.endpoint_url,
                headers=headers,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": self.temperature,
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return _strip_fences(content)

    # ── Agent Orchestrator — structured Qwen call ─────────────────────────────

    def evaluate_semantic_criterion_structured(
        self,
        qwen_prompt_context: str,
    ) -> dict:
        """Send the structured Qwen evaluation prompt and return parsed dict.

        Used by AgentOrchestrator for the main semantic reasoning step.
        Input is the EvaluationAgent-prepared context (patient text arrives
        only as pre-extracted evidence bullets, never as raw instructions).

        Returns:
            dict with keys: result, evidence_cited, explanation
            On any failure: returns a safe UNKNOWN dict.
        """
        _SYSTEM = (
            "You are a deterministic healthcare policy evaluator. "
            "Evaluate whether the patient evidence satisfies the policy criterion. "
            "Output only valid JSON. "
            "NEVER return APPROVE, DENY, PEND, or REQUEST_MORE_INFORMATION — "
            "only SATISFIED, NOT_SATISFIED, or UNKNOWN."
        )
        _SAFE: dict = {
            "result": "UNKNOWN",
            "evidence_cited": [],
            "explanation": "Semantic evaluation unavailable.",
        }

        if not self.enabled:
            _SAFE["explanation"] = "LLM evaluation disabled."
            return _SAFE

        try:
            raw = self.raw_chat(system=_SYSTEM, user=qwen_prompt_context)
            parsed = json.loads(raw)
            result = parsed.get("result", "UNKNOWN").upper()
            # Enforce allowed values — forbidden authorization decisions → UNKNOWN
            if result not in ("SATISFIED", "NOT_SATISFIED", "UNKNOWN"):
                logger.warning(
                    "Qwen returned forbidden result '%s' — converting to UNKNOWN", result
                )
                result = "UNKNOWN"
            return {
                "result": result,
                "evidence_cited": [
                    str(e) for e in parsed.get("evidence_cited", []) if e
                ],
                "explanation": str(parsed.get("explanation", "")).strip(),
            }
        except httpx.ConnectError as exc:
            logger.warning("Qwen unreachable (ConnectError): %s", exc)
            _SAFE["explanation"] = "Qwen service unreachable. Deterministic rules apply."
            return _SAFE
        except httpx.TimeoutException as exc:
            logger.warning("Qwen timed out: %s", exc)
            _SAFE["explanation"] = "Qwen evaluation timed out. Deterministic rules apply."
            return _SAFE
        except json.JSONDecodeError as exc:
            logger.warning("Qwen returned malformed JSON: %s", exc)
            _SAFE["explanation"] = "Qwen returned malformed JSON response."
            return _SAFE
        except Exception as exc:
            logger.error("Qwen structured evaluation failed: %s", exc)
            _SAFE["explanation"] = f"Qwen API error: {str(exc)}"
            return _SAFE

    # ── Legacy method (backward compatibility) ────────────────────────────────

    def evaluate_criterion(self, criterion_text: str, clinical_notes: str | None) -> LLMResponse:
        """Legacy call: evaluate criterion directly with clinical notes.

        Used by the legacy SemanticEvaluator path (non-agentic).
        Kept for backward compatibility. The agentic path uses
        evaluate_semantic_criterion_structured() instead.
        """
        if not self.enabled:
            return LLMResponse(status="UNKNOWN", patient_evidence=["LLM evaluation disabled."])

        if not clinical_notes:
            return LLMResponse(
                status="UNKNOWN",
                patient_evidence=["No clinical notes provided for evaluation."],
            )

        prompt = (
            f"You are a medical policy evaluator. Evaluate if the patient evidence "
            f"satisfies the semantic policy criterion.\n\n"
            f"Policy Criterion:\n{criterion_text}\n\n"
            f"Patient Clinical Notes:\n{clinical_notes}\n\n"
            f"Respond with a JSON object exactly matching this schema:\n"
            f"{{\n"
            f'  "status": "SATISFIED" | "NOT_SATISFIED" | "UNKNOWN",\n'
            f'  "patient_evidence": ["list of strings quoting the patient evidence"]\n'
            f"}}\n"
            f"If the evidence is insufficient, use UNKNOWN. Do not guess or invent facts."
        )

        try:
            raw = self.raw_chat(
                system="You are a deterministic healthcare policy evaluator. Output only valid JSON.",
                user=prompt,
            )
            parsed = json.loads(raw)
            status = parsed.get("status", "UNKNOWN").upper()
            if status not in ("SATISFIED", "NOT_SATISFIED", "UNKNOWN"):
                status = "UNKNOWN"
            return LLMResponse(
                status=status,
                patient_evidence=parsed.get("patient_evidence", []),
            )

        except httpx.ConnectError as exc:
            logger.warning("LLM unreachable (ConnectError) — falling back to UNKNOWN. Error: %s", exc)
            return LLMResponse(
                status="UNKNOWN",
                patient_evidence=["LLM service unreachable. Deterministic rules will apply."],
            )
        except httpx.TimeoutException as exc:
            logger.warning("LLM timed out — falling back to UNKNOWN. Error: %s", exc)
            return LLMResponse(
                status="UNKNOWN",
                patient_evidence=["LLM evaluation timed out. Deterministic rules will apply."],
            )
        except Exception as exc:
            logger.error("LLM evaluation failed: %s", exc)
            return LLMResponse(
                status="UNKNOWN",
                patient_evidence=[f"LLM API error: {str(exc)}"],
            )
