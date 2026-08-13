"""Pydantic schemas for the multi-evaluator pipeline.

This module defines the three-layer evaluation hierarchy:

    Layer 1: CriterionEvaluation  — per-criterion result (SATISFIED / NOT_SATISFIED / UNKNOWN)
    Layer 2: PolicyEvaluationResult — per-policy aggregation (COVERED / EXCLUDED / NOT_ADDRESSED / UNKNOWN)
    Layer 3: TriageDecision (existing enum, not redefined here)

Every criterion carries full provenance via CriterionSource so the audit
trail can trace exactly where each requirement originated.
"""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ── Retrieval status ──────────────────────────────────────────────────────────


class RetrievalStatus(str, Enum):
    """Internal retrieval outcome — distinguishes infrastructure failure from no-match."""

    MATCHED = "RETRIEVAL_MATCHED"
    NO_MATCH = "RETRIEVAL_NO_MATCH"            # search succeeded, nothing above threshold
    UNAVAILABLE = "RETRIEVAL_UNAVAILABLE"       # embedding/vector service down


class RetrievedSection(BaseModel):
    """A single section retrieved by the RAG pipeline."""

    policy_type: str
    policy_id: str
    policy_version: str | None = None
    section: str
    chunk_id: str | None = None
    content: str
    score: float = 0.0
    metadata: dict[str, str | None] = {}


class RetrievalResult(BaseModel):
    """Result of a RAG retrieval operation."""

    status: RetrievalStatus
    sections: list[RetrievedSection] = []
    error: str | None = None                    # populated only for UNAVAILABLE


# ── Criterion provenance ─────────────────────────────────────────────────────


class CriterionSource(BaseModel):
    """Traces a criterion back to its origin in the policy text.

    This supports the auditability requirement: every extracted criterion
    records exactly where it came from and how it was discovered.
    """

    policy_type: str                            # NCD, LCD, ARTICLE
    policy_id: str                              # e.g., "L39054"
    policy_version: str | None = None
    section: str                                # e.g., "indications_limitations", "doc_reqs"
    chunk_id: str | None = None                 # RAG chunk ID if retrieved via vector search
    extraction_method: Literal[
        "STRUCTURED_FIELD",                     # directly from DB column
        "CODE_RELATIONSHIP",                    # from code tables (LCDIcd10Covered, etc.)
        "DETERMINISTIC_PARSER",                 # regex/rule-based extraction from text
        "LLM",                                  # LLM extracted from unstructured text
    ]


# ── Criterion evaluation (Layer 1) ───────────────────────────────────────────


class CriterionEvaluation(BaseModel):
    """Result of evaluating a single atomic policy criterion.

    Layer 1 in the evaluation hierarchy.  Status values:
    - SATISFIED: available evidence meets the policy requirement.
    - NOT_SATISFIED: available evidence contradicts the requirement.
    - UNKNOWN: evidence is missing, ambiguous, or insufficient.

    UNKNOWN is NOT the same as NOT_SATISFIED.
    """

    criterion_id: str
    criterion: str                              # human-readable criterion text
    criterion_type: Literal[
        "STRUCTURED",                           # ICD-10/CPT exact match, code list
        "RULE_BASED",                           # duration, age, frequency — deterministic calc
        "SEMANTIC",                             # clinical narrative interpretation
        "DOCUMENT",                             # documentation existence / content
    ]
    mandatory: bool = True                      # if True, UNKNOWN → PEND
    source: CriterionSource                     # provenance

    evaluator: Literal["SQL", "RULE_ENGINE", "LLM", "DOCUMENT_RULE"]
    status: Literal["SATISFIED", "NOT_SATISFIED", "UNKNOWN"]
    authoritative: bool = True                  # False if overridden by higher-precedence evaluator
    overridden_by: str | None = None            # evaluator that overrode this result

    patient_evidence: list[str] = []
    policy_evidence: list[str] = []
    explanation: str = ""
    confidence: float | None = None             # metadata only — never used for decisions


# ── Evidence matrix ──────────────────────────────────────────────────────────


class EvidenceMatrix(BaseModel):
    """Aggregated criterion evaluations for a single policy evaluation pass."""

    criteria: list[CriterionEvaluation] = []

    @property
    def all_satisfied(self) -> bool:
        """True when every mandatory criterion is SATISFIED."""
        return all(
            c.status == "SATISFIED"
            for c in self.criteria
            if c.mandatory
        )

    @property
    def has_exclusion(self) -> bool:
        """True when any criterion explicitly indicates exclusion/non-coverage."""
        return any(
            c.status == "NOT_SATISFIED" and c.authoritative
            for c in self.criteria
            if c.mandatory
        )

    @property
    def has_unknown(self) -> bool:
        """True when any mandatory criterion is UNKNOWN."""
        return any(
            c.status == "UNKNOWN"
            for c in self.criteria
            if c.mandatory
        )

    @property
    def satisfied_criteria(self) -> list[CriterionEvaluation]:
        return [c for c in self.criteria if c.status == "SATISFIED"]

    @property
    def failed_criteria(self) -> list[CriterionEvaluation]:
        return [c for c in self.criteria if c.status == "NOT_SATISFIED"]

    @property
    def unknown_criteria(self) -> list[CriterionEvaluation]:
        return [c for c in self.criteria if c.status == "UNKNOWN"]


# ── Policy evaluation result (Layer 2) ───────────────────────────────────────


class PolicyEvaluationResult(BaseModel):
    """Aggregated result of evaluating all criteria for one policy.

    Layer 2 in the evaluation hierarchy.

    overall_status values differ by policy type:
    - NCD: COVERED / EXCLUDED / NOT_ADDRESSED
    - LCD: COVERED / EXCLUDED / UNKNOWN
    - ARTICLE: MATCHED / NOT_MATCHED / UNKNOWN
    """

    policy_id: str
    policy_type: Literal["NCD", "LCD", "ARTICLE"]
    policy_version: str | None = None
    title: str | None = None

    criteria: list[CriterionEvaluation] = []
    evidence_matrix: EvidenceMatrix | None = None

    overall_status: str
    retrieval_status: RetrievalStatus | None = None
    explanation: str = ""

    # Article-specific flags
    has_missing_documentation: bool = False
    has_coding_conflict: bool = False


# ── Policy section (for PolicyContentService) ────────────────────────────────


class PolicySection(BaseModel):
    """A normalized section of policy content, ready for chunking/embedding."""

    policy_type: str                            # NCD, LCD, ARTICLE
    policy_id: str
    policy_version: str | None = None
    section_type: str                           # e.g., "indications", "doc_reqs", "coverage"
    content: str
    effective_date: date | None = None
    end_date: date | None = None
    jurisdiction_id: str | None = None
    contractor_id: str | None = None
