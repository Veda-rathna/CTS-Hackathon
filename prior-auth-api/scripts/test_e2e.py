import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import engine
from app.dependencies.repositories import (
    get_policy_repository,
    get_article_repository,
    get_ncd_repository,
    get_policy_chunk_repository,
    get_multi_evaluator,
    get_embedding_service,
    get_llm_client,
)
from app.services.triage_service import TriageService
from app.schemas.triage import TriageRequest
from app.core.config import get_settings

def run_e2e():
    settings = get_settings()
    
    # Normally these are injected via FastAPI Depends
    # For a CLI test, we instantiate them manually with the real DB session
    with Session(engine) as session:
        # Repositories
        class MockSettings:
            use_mock_repositories = False
            
        repo_settings = MockSettings()
        
        from app.repositories.postgres.policy_repository import PostgresPolicyRepository
        from app.repositories.postgres.article_repository import PostgresArticleRepository
        from app.repositories.postgres.ncd_repository import PostgresNCDRepository
        from app.repositories.policy_chunk_repository import PolicyChunkRepository
        
        policy_repo = PostgresPolicyRepository()
        article_repo = PostgresArticleRepository()
        ncd_repo = PostgresNCDRepository()
        chunk_repo = PolicyChunkRepository(session)
        
        # Services
        from app.services.llm.client import LLMClient
        from app.services.rag.embedding_service import EmbeddingService
        from app.services.evaluation.multi_evaluator import MultiEvaluator
        from app.services.evaluation.structured_evaluator import StructuredEvaluator
        from app.services.evaluation.rule_evaluator import RuleEvaluator
        from app.services.evaluation.semantic_evaluator import SemanticEvaluator
        from app.repositories.postgres.lcd_repository import PostgresLCDRepository
        
        lcd_repo = PostgresLCDRepository()
        
        llm_client = LLMClient()
        embedding_service = EmbeddingService()
        
        structured_eval = StructuredEvaluator(article_repo, lcd_repo, ncd_repo)
        rule_eval = RuleEvaluator()
        semantic_eval = SemanticEvaluator(llm_client)
        
        evaluator = MultiEvaluator(structured_eval, rule_eval, semantic_eval)
        
        # Triage Service
        triage_service = TriageService(
            policy_repository=policy_repo,
            article_repository=article_repo,
            ncd_repository=ncd_repo,
            chunk_repository=chunk_repo,
            evaluator=evaluator,
            embedding_service=embedding_service
        )
        
        # Test Request
        # 64483 is a common epidural injection HCPCS code. 
        # We will use it with a diagnosis code we know might be there or not.
        request = TriageRequest(
            procedure_code="64483",
            diagnosis_codes=["M54.16"],
            state="TX",
            patient_age=70,
            clinical_notes="Patient completed 8 weeks of conservative physical therapy without improvement. Severe radicular pain present.",
            service_date="2026-08-14"
        )
        
        print("Running Triage...")
        response = triage_service.evaluate(request)
        
        print("\n=== TRIAGE RESPONSE ===")
        print(response.model_dump_json(indent=2))
        
        # Verify exact enum values are returned
        assert response.decision in ["APPROVE", "PEND", "REQUEST_MORE_INFORMATION"], f"Invalid decision state: {response.decision}"
        print(f"\nFinal decision was correctly mapped to: {response.decision}")

if __name__ == "__main__":
    run_e2e()
