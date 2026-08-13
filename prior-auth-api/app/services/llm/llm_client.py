"""LLM Client integration.

Abstracts the underlying LLM provider (Anthropic or OpenAI-compatible).
Provides structured output for evaluation and extraction tasks.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.core.config import Settings
from app.exceptions.handlers import LLMServiceError
from app.schemas.evaluation import CriterionEvaluation
from app.schemas.triage import TriageRequest

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for LLM interactions.

    Supports Anthropic and OpenAI-compatible endpoints (e.g., local Qwen server).
    Gracefully handles failures by raising LLMServiceError.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._provider = settings.llm_provider.lower()
        self._model = settings.llm_model
        self._api_key = settings.llm_api_key
        self._base_url = getattr(settings, "llm_base_url", None)
        
        # Lazy initialization
        self._client = None

    def _init_client(self) -> None:
        if self._client is not None:
            return
            
        try:
            if self._provider == "anthropic":
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self._api_key)
            elif self._provider == "openai":
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self._api_key, 
                    base_url=self._base_url
                )
            else:
                raise ValueError(f"Unsupported LLM provider: {self._provider}")
        except Exception as exc:
            raise LLMServiceError(f"Failed to initialize LLM client: {exc}") from exc

    def evaluate_criterion(
        self, 
        criterion: CriterionEvaluation, 
        request: TriageRequest,
        policy_context: str,
    ) -> dict[str, Any]:
        """Evaluate a single criterion using the LLM.
        
        Args:
            criterion: The criterion to evaluate.
            request: The submitted triage request (containing clinical notes).
            policy_context: Relevant policy text context.
            
        Returns:
            Dictionary containing status, patient_evidence, policy_evidence, and explanation.
        """
        self._init_client()
        
        prompt = self._build_semantic_evaluation_prompt(criterion, request, policy_context)
        
        try:
            response_text = self._call_llm(prompt)
            result = self._parse_json_response(response_text)
            
            # Validate output structure
            status = result.get("status", "UNKNOWN").upper()
            if status not in ("SATISFIED", "NOT_SATISFIED", "UNKNOWN"):
                status = "UNKNOWN"
                
            return {
                "status": status,
                "patient_evidence": result.get("patient_evidence", []),
                "policy_evidence": result.get("policy_evidence", []),
                "explanation": result.get("explanation", "LLM evaluation generated."),
            }
        except Exception as exc:
            logger.error(f"LLM evaluation failed for criterion {criterion.criterion_id}: {exc}")
            # Do not crash the application, return UNKNOWN gracefully
            return {
                "status": "UNKNOWN",
                "patient_evidence": [],
                "policy_evidence": [],
                "explanation": f"LLM evaluation failed: {exc}",
            }

    def _call_llm(self, prompt: str) -> str:
        """Call the underlying LLM provider."""
        system_prompt = (
            "You are an expert medical coder and policy evaluator. "
            "Evaluate the policy criterion strictly against the provided clinical notes. "
            "Do not make assumptions. Output your answer strictly as a JSON object."
        )
        
        if self._provider == "anthropic":
            response = self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            return response.content[0].text
            
        elif self._provider == "openai":
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"} if "gpt" in self._model else None
            )
            return response.choices[0].message.content

    def _parse_json_response(self, text: str) -> dict:
        """Robustly extract JSON from the LLM response."""
        text = text.strip()
        # Find JSON block if wrapped in markdown
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        else:
            # Try to find { ... } if no markdown block
            brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
            if brace_match:
                text = brace_match.group(1)
                
        return json.loads(text)

    def _build_semantic_evaluation_prompt(
        self, 
        criterion: CriterionEvaluation, 
        request: TriageRequest,
        policy_context: str,
    ) -> str:
        """Build the prompt for semantic criterion evaluation."""
        clinical_notes = request.clinical_notes or "No clinical notes provided."
        
        prompt = f"""
Evaluate whether the following policy criterion is satisfied based on the patient's clinical notes.

CRITERION:
{criterion.criterion}

POLICY CONTEXT:
{policy_context}

PATIENT CLINICAL NOTES:
{clinical_notes}

INSTRUCTIONS:
1. Compare the patient's clinical notes against the criterion.
2. If the notes clearly satisfy the criterion, status is "SATISFIED".
3. If the notes clearly contradict the criterion, status is "NOT_SATISFIED".
4. If there is insufficient information in the notes to make a determination, status is "UNKNOWN".
5. Provide specific quotes or evidence from the notes and the policy to support your decision.

Respond ONLY with a valid JSON object matching this schema:
{{
  "status": "SATISFIED" | "NOT_SATISFIED" | "UNKNOWN",
  "patient_evidence": ["Quote from clinical notes"],
  "policy_evidence": ["Quote from policy context"],
  "explanation": "Brief reasoning for the decision"
}}
"""
        return prompt.strip()
