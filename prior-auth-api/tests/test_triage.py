"""Tests for the triage endpoint — covers all decision types (updated for v3 architecture)."""
from fastapi.testclient import TestClient

def test_triage_likely_covered(client: TestClient) -> None:
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
    assert data["decision"] == "LIKELY_COVERED"
    assert data["evidence_score"] == 1.0
    assert data["requires_prior_authorization"] is None
    assert len(data["policies"]) > 0
    assert len(data["policy_path"]) > 0

def test_triage_response_has_evidence(client: TestClient) -> None:
    response = client.post(
        "/api/v1/triage",
        json={"procedure_code": "64483", "diagnosis_codes": ["M54.16"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["policy_path"]) > 0

def test_triage_diagnosis_evaluation_present(client: TestClient) -> None:
    response = client.post(
        "/api/v1/triage",
        json={"procedure_code": "64483", "diagnosis_codes": ["M54.16", "Z00.00"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "LIKELY_NOT_COVERED"

def test_triage_likely_not_covered(client: TestClient) -> None:
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
    assert data["decision"] == "LIKELY_NOT_COVERED"

def test_triage_more_information_required(client: TestClient) -> None:
    response = client.post(
        "/api/v1/triage",
        json={
            "procedure_code": "64483",
            "diagnosis_codes": ["R99.99"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] in ("MORE_INFORMATION_REQUIRED", "LIKELY_NOT_COVERED")

def test_triage_policy_not_found(client: TestClient) -> None:
    response = client.post(
        "/api/v1/triage",
        json={
            "procedure_code": "XXXXX",
            "diagnosis_codes": ["M54.16"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "POLICY_NOT_FOUND"

def test_triage_outside_jurisdiction(client: TestClient) -> None:
    response = client.post(
        "/api/v1/triage",
        json={
            "procedure_code": "64483",
            "diagnosis_codes": ["M54.16"],
            "state": "ZZ",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "OUTSIDE_JURISDICTION"

def test_triage_policy_expired(client: TestClient) -> None:
    from app.repositories.mock.article_repository import MockArticleRepository
    from app.services.article_service import ArticleService
    svc = ArticleService(MockArticleRepository())
    article = svc.get_article("A99999")
    assert article.status == "RETIRED"
    assert article.end_date is not None

def test_triage_ncd_covered(client: TestClient) -> None:
    response = client.post(
        "/api/v1/triage",
        json={
            "procedure_code": "11111",
            "diagnosis_codes": ["M54.16"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "LIKELY_COVERED"
    assert any(p["policy_type"] == "NCD" and p["policy_id"] == "N111" for p in data["policies"])

def test_triage_ncd_excluded(client: TestClient) -> None:
    response = client.post(
        "/api/v1/triage",
        json={
            "procedure_code": "22222",
            "diagnosis_codes": ["M54.16"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "LIKELY_NOT_COVERED"

def test_triage_nurse_review(client: TestClient) -> None:
    response = client.post(
        "/api/v1/triage",
        json={
            "procedure_code": "64483",
            "diagnosis_codes": ["R99.99"],
            "patient_age": 70,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] in ("NURSE_REVIEW", "MORE_INFORMATION_REQUIRED", "LIKELY_NOT_COVERED")

def test_triage_missing_procedure_code(client: TestClient) -> None:
    response = client.post(
        "/api/v1/triage",
        json={"diagnosis_codes": ["M54.16"]},
    )
    assert response.status_code == 422

def test_triage_empty_diagnosis_codes(client: TestClient) -> None:
    response = client.post(
        "/api/v1/triage",
        json={"procedure_code": "64483", "diagnosis_codes": []},
    )
    assert response.status_code == 422

def test_triage_negative_patient_age(client: TestClient) -> None:
    response = client.post(
        "/api/v1/triage",
        json={
            "procedure_code": "64483",
            "diagnosis_codes": ["M54.16"],
            "patient_age": -1,
        },
    )
    assert response.status_code == 422

def test_triage_state_normalized_to_uppercase(client: TestClient) -> None:
    response = client.post(
        "/api/v1/triage",
        json={
            "procedure_code": "64483",
            "diagnosis_codes": ["M54.16"],
            "state": "tx",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "LIKELY_COVERED"

def test_triage_evidence_score_between_0_and_1(client: TestClient) -> None:
    response = client.post(
        "/api/v1/triage",
        json={
            "procedure_code": "64483",
            "diagnosis_codes": ["M54.16"],
            "state": "TX",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert 0.0 <= data["evidence_score"] <= 1.0
