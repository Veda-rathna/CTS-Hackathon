"""Tests for the triage endpoint — covers the exactly 3 allowed decision types."""
from fastapi.testclient import TestClient

def test_triage_approve(client: TestClient) -> None:
    """Primary happy-path scenario: procedure + covered diagnosis + state match."""
    response = client.post(
        "/api/v1/triage",
        json={
            "procedure_code": "64483",
            "diagnosis_codes": ["M54.16"],
            "state": "TX",
            "patient_age": 65,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "APPROVE"
    assert data["evidence_score"] > 0.0
    assert len(data["policies"]) > 0
    assert len(data["evidence"]) > 0
    assert "M54.16" in data["matched_codes"]["diagnosis"]


def test_triage_response_has_evidence(client: TestClient) -> None:
    """Every triage result must contain at least some evidence."""
    response = client.post(
        "/api/v1/triage",
        json={"procedure_code": "64483", "diagnosis_codes": ["M54.16"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["evidence"]) > 0
    for ev in data["evidence"]:
        assert ev["type"]
        assert ev["result"]


def test_triage_pend_explicit_exclusion(client: TestClient) -> None:
    """All submitted diagnoses are explicitly non-covered -> maps to PEND for review."""
    response = client.post(
        "/api/v1/triage",
        json={
            "procedure_code": "64483",
            "diagnosis_codes": ["Z00.00"],
            "state": "TX",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "PEND"
    assert "ARTICLE_EXCLUDES_PROCEDURE" in data["reason_codes"]


def test_triage_request_more_information(client: TestClient) -> None:
    """Diagnosis code not found in any code list -> Missing info -> REQUEST_MORE_INFORMATION."""
    response = client.post(
        "/api/v1/triage",
        json={
            "procedure_code": "64483",
            "diagnosis_codes": ["R99.99"],  # not in any list
            "state": "TX",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "REQUEST_MORE_INFORMATION"
    assert len(data["missing_information"]) > 0


def test_triage_policy_not_found(client: TestClient) -> None:
    """Procedure code not referenced by any policy -> maps to PEND."""
    response = client.post(
        "/api/v1/triage",
        json={
            "procedure_code": "XXXXX",
            "diagnosis_codes": ["M54.16"],
            "state": "TX",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "REQUEST_MORE_INFORMATION"
    assert "POLICY_NOT_FOUND" in data["reason_codes"]


def test_triage_outside_jurisdiction(client: TestClient) -> None:
    """Valid procedure but state not in any policy jurisdiction -> Missing valid jurisdiction."""
    response = client.post(
        "/api/v1/triage",
        json={
            "procedure_code": "64483",
            "diagnosis_codes": ["M54.16"],
            "state": "ZZ",  # not a real state in any jurisdiction
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "REQUEST_MORE_INFORMATION"


def test_triage_ncd_covered(client: TestClient) -> None:
    """Procedure mapped to an NCD with COVERED decision."""
    response = client.post(
        "/api/v1/triage",
        json={
            "procedure_code": "11111",
            "diagnosis_codes": ["M54.16"],
            "state": "TX",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "APPROVE"
    assert "NCD_CRITERIA_SATISFIED" in data["reason"]


def test_triage_ncd_excluded(client: TestClient) -> None:
    """Procedure mapped to an NCD with EXCLUDED decision."""
    response = client.post(
        "/api/v1/triage",
        json={
            "procedure_code": "22222",
            "diagnosis_codes": ["M54.16"],
            "state": "TX",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "PEND"
    assert "NCD_EXCLUDES_PROCEDURE" in data["reason"]


def test_triage_input_validation(client: TestClient) -> None:
    assert client.post("/api/v1/triage", json={"diagnosis_codes": ["M54.16"]}).status_code == 422
    assert client.post("/api/v1/triage", json={"procedure_code": "64483", "diagnosis_codes": []}).status_code == 422


def test_triage_state_normalized(client: TestClient) -> None:
    response = client.post(
        "/api/v1/triage",
        json={"procedure_code": "64483", "diagnosis_codes": ["M54.16"], "state": "tx"},
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "APPROVE"


def test_triage_strict_output_values(client: TestClient) -> None:
    response = client.post(
        "/api/v1/triage",
        json={"procedure_code": "64483", "diagnosis_codes": ["M54.16"], "state": "tx"},
    )
    data = response.json()
    assert data["decision"] not in [
        "DENY", "LIKELY_COVERED", "LIKELY_NOT_COVERED", "UNKNOWN", 
        "NURSE_REVIEW", "OUTSIDE_JURISDICTION", "POLICY_NOT_FOUND"
    ]
    assert data["decision"] in ["APPROVE", "PEND", "REQUEST_MORE_INFORMATION"]
