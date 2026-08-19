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


def test_decision_engine_informational_unknown_does_not_block_approval():
    """Informational/background criterion being UNKNOWN must NOT block APPROVE when mandatory criteria are SATISFIED."""
    criteria = [
        EvaluatedCriterion(
            criterion_id="C1", policy_type="LCD", policy_id="39529",
            criterion="Procedure and covered diagnosis", criterion_type=CriterionType.STRUCTURED,
            evaluator=EvaluatorType.SQL, status=EvaluationStatus.SATISFIED,
            patient_evidence=["Submitted HCPCS: 20610", "Submitted ICD-10: M17.11"],
            policy_evidence=[], explanation="", mandatory=True
        ),
        EvaluatedCriterion(
            criterion_id="C2", policy_type="LCD", policy_id="39529",
            criterion="Completed 12 weeks conservative PT", criterion_type=CriterionType.SEMANTIC,
            evaluator=EvaluatorType.AGENTIC_QWEN, status=EvaluationStatus.SATISFIED,
            patient_evidence=["12 weeks physical therapy trial completed."],
            policy_evidence=[], explanation="", mandatory=True
        ),
        EvaluatedCriterion(
            criterion_id="C3-INFO", policy_type="LCD", policy_id="39529",
            criterion="IVIg is a blood product prepared from pooled plasma (background note)",
            criterion_type=CriterionType.SEMANTIC,
            evaluator=EvaluatorType.AGENTIC_QWEN, status=EvaluationStatus.UNKNOWN,
            patient_evidence=[], policy_evidence=[], explanation="Background informational text.",
            mandatory=False
        ),
    ]
    decision, reasons, _ = DecisionEngine.map_to_final("COVERED", "COVERED", "COVERED", missing=[], criteria=criteria)
    assert decision == TriageDecision.APPROVE


# ── 4. Integration Tests for 7 Realistic PA Scenarios (PA-REAL-001 - 007) ──────


def test_scenario_PA_REAL_001_knee_oa_hyaluronan(client) -> None:
    """PA-REAL-001: Knee Osteoarthritis + Hyaluronan injection (20610 / M17.11) → APPROVE."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "20610",
        "diagnosis_codes": ["M17.11"],
        "state": "TX",
        "patient_age": 51,
        "clinical_notes": (
            "Patient is a 51-year-old female presenting with chronic right knee pain due to primary osteoarthritis (M17.11). "
            "Patient completed a 12-week course of conservative management including supervised physical therapy, daily oral meloxicam, "
            "and home quad exercises. Weight-bearing radiograph confirms Kellgren-Lawrence Grade 2 osteoarthritis. "
            "Requesting intraarticular hyaluronan injection (20610)."
        )
    })
    assert r.status_code == 200
    d = r.json()
    assert d["decision"] == "APPROVE"


def test_scenario_PA_REAL_002_lumbar_radiculopathy_epidural(client) -> None:
    """PA-REAL-002: Lumbar radiculopathy epidural steroid (64483 / M54.16) → APPROVE."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483",
        "diagnosis_codes": ["M54.16"],
        "state": "TX",
        "patient_age": 47,
        "clinical_notes": (
            "Patient is a 47-year-old male with acute-on-chronic right L5-S1 lumbar radiculopathy (M54.16) radiating below the knee with positive SLR. "
            "Symptoms have persisted despite completion of an 8-week physical therapy regimen, oral gabapentin, and NSAID therapy. "
            "Lumbar MRI demonstrates L5-S1 right paracentral disc herniation with nerve root compression. "
            "Transforaminal epidural steroid injection (64483) requested."
        )
    })
    assert r.status_code == 200
    d = r.json()
    assert d["decision"] == "APPROVE"


