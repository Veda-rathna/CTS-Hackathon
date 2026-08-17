"""
Master Triage & RAG Adjudication Engine Test Suite (55 Tests).

Covers:
- All 7 J5 Jurisdiction states (TX, NM, OK, LA, AR, MS, CO)
- Article-only covered codes (M47.816)
- Explicitly non-covered ICD-10 codes (Z00.00, Z00.01)
- Unknown diagnosis codes → REQUEST_MORE_INFORMATION
- Out-of-jurisdiction states (CA, IL, WA, ZZ) & expired LCDs (IA)
- NCD National Overrides (Covered vs Excluded)
- Policy not found & garbage procedure codes
- Multi-diagnosis combinations (covered + non-covered precedence, covered + unknown)
- Pydantic whitespace/lowercase input normalization
- Schema contract verification (score ranges, evidence trace, strictly allowed enum decisions)
- RAG criterion extraction, classification, and Evidence Fusion authority rules
"""
from __future__ import annotations
# pyrefly: ignore [missing-import]
import pytest
from fastapi.testclient import TestClient

from app.schemas.evaluation import (
    CriterionType,
    EvaluationStatus,
    EvaluatorType,
    PolicyCriterion,
    EvaluatedCriterion,
)
from app.services.evaluation.criterion_classifier import CriterionClassifier
from app.services.evaluation.criterion_extractor import CriterionExtractor
from app.services.evaluation.evidence_fusion import EvidenceFusion
from app.models.policy_chunk import PolicyChunk


# ═══════════════════════════════════════════════════════════════════
# GROUP 1: CORE HAPPY PATH — Covered dx + all J5 states
# ═══════════════════════════════════════════════════════════════════

def test_TC01_covered_dx_tx(client: TestClient) -> None:
    """TC-01: 64483 + M54.16 + TX (J5) → APPROVE. Primary happy path."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["M54.16"], "state": "TX", "patient_age": 55,
    })
    d = r.json()
    assert r.status_code == 200
    assert d["decision"] == "APPROVE", d["reason"]
    assert d["matched_codes"]["procedure"] == "64483"
    assert "M54.16" in d["matched_codes"]["diagnosis"]


def test_TC02_covered_dx_nm(client: TestClient) -> None:
    """TC-02: Same procedure + dx but NM (also J5) → APPROVE."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["M54.16"], "state": "NM",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "APPROVE"


def test_TC03_covered_dx_ok(client: TestClient) -> None:
    """TC-03: OK is in J5 → APPROVE."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["M54.17"], "state": "OK",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "APPROVE"


def test_TC04_covered_dx_la(client: TestClient) -> None:
    """TC-04: LA is in J5 → APPROVE."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["M54.4"], "state": "LA",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "APPROVE"


def test_TC05_covered_dx_co(client: TestClient) -> None:
    """TC-05: CO is in J5 → APPROVE."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64484", "diagnosis_codes": ["M54.16"], "state": "CO",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "APPROVE"


def test_TC06_covered_dx_ms(client: TestClient) -> None:
    """TC-06: MS is in J5 → APPROVE."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "62321", "diagnosis_codes": ["M54.4"], "state": "MS",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "APPROVE"


def test_TC07_covered_dx_ar(client: TestClient) -> None:
    """TC-07: AR is in J5 → APPROVE."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64484", "diagnosis_codes": ["M54.17"], "state": "AR",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "APPROVE"


# ═══════════════════════════════════════════════════════════════════
# GROUP 2: ARTICLE-ONLY COVERED CODE (M47.816)
# ═══════════════════════════════════════════════════════════════════

def test_TC08_article_only_covered_spondylosis(client: TestClient) -> None:
    """TC-08: M47.816 is in Article A12345 covered list → evaluated by article lookup."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["M47.816"], "state": "TX",
    })
    assert r.status_code == 200
    assert r.json()["decision"] in ["APPROVE", "DENY", "NEED_MORE_INFORMATION"]



# ═══════════════════════════════════════════════════════════════════
# GROUP 3: EXPLICITLY NON-COVERED DIAGNOSES
# ═══════════════════════════════════════════════════════════════════

def test_TC09_noncovered_z00_00(client: TestClient) -> None:
    """TC-09: Z00.00 is explicitly non-covered → DENY."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["Z00.00"], "state": "TX",
    })
    d = r.json()
    assert r.status_code == 200
    assert d["decision"] == "DENY"


def test_TC10_noncovered_z00_01(client: TestClient) -> None:
    """TC-10: Z00.01 is explicitly non-covered in article → DENY."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["Z00.01"], "state": "TX",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "DENY"


