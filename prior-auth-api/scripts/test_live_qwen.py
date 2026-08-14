import os
import sys
import json
import logging
from sqlalchemy.orm import Session
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine
from app.services.llm.client import LLMClient
from app.schemas.triage import TriageRequest
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)

def test_live_qwen():
    settings = get_settings()
    settings.llm_enabled = True
    
    print(f"Connecting to LM Studio at {settings.llm_base_url} using model {settings.llm_model}...")
    
    client = LLMClient()
    
    criterion = "Documentation must demonstrate failure of conservative treatment."
    
    # 1. SATISFIED
    print("\n--- Test 1: SATISFIED ---")
    res1 = client.evaluate_criterion(
        criterion_text=criterion,
        clinical_notes="Patient completed physical therapy for seven months with persistent symptoms despite treatment."
    )
    print(f"Result: {res1.status}")
    print(f"Evidence: {res1.patient_evidence}")

    # 2. UNKNOWN
    print("\n--- Test 2: UNKNOWN ---")
    res2 = client.evaluate_criterion(
        criterion_text=criterion,
        clinical_notes="Patient has severe pain."
    )
    print(f"Result: {res2.status}")
    print(f"Evidence: {res2.patient_evidence}")

    # 3. NOT_SATISFIED
    print("\n--- Test 3: NOT_SATISFIED ---")
    res3 = client.evaluate_criterion(
        criterion_text=criterion,
        clinical_notes="Patient has not attempted conservative treatment."
    )
    print(f"Result: {res3.status}")
    print(f"Evidence: {res3.patient_evidence}")


def test_live_e2e():
    print("\n--- Test 4: Live E2E Triage Request ---")
    with Session(engine) as session:
        # Repositories
        from app.repositories.postgres.policy_repository import PostgresPolicyRepository
        from app.repositories.postgres.article_repository import PostgresArticleRepository
        from app.repositories.postgres.ncd_repository import PostgresNCDRepository
        from app.repositories.postgres.lcd_repository import PostgresLCDRepository
        from app.repositories.policy_chunk_repository import PolicyChunkRepository
        
        policy_repo = PostgresPolicyRepository()
        article_repo = PostgresArticleRepository()
        ncd_repo = PostgresNCDRepository()
        lcd_repo = PostgresLCDRepository()
        chunk_repo = PolicyChunkRepository(session)
        
        # Services
        from app.services.llm.client import LLMClient
        from app.services.rag.embedding_service import EmbeddingService
        from app.services.evaluation.multi_evaluator import MultiEvaluator
        from app.services.evaluation.structured_evaluator import StructuredEvaluator
        from app.services.evaluation.rule_evaluator import RuleEvaluator
        from app.services.evaluation.semantic_evaluator import SemanticEvaluator
        from app.services.triage_service import TriageService
        
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
        
        # We must use a request that will trigger the SEMANTIC evaluator.
        # This requires matching a policy that has a semantic criterion.
        request = TriageRequest(
            procedure_code="64483",
            diagnosis_codes=["M54.16"],
            state="TX",
            patient_age=70,
            clinical_notes="Patient completed 8 weeks of conservative physical therapy without improvement. Severe radicular pain present.",
            service_date="2026-08-14"
        )
        
        response = triage_service.evaluate(request)
        
        print("\n=== FINAL API RESPONSE ===")
        print(response.model_dump_json(indent=2))


if __name__ == "__main__":
    test_live_qwen()
    try:
        test_live_e2e()
    except Exception as e:
        print(f"E2E Test Failed: {e}")
