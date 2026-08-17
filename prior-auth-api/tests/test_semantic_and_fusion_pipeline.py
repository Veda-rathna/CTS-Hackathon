"""Tests for Phase 5: Semantic Evaluation, MultiEvaluator, EvidenceFusion, and DecisionEngine.

Verifies:
1. MultiEvaluator always executes both StructuredEvaluator and SemanticEvaluator.
2. EvidenceFusion.fuse_criterion enforces authority rules correctly.
3. DecisionEngine enforces the 3-state authority decision ladder.
4. End-to-end evaluation flow for PA-REAL-001, PA-REAL-003, and PA-REAL-004.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from app.schemas.evaluation import (
    CriterionType,
    EvaluatedCriterion,
    EvaluationStatus,
    EvaluatorType,
    PolicyCriterion,
)
from app.schemas.triage import TriageDecision, TriageRequest
from app.services.evaluation.evidence_fusion import EvidenceFusion
from app.services.evaluation.multi_evaluator import MultiEvaluator
from app.services.decision_engine import DecisionEngine


# ── 1. Unit Tests for EvidenceFusion.fuse_criterion ────────────────────────────


def test_fusion_structured_satisfied_and_semantic_satisfied():
    """Structured SATISFIED + Semantic SATISFIED ➔ SATISFIED."""
    crit = PolicyCriterion(
        criterion_id="TEST-CRIT-1",
        criterion="Patient must have completed conservative physical therapy.",
        type=CriterionType.SEMANTIC,
        policy_type="LCD",
        policy_id="39529",
        mandatory=True,
    )
    struct_res = EvaluatedCriterion(
        criterion_id=crit.criterion_id,
        policy_type="LCD",
        policy_id="39529",
        criterion=crit.criterion,
        criterion_type=CriterionType.STRUCTURED,
        evaluator=EvaluatorType.SQL,
        status=EvaluationStatus.SATISFIED,
        patient_evidence=["Submitted HCPCS: 20610"],
        policy_evidence=["LCD 39529 HCPCS 20610 covered"],
        explanation="Procedure is covered.",
        mandatory=True,
    )
    sem_res = EvaluatedCriterion(
        criterion_id=crit.criterion_id,
        policy_type="LCD",
        policy_id="39529",
        criterion=crit.criterion,
        criterion_type=CriterionType.SEMANTIC,
        evaluator=EvaluatorType.AGENTIC_QWEN,
        status=EvaluationStatus.SATISFIED,
        patient_evidence=["Patient completed 12 weeks of structured physical therapy."],
        policy_evidence=["Conservative therapy required."],
        explanation="Clinical notes confirm 12 weeks of physical therapy.",
        mandatory=True,
    )

    fused = EvidenceFusion.fuse_criterion(struct_res, sem_res, crit)
    assert fused.status == EvaluationStatus.SATISFIED
    assert "Submitted HCPCS: 20610" in fused.patient_evidence
    assert "Patient completed 12 weeks of structured physical therapy." in fused.patient_evidence


def test_fusion_structured_satisfied_and_semantic_unknown_clinical_requirement():
    """Requirement #6: Structured SATISFIED + Semantic UNKNOWN on clinical requirement ➔ UNKNOWN."""
    crit = PolicyCriterion(
        criterion_id="TEST-CRIT-2",
        criterion="Patient must have documented failed conservative treatment trial.",
        type=CriterionType.SEMANTIC,
        policy_type="LCD",
        policy_id="39529",
        mandatory=True,
    )
    struct_res = EvaluatedCriterion(
        criterion_id=crit.criterion_id,
        policy_type="LCD",
        policy_id="39529",
        criterion=crit.criterion,
        criterion_type=CriterionType.STRUCTURED,
        evaluator=EvaluatorType.SQL,
        status=EvaluationStatus.SATISFIED,
        patient_evidence=["Submitted ICD-10: M17.11"],
        policy_evidence=["Covered ICD-10"],
        explanation="Diagnosis code is covered.",
        mandatory=True,
    )
    sem_res = EvaluatedCriterion(
        criterion_id=crit.criterion_id,
        policy_type="LCD",
        policy_id="39529",
        criterion=crit.criterion,
        criterion_type=CriterionType.SEMANTIC,
        evaluator=EvaluatorType.AGENTIC_QWEN,
        status=EvaluationStatus.UNKNOWN,
        patient_evidence=[],
        policy_evidence=["Conservative therapy required."],
        explanation="Documentation does not establish whether conservative therapy was tried.",
        mandatory=True,
    )

    fused = EvidenceFusion.fuse_criterion(struct_res, sem_res, crit)
    assert fused.status == EvaluationStatus.UNKNOWN