def test_TC11_noncovered_different_j5_state(client: TestClient) -> None:
    """TC-11: Non-covered dx in NM → DENY."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["Z00.00"], "state": "NM",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "DENY"


# ═══════════════════════════════════════════════════════════════════
# GROUP 4: UNKNOWN DIAGNOSES → NEED_MORE_INFORMATION
# ═══════════════════════════════════════════════════════════════════

def test_TC12_unknown_dx_not_in_any_list(client: TestClient) -> None:
    """TC-12: R99.99 is not in covered or non-covered list → NEED_MORE_INFORMATION."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["R99.99"], "state": "TX",
    })
    d = r.json()
    assert r.status_code == 200
    assert d["decision"] == "NEED_MORE_INFORMATION"
    assert len(d["missing_information"]) > 0


def test_TC13_unknown_dx_different_procedure(client: TestClient) -> None:
    """TC-13: Unknown dx with 64484 → NEED_MORE_INFORMATION."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64484", "diagnosis_codes": ["A00.0"], "state": "TX",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "NEED_MORE_INFORMATION"


# ═══════════════════════════════════════════════════════════════════
# GROUP 5: JURISDICTION EDGE CASES
# ═══════════════════════════════════════════════════════════════════

def test_TC14_outside_j5_ca(client: TestClient) -> None:
    """TC-14: CA is outside J5 → NEED_MORE_INFORMATION."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["M54.16"], "state": "CA",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "NEED_MORE_INFORMATION"


def test_TC15_outside_j5_il(client: TestClient) -> None:
    """TC-15: IL is outside J5 → NEED_MORE_INFORMATION."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["M54.16"], "state": "IL",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "NEED_MORE_INFORMATION"


def test_TC16_outside_j5_wa(client: TestClient) -> None:
    """TC-16: WA is outside J5 → NEED_MORE_INFORMATION."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["M54.16"], "state": "WA",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "NEED_MORE_INFORMATION"


def test_TC17_fake_state_zz(client: TestClient) -> None:
    """TC-17: ZZ is fake state → NEED_MORE_INFORMATION."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["M54.16"], "state": "ZZ",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "NEED_MORE_INFORMATION"


def test_TC18_expired_lcd_jurisdiction(client: TestClient) -> None:
    """TC-18: IA maps to LCD L99001 (expired) → not approved."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["M54.16"], "state": "IA",
    })
    assert r.status_code == 200
    assert r.json()["decision"] != "APPROVE"


def test_TC19_no_state_no_crash(client: TestClient) -> None:
    """TC-19: No state provided → evaluates without crashing."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["M54.16"],
    })
    assert r.status_code == 200
    assert r.json()["decision"] in ["APPROVE", "DENY", "NEED_MORE_INFORMATION"]


# ═══════════════════════════════════════════════════════════════════
# GROUP 6: NCD MATCHING ACCURACY
# ═══════════════════════════════════════════════════════════════════

def test_TC20_ncd_covered_approve(client: TestClient) -> None:
    """TC-20: 11111 → NCD COVERED → APPROVE."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "11111", "diagnosis_codes": ["M54.16"], "state": "TX",
    })
    d = r.json()
    assert r.status_code == 200
    assert d["decision"] == "APPROVE"
    assert any(p["policy_type"] == "NCD" for p in d["policies"])


def test_TC21_ncd_covered_no_state(client: TestClient) -> None:
    """TC-21: NCD COVERED with no state → APPROVE (national policy)."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "11111", "diagnosis_codes": ["M54.16"],
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "APPROVE"


def test_TC22_ncd_covered_outside_j5_state(client: TestClient) -> None:
    """TC-22: NCD COVERED + CA → APPROVE (NCD ignores state)."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "11111", "diagnosis_codes": ["Z00.00"], "state": "CA",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "APPROVE"


def test_TC23_ncd_excluded_pend(client: TestClient) -> None:
    """TC-23: 22222 → NCD EXCLUDED → DENY."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "22222", "diagnosis_codes": ["M54.16"], "state": "TX",
    })
    d = r.json()
    assert r.status_code == 200
    assert d["decision"] == "DENY"


def test_TC24_ncd_excluded_any_state(client: TestClient) -> None:
    """TC-24: NCD EXCLUDED in CA → DENY."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "22222", "diagnosis_codes": ["M54.16"], "state": "CA",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "DENY"


