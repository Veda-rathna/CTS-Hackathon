"""Pydantic schemas for the Triage API (request and response)."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ── Decision enum ─────────────────────────────────────────────────────────────


class TriageDecision(str, Enum):
    """Deterministic triage outcome values.

    These values describe the final decision result (APPROVE, PEND, NEED_MORE_INFORMATION).
    """

    APPROVE = "APPROVE"
    PEND = "PEND"
    NEED_MORE_INFORMATION = "NEED_MORE_INFORMATION"
    DENY = "DENY"  # Retained for internal/backward compatibility; mapped to PEND in nurse-facing flow


# ── Request ───────────────────────────────────────────────────────────────────


class TriageRequest(BaseModel):
    """Input for the triage engine.

    PRIVACY NOTE: This model intentionally omits patient name, SSN,
    date of birth, and other PHI. Only the minimum clinical codes
    required for policy lookup are accepted.
    """

    procedure_code: str = Field(
        ...,
        min_length=1,
        description="HCPCS or CPT procedure code (e.g. '64483').",
    )
    diagnosis_codes: list[str] = Field(
        ...,
        min_length=1,
        description="One or more ICD-10-CM diagnosis codes.",
    )
    state: str | None = Field(
        default=None,
        max_length=2,
        description="Two-letter US state abbreviation (e.g. 'TX'). Normalized to uppercase.",
    )
    patient_age: int | None = Field(
        default=None,
        ge=0,
        description="Patient age in years (≥ 0). Optional context for policy checks.",
    )
    patient_id: str | None = Field(
        default=None,
        description="Optional patient identifier used to fetch Synthea clinical history.",
    )
    clinical_notes: str | None = Field(
        default=None,
        description="Patient clinical notes for semantic evaluation.",
    )
    service_date: str | None = Field(
        default=None,
        description="Date of service. Used for policy effective date validation.",
    )

    @field_validator("procedure_code", mode="before")
    @classmethod
    def normalize_procedure_code(cls, v: str) -> str:
        return v.strip().upper() if isinstance(v, str) else v

    @field_validator("diagnosis_codes", mode="before")
    @classmethod
    def normalize_diagnosis_codes(cls, v: list[str]) -> list[str]:
        if not isinstance(v, list):
            return v
        return [c.strip().upper() for c in v if isinstance(c, str) and c.strip()]

    @field_validator("state", mode="before")
    @classmethod
    def normalize_state(cls, v: str | None) -> str | None:
        return v.strip().upper() if isinstance(v, str) and v.strip() else None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "procedure_code": "64483",
                    "diagnosis_codes": ["M54.16"],
                    "state": "TX",
                    "patient_age": 65,
                }
            ]
        }
    }


# ── Response sub-models ───────────────────────────────────────────────────────


class MatchedPolicy(BaseModel):
    """A policy that matched the submitted request."""

    policy_type: str
    policy_id: str
    title: str | None = None
    article_id: str | None = None


class MatchedCodes(BaseModel):
    """Summary of procedure and diagnosis codes that matched a policy."""

    procedure: str
    diagnosis: list[str] = []


class DiagnosisEvaluation(BaseModel):
    """Per-diagnosis-code evaluation result."""

    code: str
    status: str
    """COVERED | NOT_COVERED | NOT_FOUND"""


class Evidence(BaseModel):
    """A single piece of evidence that explains the triage decision.

    Every evidence item traces back to a specific data entity so the
    user/demo can understand exactly why the decision was reached.
    """

    type: str
    """Category: HCPCS | ICD10 | JURISDICTION | POLICY_DATE | ARTICLE"""

    identifier: str | None = None
    """Source entity ID (e.g. article ID, LCD ID)."""

    code: str | None = None
    """The code being evaluated (procedure or diagnosis)."""

    state: str | None = None
    """The state value when type is JURISDICTION."""

    result: str = ""
    """MATCHED | COVERED | NOT_COVERED | NOT_FOUND | EXPIRED | ACTIVE"""

    explanation: str = ""
    """Human-readable explanation of why this evidence was generated."""


class RagEvidence(BaseModel):
    """Detailed evidence from RAG chunk retrieval."""
    policy_id: str
    policy_type: str
    policy_title: str | None = None
    section: str | None = None
    chunk_id: str
    text: str
    similarity_score: float | None = None
    source: str | None = None


# ── Top-level response ────────────────────────────────────────────────────────
from app.schemas.evaluation import EvaluatedCriterion


class TriageResponse(BaseModel):
    """Full triage result.

    IMPORTANT: This response reflects policy-matching results only.
    It is NOT a clinical decision and does NOT constitute medical advice
    or a guarantee of insurance coverage or reimbursement.
    """

    decision: TriageDecision
    evidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Deterministic evidence-completeness score (0.0–1.0). "
            "This is NOT a machine-learning probability."
        ),
    )
    requires_prior_authorization: bool | None = Field(
        default=None,
        description=(
            "True if the matched policy explicitly requires prior authorization. "
            "Null when the available policy data is insufficient to determine this."
        ),
    )
    reason: str
    reason_codes: list[str] = []
    policies: list[MatchedPolicy] = []
    policy: dict | None = None
    policy_requirements: list[EvaluatedCriterion] = []
    summary: dict[str, int] = {}
    decision_explanation: str = ""
    policy_path: dict | None = None
    matched_codes: MatchedCodes | None = None
    diagnosis_evaluation: list[DiagnosisEvaluation] = []
    evidence: list[Evidence] = []
    rag_evidence: list[RagEvidence] = []
    criteria: list[EvaluatedCriterion] = []
    missing_information: list[str] = []
    warnings: list[str] = []
    evidence_fusion_result: str | None = Field(
        default=None,
        description=(
            "The intermediate policy coverage result produced by EvidenceFusion "
            "before the DecisionEngine maps it to a public decision. "
            "One of: COVERED, EXCLUDED, UNKNOWN, NOT_ADDRESSED."
        ),
    )
    decision_basis: str = Field(
        default="",
        description=(
            "Human-readable narrative explaining how the EvidenceFusion result "
            "led to the final public decision."
        ),
    )

    def model_post_init(self, __context: Any) -> None:
        if not self.policy_requirements and self.criteria:
            self.policy_requirements = self.criteria
        if not self.policy and self.policies:
            p0 = self.policies[0]
            self.policy = {
                "id": p0.policy_id,
                "title": p0.title or f"{p0.policy_type} {p0.policy_id}",
                "type": p0.policy_type,
            }
        if not self.summary and self.criteria:
            sat = sum(1 for c in self.criteria if c.status == "SATISFIED")
            not_sat = sum(1 for c in self.criteria if c.status == "NOT_SATISFIED")
            unk = sum(1 for c in self.criteria if c.status == "UNKNOWN")
            self.summary = {"satisfied": sat, "not_satisfied": not_sat, "unknown": unk}
        if not self.decision_explanation:
            self.decision_explanation = self.reason


    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "decision": "APPROVE",
                    "evidence_score": 0.9,
                    "requires_prior_authorization": None,
                    "reason": "The procedure and diagnosis match an active applicable policy.",
                    "reason_codes": ["PROCEDURE_FOUND", "DIAGNOSIS_COVERED"],
                    "policies": [
                        {
                            "policy_type": "LCD",
                            "policy_id": "L39054",
                            "title": "Epidural Injections for Pain Management",
                            "article_id": "A12345",
                        }
                    ],
                    "matched_codes": {
                        "procedure": "64483",
                        "diagnosis": ["M54.16"],
                    },
                    "diagnosis_evaluation": [
                        {"code": "M54.16", "status": "COVERED"}
                    ],
                    "evidence": [
                        {
                            "type": "HCPCS",
                            "identifier": "A12345",
                            "code": "64483",
                            "state": None,
                            "result": "MATCHED",
                            "explanation": "Procedure code 64483 is listed in the article's HCPCS/CPT code set.",
                        },
                        {
                            "type": "ICD10",
                            "identifier": "A12345",
                            "code": "M54.16",
                            "state": None,
                            "result": "COVERED",
                            "explanation": "Diagnosis code M54.16 is in the article's covered ICD-10 list.",
                        },
                        {
                            "type": "JURISDICTION",
                            "identifier": "J5",
                            "code": None,
                            "state": "TX",
                            "result": "MATCHED",
                            "explanation": "State TX falls within jurisdiction J5 which governs LCD L39054.",
                        },
                    ],
                    "missing_information": [],
                    "warnings": [],
                }
            ]
        }
    }


class CodeEntry(BaseModel):
    """Re-exported for code endpoint convenience (also defined in article.py)."""

    code: str
    description: str | None = None
