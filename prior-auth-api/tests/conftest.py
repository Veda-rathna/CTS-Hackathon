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


import pytest
from fastapi.testclient import TestClient

from app.services.agents.agent_orchestrator import AgentOrchestrator
from app.services.agents.schemas import AgentOrchestrationResult, CriticVerdict, SemanticResult

_REAL_AGENT_ORCHESTRATOR_RUN = AgentOrchestrator.run


@pytest.fixture(autouse=True)
def mock_semantic_evaluator_for_engine(request):
    """Mock semantic evaluator for structural unit tests to focus on SQL/rules."""
    if "test_agentic_semantic" not in request.node.nodeid:
        def mock_run(self, criterion, req):
            return AgentOrchestrationResult(
                criterion_id=criterion.criterion_id,
                criterion=criterion.criterion,
                policy_id=criterion.policy_id,
                policy_type=criterion.policy_type,
                qwen_result=SemanticResult.SATISFIED,
                critic_verdict=CriticVerdict.VALIDATED,
                final_result=SemanticResult.SATISFIED,
                explanation="Mocked as SATISFIED for structural unit tests",
                confidence=1.0,
                latency_ms=0,
            )

        AgentOrchestrator.run = mock_run
        try:
            yield
        finally:
            AgentOrchestrator.run = _REAL_AGENT_ORCHESTRATOR_RUN
    else:
        AgentOrchestrator.run = _REAL_AGENT_ORCHESTRATOR_RUN
        yield





@pytest.fixture(scope="session")
def client() -> TestClient:
    """Return a TestClient using the FastAPI app in mock mode."""
    from app.main import app
    from app.db.session import get_db
    
    # Override get_db to prevent database connection attempts
    app.dependency_overrides[get_db] = lambda: None
    
    return TestClient(app)



