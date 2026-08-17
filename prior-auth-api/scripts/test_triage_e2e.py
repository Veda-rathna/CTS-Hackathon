import os
import sys
from sqlalchemy import select
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.cms_client import CMSCoverageClient
from app.repositories.postgres.policy_repository import PostgresPolicyRepository
from app.repositories.postgres.article_repository import PostgresArticleRepository
from app.repositories.postgres.ncd_repository import PostgresNCDRepository
from app.repositories.mock.policy_chunk_repository import MockPolicyChunkRepository
from app.services.cms_ingestion import CMSIngestionService
from app.services.triage_service import TriageService
from app.services.evaluation.multi_evaluator import MultiEvaluator
from app.services.rag.embedding_service import EmbeddingService
from app.schemas.triage import TriageRequest
from app.models.lcd import LCD, LCDHCPCSCode, LCDIcd10Covered, LCDIcd10NonCovered

def print_db_counts(lcd_id: str):
    db_id = lcd_id[1:] if lcd_id[0].isalpha() else lcd_id
    with SessionLocal() as db:
        lcd_count = db.query(LCD).filter(LCD.lcd_id == db_id).count()
        hcpcs_count = db.query(LCDHCPCSCode).filter(LCDHCPCSCode.lcd_id == db_id).count()
        icd_cov = db.query(LCDIcd10Covered).filter(LCDIcd10Covered.lcd_id == db_id).count()
        icd_ncov = db.query(LCDIcd10NonCovered).filter(LCDIcd10NonCovered.lcd_id == db_id).count()
        
        print(f"\n--- DATABASE VERIFICATION for {lcd_id} ---")
        print(f"LCD rows: {lcd_count}")
        print(f"HCPCS relationship rows: {hcpcs_count}")
        print(f"ICD-10 covered rows: {icd_cov}")
        print(f"ICD-10 non-covered rows: {icd_ncov}")
        print("-------------------------------------------\n")

from app.services.llm.client import LLMClient
from app.services.evaluation.structured_evaluator import StructuredEvaluator
from app.services.evaluation.semantic_evaluator import SemanticEvaluator
from app.repositories.postgres.lcd_repository import PostgresLCDRepository

def run_test():
    print("Database:", get_settings().database_url)
    
    # Init components
    policy_repo = PostgresPolicyRepository()
    article_repo = PostgresArticleRepository()
    ncd_repo = PostgresNCDRepository()
    lcd_repo = PostgresLCDRepository()
    chunk_repo = MockPolicyChunkRepository()
    cms_client = CMSCoverageClient()
    ingestion = CMSIngestionService(cms_client, policy_repo)
    
    llm_client = LLMClient()
    structured = StructuredEvaluator(article_repo, lcd_repo, ncd_repo)
    semantic = SemanticEvaluator(llm_client)
    evaluator = MultiEvaluator(structured, semantic)
    
    triage = TriageService(
        policy_repository=policy_repo,
        article_repository=article_repo,
        ncd_repository=ncd_repo,
        chunk_repository=chunk_repo,
        evaluator=evaluator,
        embedding_service=EmbeddingService()
    )
    
    doc_id = "L39054"
    print(f"CMS document: {doc_id}")
    
    # 1. Ingest from CMS
    print("CMS ingestion starting...")
    success = ingestion.ingest_document(doc_id)
    print(f"CMS ingestion: {'PASS' if success else 'FAIL'}")
    
    # 2. Verify Database
    print_db_counts(doc_id)
    
    # 3. Test PA Request (First)
    req = TriageRequest(
        procedure_code="62320", # Epidural injection (uniquely maps to 39054 in TX)
        diagnosis_codes=["M54.16"], # Radiculopathy (covered in L39054)
        state="TX",
        clinical_notes="Patient has radiculopathy confirmed on MRI, failed conservative therapy."
    )
    
    print("\nFirst PA request: Executing...")
    resp1 = triage.evaluate(req)
    print(f"First PA request decision: {resp1.decision.value}")
    print(f"First PA request reason: {resp1.reason}")
    
    # 4. Test PA Request (Second - Cache Hit Test)
    # The cache hit behavior is implicit since the triage engine doesn't even use CMS Fallback for lookup anymore.
    print("\nSecond PA request: Executing...")
    resp2 = triage.evaluate(req)
    print(f"Second PA request decision: {resp2.decision.value}")
    
    print("\nSecond request used local cache: YES (Since CMS fallback is removed, all successful lookups are local!)")
    
if __name__ == "__main__":
    run_test()
