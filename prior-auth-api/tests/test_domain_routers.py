"""
Tests for domain lookup REST API routers (Articles, LCDs, NCDs, Policy Search, Health).
"""
from fastapi.testclient import TestClient


# ── Health Endpoints ──────────────────────────────────────────────────────────

def test_health_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "prior-authorization-api"
    assert "version" in data


def test_db_health_mock_mode(client: TestClient) -> None:
    response = client.get("/api/v1/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["mode"] == "mock"


# ── Article Endpoints ─────────────────────────────────────────────────────────

def test_get_article_found(client: TestClient) -> None:
    response = client.get("/api/v1/articles/A12345")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "A12345"
    assert data["title"] != ""
    assert data["status"] == "ACTIVE"


def test_get_article_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/articles/DOES_NOT_EXIST")
    assert response.status_code == 404
    data = response.json()
    assert "code" in data
    assert "message" in data


def test_get_article_case_insensitive(client: TestClient) -> None:
    response = client.get("/api/v1/articles/a12345")
    assert response.status_code == 200


def test_get_icd10_covered(client: TestClient) -> None:
    response = client.get("/api/v1/articles/A12345/icd10-covered")
    assert response.status_code == 200
    data = response.json()
    assert data["article_id"] == "A12345"
    assert len(data["codes"]) > 0
    codes = [c["code"] for c in data["codes"]]
    assert "M54.16" in codes


def test_get_icd10_covered_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/articles/DOES_NOT_EXIST/icd10-covered")
    assert response.status_code == 404


def test_get_icd10_noncovered(client: TestClient) -> None:
    response = client.get("/api/v1/articles/A12345/icd10-noncovered")
    assert response.status_code == 200
    data = response.json()
    assert data["article_id"] == "A12345"
    assert len(data["codes"]) > 0
    codes = [c["code"] for c in data["codes"]]
    assert "Z00.00" in codes


def test_get_icd10_noncovered_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/articles/DOES_NOT_EXIST/icd10-noncovered")
    assert response.status_code == 404


def test_get_hcpcs(client: TestClient) -> None:
    response = client.get("/api/v1/articles/A12345/hcpcs")
    assert response.status_code == 200
    data = response.json()
    assert data["article_id"] == "A12345"
    assert len(data["codes"]) > 0
    codes = [c["code"] for c in data["codes"]]
    assert "64483" in codes


def test_get_hcpcs_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/articles/DOES_NOT_EXIST/hcpcs")
    assert response.status_code == 404


# ── LCD Endpoints ─────────────────────────────────────────────────────────────

def test_get_lcd_found(client: TestClient) -> None:
    response = client.get("/api/v1/lcds/L39054")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "L39054"
    assert data["jurisdiction"]["id"] == "J5"
    assert data["contractor"]["id"] == "12301"
    assert len(data["hcpcs_codes"]) > 0
    assert len(data["icd10_covered"]) > 0
    assert len(data["icd10_noncovered"]) > 0


def test_get_lcd_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/lcds/DOES_NOT_EXIST")
    assert response.status_code == 404
    data = response.json()
    assert "code" in data


def test_get_lcd_case_insensitive(client: TestClient) -> None:
    response = client.get("/api/v1/lcds/l39054")
    assert response.status_code == 200


# ── NCD Endpoints ─────────────────────────────────────────────────────────────

def test_get_ncd_found(client: TestClient) -> None:
    response = client.get("/api/v1/ncds/N123")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "N123"
    assert data["title"] != ""


def test_get_ncd_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/ncds/DOES_NOT_EXIST")
    assert response.status_code == 404
    data = response.json()
    assert "code" in data


# ── Policy Search Endpoints ───────────────────────────────────────────────────

def test_policy_search_procedure_match(client: TestClient) -> None:
    response = client.get("/api/v1/policies/search?procedure_code=64483")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    match = data["matches"][0]
    assert match["procedure_match"] is True


def test_policy_search_diagnosis_match(client: TestClient) -> None:
    response = client.get(
        "/api/v1/policies/search?procedure_code=64483&diagnosis_code=M54.16"
    )
    assert response.status_code == 200
    data = response.json()
    assert any(m["diagnosis_match"] for m in data["matches"])


def test_policy_search_jurisdiction_match(client: TestClient) -> None:
    response = client.get(
        "/api/v1/policies/search?procedure_code=64483&state=TX"
    )
    assert response.status_code == 200
    data = response.json()
    assert any(m["jurisdiction_match"] for m in data["matches"])


def test_policy_search_no_match(client: TestClient) -> None:
    response = client.get("/api/v1/policies/search?procedure_code=XXXXX")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


def test_policy_search_outside_jurisdiction(client: TestClient) -> None:
    response = client.get(
        "/api/v1/policies/search?procedure_code=64483&state=ZZ"
    )
    assert response.status_code == 200
    data = response.json()
    assert all(not m["jurisdiction_match"] for m in data["matches"])


def test_policy_search_with_policy_type_filter(client: TestClient) -> None:
    response = client.get(
        "/api/v1/policies/search?procedure_code=64483&policy_type=LCD"
    )
    assert response.status_code == 200
    data = response.json()
    for match in data["matches"]:
        assert match["policy_type"] == "LCD"