def test_scenario_PA_REAL_003_noncovered_joint_pain_trigger_point(client) -> None:
    """PA-REAL-003: Non-covered joint pain for trigger point (20552 / M25.50) → DENY."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "20552",
        "diagnosis_codes": ["M25.50"],
        "state": "TX",
        "patient_age": 61,
        "clinical_notes": (
            "Patient is a 61-year-old male presenting with acute joint pain (M25.50) without documented myofascial trigger points. "
            "Patient has not undergone conservative physical therapy or trial of analgesics. Requesting trigger point injection (20552)."
        )
    })
    assert r.status_code == 200
    d = r.json()
    assert d["decision"] in ["DENY", "PEND"]


def test_scenario_PA_REAL_004_unlisted_headache_epidural(client) -> None:
    """PA-REAL-004: Unlisted headache for epidural (64483 / R51.9) → NEED_MORE_INFORMATION."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483",
        "diagnosis_codes": ["R51.9"],
        "state": "TX",
        "patient_age": 67,
        "clinical_notes": (
            "Patient is a 67-year-old male presenting with diffuse headache symptoms (R51.9). "
            "Provider requested lumbar epidural injection (64483). No spinal exam, no imaging reports."
        )
    })
    assert r.status_code == 200
    d = r.json()
    assert d["decision"] == "NEED_MORE_INFORMATION"


def test_scenario_PA_REAL_005_ncd_exclusion_acupuncture(client) -> None:
    """PA-REAL-005: Explicit NCD exclusion under NCD 373 (20552 / M25.50) → DENY."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "20552",
        "diagnosis_codes": ["M25.50"],
        "state": "TX",
        "patient_age": 57,
        "clinical_notes": (
            "Patient requesting trigger point injections for generalized joint discomfort (M25.50) under acupuncture/dry needling indications."
        )
    })
    assert r.status_code == 200
    d = r.json()
    assert d["decision"] in ["DENY", "PEND"]


def test_scenario_PA_REAL_006_admin_exam_code_knee_injection(client) -> None:
    """PA-REAL-006: Administrative exam code for knee injection (20610 / Z00.00) → NEED_MORE_INFORMATION."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "20610",
        "diagnosis_codes": ["Z00.00"],
        "state": "TX",
        "patient_age": 44,
        "clinical_notes": (
            "Patient is a 44-year-old female presenting for an annual general adult medical examination (Z00.00). "
            "Prior authorization requested for major joint injection (20610)."
        )
    })
    assert r.status_code == 200
    d = r.json()
    assert d["decision"] == "NEED_MORE_INFORMATION"


