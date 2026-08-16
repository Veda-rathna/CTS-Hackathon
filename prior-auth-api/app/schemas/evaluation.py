"""Schemas for policy criteria evaluation."""
from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field



class CriterionType(str, Enum):
    """Categorization of a policy criterion."""
    STRUCTURED = "STRUCTURED"
    SEMANTIC = "SEMANTIC"


class EvaluatorType(str, Enum):
    """The system that evaluates the criterion."""
    SQL = "SQL"
    LLM = "LLM"
    AGENTIC_QWEN = "AGENTIC_QWEN"  # Four-agent orchestrated semantic evaluation


class EvaluationStatus(str, Enum):
    """Result of evaluating a single criterion."""
    SATISFIED = "SATISFIED"
    NOT_SATISFIED = "NOT_SATISFIED"
    UNKNOWN = "UNKNOWN"


class PolicyCriterion(BaseModel):
    """A single evaluation unit extracted from policy text."""
    criterion_id: str
    criterion: str
    type: CriterionType
    policy_type: str
    policy_id: str
    source_text: str | None = None
    mandatory: bool = True
    """If False, a NOT_SATISFIED result does not hard-block the coverage decision.
    Used for alternative OR-branch sections (e.g. CED trial path in NCD 110.23)."""


class EvaluatedCriterion(BaseModel):
    """The result of evaluating a single policy criterion."""
    criterion_id: str
    policy_type: str
    policy_id: str
    criterion: str
    requirement: str | None = None
    criterion_type: CriterionType
    evaluator: EvaluatorType
    status: EvaluationStatus
    patient_evidence: list[str] = []
    policy_evidence: list[str] = []
    evidence: list[dict[str, Any]] = []
    explanation: str = ""
    """Human-readable explanation of WHY this criterion received its status.
    Synthesized by the evaluator — clean, provider/nurse-friendly narrative."""
    mandatory: bool = True
    authoritative: bool = True

    def model_post_init(self, __context: Any) -> None:
        if not self.requirement:
            self.requirement = self.criterion
        if not self.evidence and self.patient_evidence:
            self.evidence = [
                {"source": "Patient Clinical Record", "date": "Service Date / Active Record", "text": str(pe)}
                for pe in self.patient_evidence
            ]


class EvidenceMatrix(BaseModel):
    """Consolidated evidence from all evaluation paths."""
    criteria: list[EvaluatedCriterion] = []