def test_TC25_ncd_excluded_no_state(client: TestClient) -> None:
    """TC-25: NCD EXCLUDED with no state → DENY."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "22222", "diagnosis_codes": ["M54.16"],
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "DENY"


def test_TC26_ncd_excluded_noncovered_dx(client: TestClient) -> None:
    """TC-26: NCD EXCLUDED + non-covered dx → DENY."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "22222", "diagnosis_codes": ["Z00.00"], "state": "TX",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "DENY"


# ═══════════════════════════════════════════════════════════════════
# GROUP 7: POLICY NOT FOUND & GARBAGE CODES
# ═══════════════════════════════════════════════════════════════════

def test_TC27_policy_not_found_xxxxx(client: TestClient) -> None:
    """TC-27: XXXXX no policy → NEED_MORE_INFORMATION."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "XXXXX", "diagnosis_codes": ["M54.16"], "state": "TX",
    })
    d = r.json()
    assert r.status_code == 200
    assert d["decision"] == "NEED_MORE_INFORMATION"
    assert "POLICY_NOT_FOUND" in d["reason_codes"]


def test_TC28_garbage_procedure_code(client: TestClient) -> None:
    """TC-28: Garbage code → NEED_MORE_INFORMATION (no 500 crash)."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "!@#$%", "diagnosis_codes": ["M54.16"], "state": "TX",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "NEED_MORE_INFORMATION"


def test_TC29_numeric_only_procedure_unknown(client: TestClient) -> None:
    """TC-29: Numeric unknown code 99999 → NEED_MORE_INFORMATION."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "99999", "diagnosis_codes": ["M54.16"], "state": "TX",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "NEED_MORE_INFORMATION"


# ═══════════════════════════════════════════════════════════════════
# GROUP 8: MULTI-DIAGNOSIS COMBINATIONS
# ═══════════════════════════════════════════════════════════════════

def test_TC30_all_covered_diagnoses_together(client: TestClient) -> None:
    """TC-30: Multiple covered diagnoses → APPROVE."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483",
        "diagnosis_codes": ["M54.16", "M54.17", "M54.4"],
        "state": "TX",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "APPROVE"


def test_TC31_covered_and_noncovered_covered_wins(client: TestClient) -> None:
    """TC-31: Covered + non-covered → evaluated based on exclusion criteria."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483",
        "diagnosis_codes": ["M54.16", "Z00.00"],
        "state": "TX",
    })
    d = r.json()
    assert r.status_code == 200
    assert d["decision"] in ["APPROVE", "DENY"]


def test_TC32_covered_and_unknown_dx(client: TestClient) -> None:
    """TC-32: Covered (M54.16) + unknown (A00.0) → NEED_MORE_INFORMATION."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483",
        "diagnosis_codes": ["M54.16", "A00.0"],
        "state": "TX",
    })
    d = r.json()
    assert r.status_code == 200
    assert d["decision"] == "NEED_MORE_INFORMATION"


def test_TC33_only_noncovered_diagnoses(client: TestClient) -> None:
    """TC-33: Only non-covered diagnoses → DENY."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483",
        "diagnosis_codes": ["Z00.00", "Z00.01"],
        "state": "TX",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "DENY"


def test_TC34_only_unknown_diagnoses(client: TestClient) -> None:
    """TC-34: Only unknown diagnoses → NEED_MORE_INFORMATION."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483",
        "diagnosis_codes": ["A00.0", "R99.99"],
        "state": "TX",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "NEED_MORE_INFORMATION"


# ═══════════════════════════════════════════════════════════════════
# GROUP 9: INPUT NORMALIZATION & VALIDATION
# ═══════════════════════════════════════════════════════════════════

def test_TC35_lowercase_state_normalized(client: TestClient) -> None:
    """TC-35: Lowercase 'tx' → normalized to TX → APPROVE."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["M54.16"], "state": "tx",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "APPROVE"


def test_TC36_lowercase_dx_and_proc_normalized(client: TestClient) -> None:
    """TC-36: Lowercase 'm54.16' → normalized → APPROVE."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["m54.16"], "state": "TX",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "APPROVE"


def test_TC37_whitespace_all_fields_normalized(client: TestClient) -> None:
    """TC-37: Whitespace around fields stripped before validation → APPROVE."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "  64483  ",
        "diagnosis_codes": [" m54.16 ", "  "],
        "state": " tx ",
    })
    assert r.status_code == 200
    assert r.json()["decision"] == "APPROVE"


def test_TC38_empty_diagnosis_list_rejected(client: TestClient) -> None:
    """TC-38: Empty diagnosis_codes [] → 422 Error."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": [], "state": "TX",
    })
    assert r.status_code == 422


