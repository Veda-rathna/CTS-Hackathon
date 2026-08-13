"""Tests for policy search endpoint."""
from fastapi.testclient import TestClient


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
    # At least one result should have diagnosis_match True
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
    """A state not in any jurisdiction should produce jurisdiction_match=False."""
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