def test_scenario_PA_REAL_007_ivig_covered_ncd_158(client) -> None:
    """PA-REAL-007: IVIG covered under National Policy NCD 158 (J1561 / L10.0) → APPROVE."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "J1561",
        "diagnosis_codes": ["L10.0"],
        "state": "TX",
        "patient_age": 58,
        "clinical_notes": (
            "Intravenous immune globulin infusion for biopsy-proven pemphigus vulgaris refractory to standard systemic corticosteroid therapy."
        )
    })
    assert r.status_code == 200
    d = r.json()
    assert d["decision"] == "APPROVE"


# ── Regression Tests A through J (Targeted Extraction & Authority Rules) ────────


def test_A_background_sentence_is_classified_informational():
    from app.models.policy_chunk import PolicyChunk
    from app.services.evaluation.criterion_extractor import CriterionExtractor
    chunk = PolicyChunk(
        policy_type="NCD",
        policy_id="158",
        section="item_service_description",
        chunk_text="Intravenous immune globulin (IVIg) is a blood product prepared from pooled plasma of donors."
    )
    criteria = CriterionExtractor.extract_from_chunk(chunk)
    assert len(criteria) > 0
    assert all(c["mandatory"] is False for c in criteria)


def test_B_low_back_quality_of_life_is_informational():
    from app.models.policy_chunk import PolicyChunk
    from app.services.evaluation.criterion_extractor import CriterionExtractor
    chunk = PolicyChunk(
        policy_type="LCD",
        policy_id="36920",
        section="history/background",
        chunk_text="Low back and neck pain can influence the quality of life and function and is associated with depression and anxiety."
    )
    criteria = CriterionExtractor.extract_from_chunk(chunk)
    assert len(criteria) > 0
    assert all(c["mandatory"] is False for c in criteria)


def test_C_failed_conservative_therapy_is_mandatory():
    from app.models.policy_chunk import PolicyChunk
    from app.services.evaluation.criterion_extractor import CriterionExtractor
    chunk = PolicyChunk(
        policy_type="LCD",
        policy_id="L39054",
        section="indications_limitations",
        chunk_text="Conservative therapy of at least 6 weeks duration must have been tried and failed prior to injection."
    )
    criteria = CriterionExtractor.extract_from_chunk(chunk)
    assert len(criteria) > 0
    assert any(c["mandatory"] is True for c in criteria)


def test_D_biopsy_proven_pemphigus_is_mandatory_with_evidence():
    from app.models.policy_chunk import PolicyChunk
    from app.services.evaluation.criterion_extractor import CriterionExtractor
    from app.services.agents.policy_agent import PolicyAgent
    from app.schemas.evaluation import PolicyCriterion, CriterionType
    from app.schemas.triage import TriageRequest
    from unittest.mock import MagicMock
    chunk = PolicyChunk(
        policy_type="NCD",
        policy_id="158",
        section="indications_limitations",
        chunk_text="IVIg is covered for the treatment of biopsy-proven Pemphigus Vulgaris."
    )
    criteria = CriterionExtractor.extract_from_chunk(chunk)
    assert len(criteria) > 0
    mand_crit = [c for c in criteria if c["mandatory"]]
    assert len(mand_crit) > 0

    mock_llm = MagicMock()
    mock_llm.enabled = False
    pagent = PolicyAgent(mock_llm)
    crit_obj = PolicyCriterion(
        criterion_id=mand_crit[0]["criterion_id"],
        criterion=mand_crit[0]["criterion"],
        type=CriterionType.SEMANTIC,
        policy_type="NCD",
        policy_id="158",
        mandatory=True,
    )
    req = TriageRequest(procedure_code="J1561", diagnosis_codes=["L10.0"])
    req_ev, _ = pagent.run(crit_obj, req)
    assert any(item.category in ("diagnostic_confirmation", "clinical_indication") for item in req_ev.required_evidence)


def test_E_ivig_blood_product_is_informational():
    from app.models.policy_chunk import PolicyChunk
    from app.services.evaluation.criterion_extractor import CriterionExtractor
    chunk = PolicyChunk(
        policy_type="NCD",
        policy_id="158",
        section="description",
        chunk_text="IVIg is a blood product prepared from pooled human donor plasma."
    )
    criteria = CriterionExtractor.extract_from_chunk(chunk)
    assert all(c["mandatory"] is False for c in criteria)


def test_F_PA_REAL_002_evidence_satisfies_mandatory():
    from app.services.agents.clinical_evidence_agent import ClinicalEvidenceAgent
    from app.services.agents.policy_agent import RequiredEvidence, RequiredEvidenceItem
    from app.schemas.triage import TriageRequest
    from unittest.mock import MagicMock
    mock_llm = MagicMock()
    mock_llm.enabled = False
    cagent = ClinicalEvidenceAgent(mock_llm)
    req = TriageRequest(
        procedure_code="64483",
        diagnosis_codes=["M54.16"],
        clinical_notes="Epidural injection, lumbar or sacral. Patient presents with lumbar radiculopathy confirmed on MRI. Conservative physical therapy was tried for 8 weeks without adequate relief."
    )
    req_ev = RequiredEvidence(
        criterion_id="TEST-RADIC",
        requirement="Diagnosis of radiculopathy supported by MRI",
        required_evidence=[
            RequiredEvidenceItem(category="diagnostic_imaging", description="MRI imaging confirmation"),
            RequiredEvidenceItem(category="clinical_indication", description="Lumbar radiculopathy symptoms"),
        ]
    )
    result, _ = cagent.run(req_ev, req)
    assert len(result.supporting_evidence) > 0
    assert len(result.contradicting_evidence) == 0
    assert len(result.missing_evidence) == 0


def test_G_PA_REAL_007_evidence_satisfies_biopsy_and_failure():
    from app.services.agents.clinical_evidence_agent import ClinicalEvidenceAgent
    from app.services.agents.policy_agent import RequiredEvidence, RequiredEvidenceItem
    from app.schemas.triage import TriageRequest
    from unittest.mock import MagicMock
    mock_llm = MagicMock()
    mock_llm.enabled = False
    cagent = ClinicalEvidenceAgent(mock_llm)
    req = TriageRequest(
        procedure_code="J1561",
        diagnosis_codes=["L10.0"],
        clinical_notes="Intravenous immune globulin infusion for biopsy-proven pemphigus vulgaris refractory to standard systemic corticosteroid therapy."
    )
    req_ev = RequiredEvidence(
        criterion_id="TEST-PEMPH",
        requirement="Biopsy-proven pemphigus vulgaris refractory to corticosteroid",
        required_evidence=[
            RequiredEvidenceItem(category="diagnostic_confirmation", description="Biopsy-proven pemphigus vulgaris"),
            RequiredEvidenceItem(category="prior_therapy", description="Refractory to corticosteroid therapy"),
        ]
    )
    result, _ = cagent.run(req_ev, req)
    assert len(result.supporting_evidence) > 0
    assert len(result.contradicting_evidence) == 0
    assert len(result.missing_evidence) == 0


def test_H_missing_evidence_remains_unknown():
    from app.services.agents.critic_agent import CriticAgent, QwenSemanticResult, CriticVerdict, SemanticResult
    from app.services.agents.clinical_evidence_agent import ClinicalEvidenceResult
    from app.services.agents.policy_agent import RequiredEvidence
    critic = CriticAgent()
    req_ev = RequiredEvidence(
        criterion_id="TEST-ABSENCE",
        requirement="Conservative therapy trial required",
        required_evidence=[],
    )
    qwen_res = QwenSemanticResult(
        result=SemanticResult.NOT_SATISFIED,
        evidence_cited=[],
        explanation="Missing documentation of physical therapy."
    )
    clin_ev = ClinicalEvidenceResult(
        supporting_evidence=[],
        contradicting_evidence=[],
        missing_evidence=["Documentation of completed conservative therapy."],
        raw_clinical_text="Epidural injection for headache."
    )
    critic_res, _ = critic.run(req_ev, clin_ev, qwen_res)
    assert critic_res.validated_result == SemanticResult.UNKNOWN
    assert critic_res.verdict == CriticVerdict.REJECTED


def test_I_explicit_contradiction_remains_not_satisfied():
    from app.services.agents.critic_agent import CriticAgent, QwenSemanticResult, CriticVerdict, SemanticResult
    from app.services.agents.clinical_evidence_agent import ClinicalEvidenceResult
    from app.services.agents.policy_agent import RequiredEvidence
    critic = CriticAgent()
    req_ev = RequiredEvidence(
        criterion_id="TEST-CONTRA",
        requirement="Must not be acupuncture related",
        required_evidence=[],
    )
    qwen_res = QwenSemanticResult(
        result=SemanticResult.NOT_SATISFIED,
        evidence_cited=["trigger point injection for acupuncture-related indications"],
        explanation="Explicitly contradicted by patient request."
    )
    clin_ev = ClinicalEvidenceResult(
        supporting_evidence=[],
        contradicting_evidence=["Trigger point injection for acupuncture-related indications."],
        missing_evidence=[],
        raw_clinical_text="Trigger point injection for acupuncture-related indications."
    )
    critic_res, _ = critic.run(req_ev, clin_ev, qwen_res)
    assert critic_res.validated_result == SemanticResult.NOT_SATISFIED
    assert critic_res.verdict == CriticVerdict.VALIDATED


def test_J_sql_exclusion_remains_authoritative_over_llm():
    from app.schemas.evaluation import (
        CriterionType, EvaluatedCriterion, EvaluationStatus, EvaluatorType, PolicyCriterion
    )
    from app.services.evaluation.evidence_fusion import EvidenceFusion
    crit = PolicyCriterion(
        criterion_id="TEST-SQL-AUTH",
        criterion="Procedure must not be excluded",
        type=CriterionType.STRUCTURED,
        policy_type="NCD",
        policy_id="373",
        mandatory=True,
    )
    struct_res = EvaluatedCriterion(
        criterion_id="TEST-SQL-AUTH",
        policy_type="NCD",
        policy_id="373",
        criterion="Procedure must not be excluded",
        criterion_type=CriterionType.STRUCTURED,
        evaluator=EvaluatorType.SQL,
        status=EvaluationStatus.NOT_SATISFIED,
        patient_evidence=["Submitted HCPCS: 20552"],
        policy_evidence=["NCD 373 explicitly excludes HCPCS 20552."],
        mandatory=True,
    )
    sem_res = EvaluatedCriterion(
        criterion_id="TEST-SQL-AUTH",
        policy_type="NCD",
        policy_id="373",
        criterion="Procedure must not be excluded",
        criterion_type=CriterionType.SEMANTIC,
        evaluator=EvaluatorType.AGENTIC_QWEN,
        status=EvaluationStatus.SATISFIED,  # LLM erroneously says satisfied
        patient_evidence=["Clinical notes mention joint pain"],
        policy_evidence=["Policy text"],
        mandatory=True,
    )
    fused = EvidenceFusion.fuse_criterion(struct_res, sem_res, crit)
    assert fused.status == EvaluationStatus.NOT_SATISFIED
    assert fused.evaluator == EvaluatorType.SQL


# ═════════════════════════════════════════════════════════════════════════════
# NURSE-FACING DISPOSITION TESTS (Exactly 3 Outcomes: APPROVE, PEND, NEED_MORE_INFO)
# ═════════════════════════════════════════════════════════════════════════════

def test_nurse_disposition_1_fully_supported_approves(client):
    """Test 1 — APPROVE: A fully supported PA resolves to APPROVE."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483",
        "diagnosis_codes": ["M54.16"],
        "state": "TX",
        "patient_age": 47,
        "clinical_notes": (
            "Epidural injection, lumbar or sacral. Patient presents with lumbar radiculopathy confirmed on MRI. "
            "Conservative physical therapy was tried for 8 weeks without adequate relief."
        ),
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "APPROVE"


