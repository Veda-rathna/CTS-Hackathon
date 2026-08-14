"""pytest configuration and shared fixtures.

All tests run entirely against mock repositories — no PostgreSQL connection required.
The USE_MOCK_REPOSITORIES environment variable is forced to True via monkeypatching.
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Force mock mode before importing the app
os.environ["USE_MOCK_REPOSITORIES"] = "true"
os.environ["DATABASE_URL"] = "postgresql+psycopg://test:test@localhost:5432/test"


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Return a TestClient using the FastAPI app in mock mode."""
    # Import here so env vars are already set
    from app.main import app
    from app.db.session import get_db
    
    # Override get_db to prevent database connection attempts
    app.dependency_overrides[get_db] = lambda: None
    
    return TestClient(app)
