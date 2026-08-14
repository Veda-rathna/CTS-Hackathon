"""Tests for the RAG and LLM Evaluation Pipeline."""
import pytest
from app.schemas.evaluation import CriterionType, EvaluationStatus, EvaluatorType, PolicyCriterion, EvaluatedCriterion
from app.schemas.triage import TriageRequest
from app.services.evaluation.criterion_classifier import CriterionClassifier
from app.services.evaluation.criterion_extractor import CriterionExtractor
from app.services.evaluation.evidence_fusion import EvidenceFusion
from app.models.policy_chunk import PolicyChunk


def test_criterion_classifier_structured():
    criterion = {"criterion_id": "1", "criterion": "Must have HCPCS code 99213", "policy_type": "NCD", "policy_id": "123"}
    classified = CriterionClassifier.classify(criterion)
    assert classified.type == CriterionType.STRUCTURED


def test_criterion_classifier_rule():
    criterion = {"criterion_id": "2", "criterion": "Patient age must be greater than 65 years old", "policy_type": "NCD", "policy_id": "123"}
    classified = CriterionClassifier.classify(criterion)
    assert classified.type == CriterionType.RULE_BASED


def test_criterion_classifier_semantic():
    criterion = {"criterion_id": "3", "criterion": "Documentation must show conservative treatment failed", "policy_type": "NCD", "policy_id": "123"}
    classified = CriterionClassifier.classify(criterion)
    assert classified.type == CriterionType.SEMANTIC


def test_criterion_extractor():
    chunk = PolicyChunk(
        policy_type="NCD",
        policy_id="123",
        chunk_text="- Patient has a history of heart disease.\n- Documentation must support medical necessity.",
    )
    extracted = CriterionExtractor.extract_from_chunk(chunk)
    assert len(extracted) > 0
    assert "Patient has a history of heart disease" in extracted[0]["criterion"]


def test_evidence_fusion_authority():
    criteria = [
        EvaluatedCriterion(
            criterion_id="C1",
            policy_type="NCD",
            policy_id="123",
            criterion="HCPCS Code",
            criterion_type=CriterionType.STRUCTURED,
            evaluator=EvaluatorType.SQL,
            status=EvaluationStatus.NOT_SATISFIED,
            mandatory=True,
            authoritative=True,
        ),
        EvaluatedCriterion(
            criterion_id="C2",
            policy_type="NCD",
            policy_id="123",
            criterion="Conservative treatment",
            criterion_type=CriterionType.SEMANTIC,
            evaluator=EvaluatorType.LLM,
            status=EvaluationStatus.SATISFIED,
            mandatory=True,
            authoritative=False,
        )
    ]
    
    matrix = EvidenceFusion.fuse(criteria)
    decision = EvidenceFusion.resolve_decision(matrix)
    
    # Deterministic NOT_SATISFIED should override LLM SATISFIED, resulting in EXCLUDED
    assert decision == "EXCLUDED"
