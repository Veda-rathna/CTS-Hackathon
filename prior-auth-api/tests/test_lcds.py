"""Tests for LCD endpoints."""
from fastapi.testclient import TestClient


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
