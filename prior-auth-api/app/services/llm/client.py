"""LLM Client for semantic evaluation via LM Studio / Qwen."""
from __future__ import annotations

import json
import logging
import httpx
from typing import Any
from pydantic import BaseModel, Field

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    """Structured response from the LLM."""
    status: str = Field(..., description="SATISFIED, NOT_SATISFIED, or UNKNOWN")
    patient_evidence: list[str] = Field(default_factory=list, description="Evidence found in patient clinical notes")


class LLMClient:
    """Client for LM Studio (OpenAI compatible)."""
    
    def __init__(self):
        self._settings = get_settings()
        self.base_url = self._settings.llm_base_url
        self.model = self._settings.llm_model
        self.temperature = self._settings.llm_temperature
        self.enabled = self._settings.llm_enabled
        
    def evaluate_criterion(self, criterion_text: str, clinical_notes: str | None) -> LLMResponse:
        """Call LLM to evaluate if patient evidence satisfies the semantic criterion."""
        
        # Fallback to UNKNOWN if LLM is disabled or no notes are provided
        if not self.enabled:
            return LLMResponse(status="UNKNOWN", patient_evidence=["LLM evaluation disabled."])
            
        if not clinical_notes:
            return LLMResponse(status="UNKNOWN", patient_evidence=["No clinical notes provided for evaluation."])

        prompt = (
            f"You are a medical policy evaluator. Evaluate if the patient evidence satisfies the semantic policy criterion.\n\n"
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
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are a deterministic healthcare policy evaluator. Output only valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": self.temperature
                    }
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                parsed = json.loads(content)
                status = parsed.get("status", "UNKNOWN").upper()
                if status not in ("SATISFIED", "NOT_SATISFIED", "UNKNOWN"):
                    status = "UNKNOWN"
                    
                return LLMResponse(
                    status=status,
                    patient_evidence=parsed.get("patient_evidence", [])
                )
                
        except Exception as e:
            logger.error("LLM evaluation failed: %s", e)
            return LLMResponse(
                status="UNKNOWN", 
                patient_evidence=[f"LLM API error: {str(e)}"]
            )
