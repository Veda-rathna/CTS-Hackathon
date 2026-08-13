"""Tests for article endpoints."""
from fastapi.testclient import TestClient


# ── Article ───────────────────────────────────────────────────────────────────

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
    """Article IDs should be normalised to uppercase."""
    response = client.get("/api/v1/articles/a12345")
    assert response.status_code == 200


# ── ICD-10 covered ────────────────────────────────────────────────────────────

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


# ── ICD-10 non-covered ────────────────────────────────────────────────────────

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


# ── HCPCS ─────────────────────────────────────────────────────────────────────

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