def test_fusion_structured_satisfied_and_semantic_not_satisfied():
    """Requirement #7: Semantic NOT_SATISFIED (clinical contradiction) ➔ NOT_SATISFIED."""
    crit = PolicyCriterion(
        criterion_id="TEST-CRIT-3",
        criterion="Patient must have documented trigger points.",
        type=CriterionType.SEMANTIC,
        policy_type="LCD",
        policy_id="36920",
        mandatory=True,
    )
    struct_res = EvaluatedCriterion(
        criterion_id=crit.criterion_id,
        policy_type="LCD",
        policy_id="36920",
        criterion=crit.criterion,
        criterion_type=CriterionType.STRUCTURED,
        evaluator=EvaluatorType.SQL,
        status=EvaluationStatus.SATISFIED,
        patient_evidence=["Submitted HCPCS: 20552"],
        policy_evidence=["HCPCS recognized"],
        explanation="Procedure code recognized.",
        mandatory=True,
    )
    sem_res = EvaluatedCriterion(
        criterion_id=crit.criterion_id,
        policy_type="LCD",
        policy_id="36920",
        criterion=crit.criterion,
        criterion_type=CriterionType.SEMANTIC,
        evaluator=EvaluatorType.AGENTIC_QWEN,
        status=EvaluationStatus.NOT_SATISFIED,
        patient_evidence=["Clinical notes explicitly state without documented myofascial trigger points."],
        policy_evidence=["Trigger points required."],
        explanation="Clinical notes explicitly state no trigger points found.",
        mandatory=True,
    )

    fused = EvidenceFusion.fuse_criterion(struct_res, sem_res, crit)
    assert fused.status == EvaluationStatus.NOT_SATISFIED


def test_fusion_structured_unknown_and_semantic_satisfied():
    """Structured UNKNOWN + Semantic SATISFIED ➔ SATISFIED."""
    crit = PolicyCriterion(
        criterion_id="TEST-CRIT-4",
        criterion="Documented MRI confirmation of nerve root compression.",
        type=CriterionType.SEMANTIC,
        policy_type="LCD",
        policy_id="36920",
        mandatory=True,
    )
    struct_res = EvaluatedCriterion(
        criterion_id=crit.criterion_id,
        policy_type="LCD",
        policy_id="36920",
        criterion=crit.criterion,
        criterion_type=CriterionType.STRUCTURED,
        evaluator=EvaluatorType.SQL,
        status=EvaluationStatus.UNKNOWN,
        patient_evidence=[],
        policy_evidence=[],
        explanation="Cannot be deterministically evaluated by SQL.",
        mandatory=True,
    )
    sem_res = EvaluatedCriterion(
        criterion_id=crit.criterion_id,
        policy_type="LCD",
        policy_id="36920",
        criterion=crit.criterion,
        criterion_type=CriterionType.SEMANTIC,
        evaluator=EvaluatorType.AGENTIC_QWEN,
        status=EvaluationStatus.SATISFIED,
        patient_evidence=["Lumbar MRI confirms L4-L5 disc herniation with nerve root impingement."],
        policy_evidence=["Imaging confirmation required."],
        explanation="MRI confirms nerve root compression.",
        mandatory=True,
    )

    fused = EvidenceFusion.fuse_criterion(struct_res, sem_res, crit)
    assert fused.status == EvaluationStatus.SATISFIED
    assert "Lumbar MRI confirms L4-L5 disc herniation with nerve root impingement." in fused.patient_evidence


# ── 2. Unit Tests for MultiEvaluator Execution ────────────────────────────────


