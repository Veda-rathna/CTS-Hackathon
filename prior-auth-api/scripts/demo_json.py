import os
import sys
import asyncio
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["USE_MOCK_REPOSITORIES"] = "true"

# Try to detect LM Studio
import httpx
try:
    _probe = httpx.get("http://127.0.0.1:1234/v1/models", timeout=2.0)
    if _probe.status_code == 200 and _probe.json().get("data", []):
        os.environ["LLM_ENABLED"] = "true"
    else:
        os.environ["LLM_ENABLED"] = "false"
except Exception:
    os.environ["LLM_ENABLED"] = "false"

from app.schemas.triage import TriageRequest
from app.services.triage_service import TriageService

from app.repositories.mock.policy_repository import MockPolicyRepository
from app.repositories.mock.article_repository import MockArticleRepository
from app.repositories.mock.ncd_repository import MockNCDRepository
from app.repositories.mock.lcd_repository import MockLCDRepository
from app.repositories.mock.policy_chunk_repository import MockPolicyChunkRepository
from app.services.llm.client import LLMClient
from app.services.evaluation.structured_evaluator import StructuredEvaluator
from app.services.evaluation.rule_evaluator import RuleEvaluator
from app.services.agents.agent_orchestrator import AgentOrchestrator

from app.services.evaluation.multi_evaluator import MultiEvaluator
from app.services.evaluation.semantic_evaluator import SemanticEvaluator

async def main():
    req = TriageRequest(
        procedure_code="64483",
        diagnosis_codes=["M54.16"],
        state="TX",
        patient_age=55,
        clinical_notes="Patient presents with lumbar radiculopathy confirmed on MRI. Conservative therapy was tried for 8 weeks without relief."
    )
    
    import logging
    logging.getLogger("app").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)
    
    sys.stdout.reconfigure(encoding="utf-8")
    
    # Instantiate Mock Repositories
    policy_repo = MockPolicyRepository()
    article_repo = MockArticleRepository()
    ncd_repo = MockNCDRepository()
    lcd_repo = MockLCDRepository()
    chunk_repo = MockPolicyChunkRepository()

    class DummyEmbedding:
        def get_embedding(self, *a, **kw): return []
        def get_embeddings(self, *a, **kw): return []
        def embed_text(self, *a, **kw): return []

    llm_client = LLMClient()
    
    structured_evaluator = StructuredEvaluator(article_repo, lcd_repo, ncd_repo)
    rule_eval = RuleEvaluator()
    semantic_eval = SemanticEvaluator(llm_client)
    multi_eval = MultiEvaluator(structured_evaluator, rule_eval, semantic_eval)

    svc = TriageService(
        policy_repository=policy_repo,
        article_repository=article_repo,
        ncd_repository=ncd_repo,
        chunk_repository=chunk_repo,
        evaluator=multi_eval,
        embedding_service=DummyEmbedding()
    )
    res = svc.evaluate(req)
    
    # Print the beautifully structured JSON output returned by the API
    print(res.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())
