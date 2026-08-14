"""Schemas for policy criteria evaluation."""
from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class CriterionType(str, Enum):
    """Categorization of a policy criterion."""
    STRUCTURED = "STRUCTURED"
    RULE_BASED = "RULE_BASED"
    SEMANTIC = "SEMANTIC"


class EvaluatorType(str, Enum):
    """The system that evaluates the criterion."""
    SQL = "SQL"
    RULES = "RULES"
    LLM = "LLM"


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


class EvaluatedCriterion(BaseModel):
    """The result of evaluating a single policy criterion."""
    criterion_id: str
    policy_type: str
    policy_id: str
    criterion: str
    criterion_type: CriterionType
    evaluator: EvaluatorType
    status: EvaluationStatus
    patient_evidence: list[str] = []
    policy_evidence: list[str] = []
    mandatory: bool = True
    authoritative: bool = True


class EvidenceMatrix(BaseModel):
    """Consolidated evidence from all evaluation paths."""
    criteria: list[EvaluatedCriterion] = []