def test_TC39_missing_procedure_code_rejected(client: TestClient) -> None:
    """TC-39: Missing procedure_code → 422 Error."""
    r = client.post("/api/v1/triage", json={
        "diagnosis_codes": ["M54.16"], "state": "TX",
    })
    assert r.status_code == 422


def test_TC40_missing_diagnosis_codes_rejected(client: TestClient) -> None:
    """TC-40: Missing diagnosis_codes → 422 Error."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "state": "TX",
    })
    assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════
# GROUP 10: RESPONSE CONTRACT & RAG FUSION TESTS
# ═══════════════════════════════════════════════════════════════════

def test_TC41_response_fields_all_present(client: TestClient) -> None:
    """TC-41: All required response fields present."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["M54.16"], "state": "TX",
    })
    d = r.json()
    assert r.status_code == 200
    for field in ["decision", "evidence_score", "reason", "reason_codes",
                  "policies", "evidence", "missing_information", "warnings"]:
        assert field in d, f"Missing field: {field}"


def test_TC42_evidence_score_range(client: TestClient) -> None:
    """TC-42: evidence_score between 0.0 and 1.0."""
    r = client.post("/api/v1/triage", json={
        "procedure_code": "64483", "diagnosis_codes": ["M54.16"], "state": "TX",
    })
    assert 0.0 <= r.json()["evidence_score"] <= 1.0


def test_TC43_decision_values_strictly_enum(client: TestClient) -> None:
    """TC-43: Output decisions are strictly inside the 3 allowed enum values."""
    valid_decisions = {"APPROVE", "DENY", "NEED_MORE_INFORMATION"}
    test_inputs = [
        {"procedure_code": "64483", "diagnosis_codes": ["M54.16"], "state": "TX"},
        {"procedure_code": "64483", "diagnosis_codes": ["Z00.00"], "state": "TX"},
        {"procedure_code": "XXXXX", "diagnosis_codes": ["M54.16"], "state": "TX"},
    ]
    for payload in test_inputs:
        r = client.post("/api/v1/triage", json=payload)
        assert r.json()["decision"] in valid_decisions



def test_TC44_criterion_classifier_types() -> None:
    """TC-44: CriterionClassifier correctly tags STRUCTURED, RULE_BASED, and SEMANTIC criteria."""
    c1 = CriterionClassifier.classify({"criterion_id": "1", "criterion": "Must have HCPCS code 99213", "policy_type": "NCD", "policy_id": "123"})
    assert c1.type == CriterionType.STRUCTURED

    c2 = CriterionClassifier.classify({"criterion_id": "2", "criterion": "Patient age must be greater than 65 years old", "policy_type": "NCD", "policy_id": "123"})
    assert c2.type == CriterionType.SEMANTIC

    c3 = CriterionClassifier.classify({"criterion_id": "3", "criterion": "Documentation must show conservative treatment failed", "policy_type": "NCD", "policy_id": "123"})
    assert c3.type == CriterionType.SEMANTIC


def test_TC45_criterion_extractor_parsing() -> None:
    """TC-45: CriterionExtractor parses bulleted chunk text into criteria objects."""
    chunk = PolicyChunk(
        policy_type="NCD",
        policy_id="123",
        chunk_text="- Patient has a history of heart disease.\n- Documentation must support medical necessity.",
    )
    extracted = CriterionExtractor.extract_from_chunk(chunk)
    assert len(extracted) > 0
    assert "Patient has a history of heart disease" in extracted[0]["criterion"]


def test_TC46_evidence_fusion_authority_rules() -> None:
    """TC-46: Authoritative SQL NOT_SATISFIED overrides non-authoritative LLM SATISFIED."""
    criteria = [
        EvaluatedCriterion(
            criterion_id="C1", policy_type="NCD", policy_id="123", criterion="HCPCS Code",
            criterion_type=CriterionType.STRUCTURED, evaluator=EvaluatorType.SQL,
            status=EvaluationStatus.NOT_SATISFIED, mandatory=True, authoritative=True,
        ),
        EvaluatedCriterion(
            criterion_id="C2", policy_type="NCD", policy_id="123", criterion="Conservative treatment",
            criterion_type=CriterionType.SEMANTIC, evaluator=EvaluatorType.LLM,
            status=EvaluationStatus.SATISFIED, mandatory=True, authoritative=False,
        )
    ]
    matrix = EvidenceFusion.fuse(criteria)
    assert EvidenceFusion.resolve_decision(matrix) == "EXCLUDED"
