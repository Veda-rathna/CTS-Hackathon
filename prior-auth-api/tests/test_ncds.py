"""Tests for NCD endpoints."""
from fastapi.testclient import TestClient


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