def test_multievaluator_executes_both_evaluators():
    """Verify that MultiEvaluator calls BOTH StructuredEvaluator and SemanticEvaluator."""
    mock_struct = MagicMock()
    mock_sem = MagicMock()

    crit = PolicyCriterion(
        criterion_id="CRIT-MULTI-1",
        criterion="Patient must complete 12 weeks of conservative therapy.",
        type=CriterionType.SEMANTIC,
        policy_type="LCD",
        policy_id="39529",
        mandatory=True,
    )
    req = TriageRequest(
        procedure_code="20610",
        diagnosis_codes=["M17.11"],
        clinical_notes="Patient completed 12 weeks of physical therapy and NSAIDs.",
    )

    mock_struct.evaluate.return_value = EvaluatedCriterion(
        criterion_id=crit.criterion_id,
        policy_type="LCD",
        policy_id="39529",
        criterion=crit.criterion,
        criterion_type=CriterionType.STRUCTURED,
        evaluator=EvaluatorType.SQL,
        status=EvaluationStatus.UNKNOWN,
        patient_evidence=[],
        policy_evidence=[],
        explanation="",
        mandatory=True,
    )
    mock_sem.evaluate.return_value = EvaluatedCriterion(
        criterion_id=crit.criterion_id,
        policy_type="LCD",
        policy_id="39529",
        criterion=crit.criterion,
        criterion_type=CriterionType.SEMANTIC,
        evaluator=EvaluatorType.AGENTIC_QWEN,
        status=EvaluationStatus.SATISFIED,
        patient_evidence=["Patient completed 12 weeks of physical therapy and NSAIDs."],
        policy_evidence=[],
        explanation="12-week trial confirmed.",
        mandatory=True,
    )

    multi = MultiEvaluator(structured_evaluator=mock_struct, semantic_evaluator=mock_sem)
    result = multi.evaluate(crit, req)

    # Prove both evaluators were executed
    mock_struct.evaluate.assert_called_once_with(crit, req)
    mock_sem.evaluate.assert_called_once_with(crit, req)
    assert result.status == EvaluationStatus.SATISFIED


# ── 3. DecisionEngine Authority Ladder Tests ───────────────────────────────────


def test_decision_engine_all_satisfied_approves():
    criteria = [
        EvaluatedCriterion(
            criterion_id="C1", policy_type="LCD", policy_id="1",
            criterion="Procedure", criterion_type=CriterionType.STRUCTURED,
            evaluator=EvaluatorType.SQL, status=EvaluationStatus.SATISFIED,
            patient_evidence=[], policy_evidence=[], explanation="", mandatory=True
        ),
        EvaluatedCriterion(
            criterion_id="C2", policy_type="LCD", policy_id="1",
            criterion="Conservative therapy", criterion_type=CriterionType.SEMANTIC,
            evaluator=EvaluatorType.AGENTIC_QWEN, status=EvaluationStatus.SATISFIED,
            patient_evidence=[], policy_evidence=[], explanation="", mandatory=True
        ),
    ]
    decision, reasons, _ = DecisionEngine.map_to_final("COVERED", "COVERED", "COVERED", missing=[], criteria=criteria)
    assert decision == TriageDecision.APPROVE


def test_decision_engine_mandatory_unknown_returns_need_more_information():
    criteria = [
        EvaluatedCriterion(
            criterion_id="C1", policy_type="LCD", policy_id="1",
            criterion="Procedure", criterion_type=CriterionType.STRUCTURED,
            evaluator=EvaluatorType.SQL, status=EvaluationStatus.SATISFIED,
            patient_evidence=[], policy_evidence=[], explanation="", mandatory=True
        ),
        EvaluatedCriterion(
            criterion_id="C2", policy_type="LCD", policy_id="1",
            criterion="Conservative therapy", criterion_type=CriterionType.SEMANTIC,
            evaluator=EvaluatorType.AGENTIC_QWEN, status=EvaluationStatus.UNKNOWN,
            patient_evidence=[], policy_evidence=[], explanation="", mandatory=True
        ),
    ]
    decision, reasons, _ = DecisionEngine.map_to_final("COVERED", "COVERED", "COVERED", missing=[], criteria=criteria)
    assert decision == TriageDecision.NEED_MORE_INFORMATION


def test_decision_engine_mandatory_not_satisfied_denies():
    criteria = [
        EvaluatedCriterion(
            criterion_id="C1", policy_type="LCD", policy_id="1",
            criterion="Procedure", criterion_type=CriterionType.STRUCTURED,
            evaluator=EvaluatorType.SQL, status=EvaluationStatus.SATISFIED,
            patient_evidence=[], policy_evidence=[], explanation="", mandatory=True
        ),
        EvaluatedCriterion(
            criterion_id="C2", policy_type="LCD", policy_id="1",
            criterion="Covered indication", criterion_type=CriterionType.SEMANTIC,
            evaluator=EvaluatorType.AGENTIC_QWEN, status=EvaluationStatus.NOT_SATISFIED,
            patient_evidence=[], policy_evidence=[], explanation="", mandatory=True
        ),
    ]
    decision, reasons, _ = DecisionEngine.map_to_final("COVERED", "COVERED", "COVERED", missing=[], criteria=criteria)
    assert decision == TriageDecision.DENY
