"""Pydantic schemas for the Agentic Semantic Evaluation pipeline.

These models define the structured I/O contracts for each agent.
No agent returns APPROVE / PEND / REQUEST_MORE_INFORMATION — those
decisions belong exclusively to DecisionEngine.

Allowed semantic results: SATISFIED | NOT_SATISFIED | UNKNOWN
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


# ── Semantic result enum (agents only — never authorization decisions) ─────────

class SemanticResult(str, Enum):
    """Semantic evaluation result.

    Agents may only produce these three values.
    APPROVE / PEND / REQUEST_MORE_INFORMATION are strictly forbidden
    from any agent output.
    """
    SATISFIED = "SATISFIED"
    NOT_SATISFIED = "NOT_SATISFIED"
    UNKNOWN = "UNKNOWN"


class CriticVerdict(str, Enum):
    """Critic agent verdict."""
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"


class AgentStatus(str, Enum):
    """Execution status of a single agent step."""
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


# ── Agent 1 — Policy Agent output ─────────────────────────────────────────────

class RequiredEvidenceItem(BaseModel):
    """A single category of evidence the policy requires."""
    category: str = Field(..., description="Short category label (e.g. 'prior_treatment')")
    description: str = Field(..., description="What evidence must be found")


class RequiredEvidence(BaseModel):
    """Structured output from the Policy Agent.

    Answers: 'What does the policy require us to look for?'
    Does NOT evaluate the patient. Does NOT make coverage decisions.
    """
    criterion_id: str
    requirement: str = Field(..., description="Human-readable policy requirement summary")
    required_evidence: List[RequiredEvidenceItem] = Field(
        default_factory=list,
        description="List of evidence categories needed to satisfy the criterion"
    )
    evaluation_type: str = "SEMANTIC"


# ── Agent 2 — Clinical Evidence Agent output ──────────────────────────────────

class ClinicalEvidenceResult(BaseModel):
    """Structured output from the Clinical Evidence Agent.

    Answers: 'What relevant evidence is available in the request?'
    Only extracts what is ACTUALLY present in the request — never infers
    or invents facts.
    """
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="Statements from the request that support the policy requirement"
    )
    contradicting_evidence: List[str] = Field(
        default_factory=list,
        description="Statements that contradict the policy requirement"
    )
    missing_evidence: List[str] = Field(
        default_factory=list,
        description="Required evidence categories not found in the request"
    )
    raw_clinical_text: str = Field(
        default="",
        description="The clinical text that was searched (for audit)"
    )


# ── Agent 3 — Evaluation Agent output ────────────────────────────────────────

class EvidenceSufficiency(str, Enum):
    """Pre-assessment by the Evaluation Agent before calling Qwen."""
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class EvaluationAgentResult(BaseModel):
    """Structured output from the Evaluation Agent.

    Prepares the semantic evaluation context for Qwen.
    The Evaluation Agent does NOT call Qwen — it prepares the structured
    context that will be sent to Qwen.
    """
    pre_assessment: EvidenceSufficiency
    qwen_prompt_context: str = Field(
        ...,
        description="Structured context ready to send to Qwen (policy + evidence summary)"
    )
    assessment_summary: str = Field(
        ...,
        description="Human-readable pre-assessment summary"
    )


# ── Qwen result ───────────────────────────────────────────────────────────────

class QwenSemanticResult(BaseModel):
    """Structured result returned by Qwen via LM Studio.

    Qwen is ONLY allowed to return SATISFIED / NOT_SATISFIED / UNKNOWN.
    Any other value is treated as UNKNOWN.
    """
    result: SemanticResult = SemanticResult.UNKNOWN
    evidence_cited: List[str] = Field(
        default_factory=list,
        description="Specific evidence Qwen cited from the patient record"
    )
    explanation: str = Field(
        default="",
        description="Concise explanation (no hidden chain-of-thought)"
    )


# ── Agent 4 — Critic Agent output ─────────────────────────────────────────────

class CriticResult(BaseModel):
    """Structured output from the Critic Agent.

    Validates Qwen's semantic conclusion.
    If REJECTED, the final semantic result becomes UNKNOWN.
    """
    verdict: CriticVerdict
    checks_performed: List[str] = Field(
        default_factory=list,
        description="List of validation checks that were performed"
    )
    rejection_reason: Optional[str] = Field(
        default=None,
        description="Why Qwen's result was rejected (if applicable)"
    )
    validated_result: SemanticResult = Field(
        default=SemanticResult.UNKNOWN,
        description="The final validated result after critic review"
    )


# ── Agent trace ───────────────────────────────────────────────────────────────

class AgentTraceEntry(BaseModel):
    """Audit trace entry for a single agent step.

    Does NOT expose raw prompts, hidden reasoning, or chain-of-thought.
    Only concise, auditable summaries.
    """
    agent: str
    status: AgentStatus
    output_summary: str
    result: Optional[str] = None


# ── Final orchestration result ────────────────────────────────────────────────

class AgentOrchestrationResult(BaseModel):
    """Final structured output of the AgentOrchestrator.

    This is the complete semantic evaluation result ready for the
    SemanticEvaluator to map into an EvaluatedCriterion.

    CRITICAL INVARIANT:
    final_result is always one of: SATISFIED | NOT_SATISFIED | UNKNOWN
    It is NEVER: APPROVE | PEND | REQUEST_MORE_INFORMATION
    """
    criterion_id: str
    criterion: str
    evaluator: str = "AGENTIC_QWEN"

    # Policy Agent outputs
    policy_requirement: str = ""
    required_evidence: List[str] = Field(default_factory=list)

    # Clinical Evidence Agent outputs
    patient_evidence: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)

    # Qwen outputs
    qwen_result: SemanticResult = SemanticResult.UNKNOWN
    qwen_evidence: List[str] = Field(default_factory=list)

    # Critic outputs
    critic_result: CriticVerdict = CriticVerdict.REJECTED

    # Final
    final_result: SemanticResult = SemanticResult.UNKNOWN
    explanation: str = ""

    # Audit trail (no raw prompts / chain-of-thought)
    agent_trace: List[AgentTraceEntry] = Field(default_factory=list)