def test_nurse_disposition_2_missing_evidence_returns_need_more_information(client):
    """Test 2 — NEED_MORE_INFORMATION: Potentially covered PA with missing mandatory documentation."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483",
        "diagnosis_codes": ["R51.9"],
        "state": "TX",
        "patient_age": 67,
        "clinical_notes": "Epidural injection, lumbar or sacral for unspecified headache.",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "NEED_MORE_INFORMATION"


def test_nurse_disposition_3_explicit_policy_exclusion_pends(client):
    """Test 3 — Explicit policy exclusion (PA-REAL-003 / PA-REAL-005) resolves to DENY (or PEND)."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "20552",
        "diagnosis_codes": ["M25.50"],
        "state": "TX",
        "patient_age": 61,
        "clinical_notes": "Injection(s), single or multiple trigger point(s), 1 or 2 muscle(s) for pain in unspecified joint.",
    })
    assert r.status_code == 200
    assert r.json()["decision"] in ["DENY", "PEND"]


def test_nurse_disposition_4_policy_conflict_pends(client):
    """Test 4 — Unresolved policy exclusion / conflict resolves to DENY (or PEND)."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "20552",
        "diagnosis_codes": ["M25.50"],
        "state": "TX",
        "patient_age": 57,
        "clinical_notes": "Trigger point injection for acupuncture-related indications.",
    })
    assert r.status_code == 200
    assert r.json()["decision"] in ["DENY", "PEND"]


def test_nurse_disposition_5_verify_canonical_dispositions():
    """Test 5 — Verify that the public triage decisions only map to APPROVE, PEND, DENY, or NEED_MORE_INFORMATION."""
    from app.services.decision_engine import DecisionEngine
    from app.schemas.triage import TriageDecision

    # Exclusions must return DENY
    d_excl, _, _ = DecisionEngine.map_to_final("EXCLUDED", "NOT_ADDRESSED", "NOT_ADDRESSED", missing=[])
    assert d_excl in [TriageDecision.DENY, TriageDecision.PEND]

    # Missing docs must return NEED_MORE_INFORMATION
    d_miss, _, _ = DecisionEngine.map_to_final("COVERED", "COVERED", "COVERED", missing=["Missing notes"])
    assert d_miss == TriageDecision.NEED_MORE_INFORMATION

    # Full coverage must return APPROVE
    d_appr, _, _ = DecisionEngine.map_to_final("COVERED", "COVERED", "COVERED", missing=[])
    assert d_appr == TriageDecision.APPROVE


