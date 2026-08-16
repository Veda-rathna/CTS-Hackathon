"""
Real Neon PostgreSQL Database PA Evaluation Demo & Test Script
================================================================
Runs Prior Authorization evaluations against the LIVE Neon PostgreSQL Database
and Amazon Bedrock (qwen.qwen3-next-80b-a3b).

Run:
    python scripts/test_real_neon_db.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.repositories.postgres.policy_repository import PostgresPolicyRepository
from app.repositories.postgres.article_repository import PostgresArticleRepository
from app.repositories.postgres.ncd_repository import PostgresNCDRepository
from app.repositories.postgres.lcd_repository import PostgresLCDRepository
from app.repositories.policy_chunk_repository import PolicyChunkRepository
from app.services.rag.embedding_service import EmbeddingService
from app.services.evaluation.multi_evaluator import MultiEvaluator
from app.services.evaluation.structured_evaluator import StructuredEvaluator
from app.services.evaluation.rule_evaluator import RuleEvaluator
from app.services.evaluation.semantic_evaluator import SemanticEvaluator
from app.services.llm.client import LLMClient
from app.services.triage_service import TriageService
from app.schemas.triage import TriageRequest


def build_real_triage_service(db) -> TriageService:
    policy_repo = PostgresPolicyRepository()
    article_repo = PostgresArticleRepository()
    lcd_repo = PostgresLCDRepository()
    ncd_repo = PostgresNCDRepository()
    chunk_repo = PolicyChunkRepository(db)
    llm_client = LLMClient()
    embedding_service = EmbeddingService()

    return TriageService(
        policy_repository=policy_repo,
        article_repository=article_repo,
        ncd_repository=ncd_repo,
        chunk_repository=chunk_repo,
        evaluator=MultiEvaluator(
            StructuredEvaluator(article_repo, lcd_repo, ncd_repo),
            RuleEvaluator(),
            SemanticEvaluator(llm_client),
        ),
        embedding_service=embedding_service,
    )


def main():
    settings = get_settings()

    print("=" * 75)
    print("  PRIOR AUTHORIZATION TRIAGE & POLICY COMPANION")
    print("  Live Neon PostgreSQL Database & Bedrock LLM Evaluation")
    print("=" * 75)
    print(f"  Repository Mode : LIVE NEON POSTGRESQL (use_mock_repositories={settings.use_mock_repositories})")
    print(f"  Database Host   : {settings.database_url_normalized.split('@')[-1].split('/')[0]}")
    print(f"  LLM Provider    : {settings.llm_provider.upper()}")
    print(f"  LLM Model       : {settings.llm_model}")
    print("=" * 75 + "\n")

    db = SessionLocal()
    triage_service = build_real_triage_service(db)

    # Test cases built directly from real Neon PostgreSQL database records
    test_cases = [
        {
            "title": "TEST CASE 1: Respiratory Pathogen Panel (HCPCS 0202U) + Cystic Fibrosis (E84.0) [Covered]",
            "request": TriageRequest(
                procedure_code="0202U",
                diagnosis_codes=["E84.0"],
                state=None,
                patient_age=34,
                clinical_notes="Patient with cystic fibrosis presenting with acute pulmonary exacerbation and dyspnea.",
            ),
        },
        {
            "title": "TEST CASE 2: Trigger Point Injection (HCPCS 20552) + Unspecified Joint Pain (M25.50) [Non-Covered Dx]",
            "request": TriageRequest(
                procedure_code="20552",
                diagnosis_codes=["M25.50"],
                state=None,
                patient_age=45,
                clinical_notes="Routine consultation for general unspecified joint pain without muscle trigger points.",
            ),
        },
        {
            "title": "TEST CASE 3: OnabotulinumtoxinA (HCPCS J0585) + Cervical Dystonia (G24.3) [Semantic Evaluation Path]",
            "request": TriageRequest(
                procedure_code="J0585",
                diagnosis_codes=["G24.3"],
                state=None,
                patient_age=52,
                clinical_notes=(
                    "Patient has severe chronic cervical dystonia (G24.3) confirmed by neurologist. "
                    "Conservative physical therapy and oral muscle relaxants were tried for 12 weeks with zero improvement."
                ),
            ),
        },
    ]

    for idx, case in enumerate(test_cases, 1):
        print("=" * 75)
        print(f"  {case['title']}")
        print("=" * 75)

        req = case["request"]
        print("PA REQUEST DETAILS:")
        print(f"  • Procedure Code : {req.procedure_code}")
        print(f"  • Diagnosis Code : {', '.join(req.diagnosis_codes)}")
        print(f"  • Patient Age    : {req.patient_age}")
        print(f"  • Clinical Notes : {req.clinical_notes}\n")

        res = triage_service.evaluate(req)

        print("MATCHED POLICIES:")
        if res.policies:
            for p in res.policies:
                print(f"  • Policy ID   : {p.policy_id} ({p.policy_type})")
                print(f"    Title       : {p.title or 'N/A'}")
                print(f"    Article ID  : {p.article_id or 'N/A'}")
        else:
            print("  No applicable policies matched.")

        print("\nFINAL TRIAGE DECISION:")
        print(f"  • Decision             : {res.decision.value}")
        print(f"  • Evidence Score       : {res.evidence_score}")
        print(f"  • Reason               : {res.reason}")
        print(f"  • Reason Codes         : {', '.join(res.reason_codes)}")
        if res.evidence_fusion_result:
            print(f"  • Evidence Fusion      : {res.evidence_fusion_result}")

        if res.criteria:
            print("\nEVALUATED POLICY CRITERIA:")
            for c in res.criteria:
                print(f"  • [{c.evaluator.value}] {c.criterion_id} -> {c.status.value}")
                print(f"    Requirement : {c.criterion[:80]}...")
                if c.patient_evidence:
                    print(f"    Evidence    : {', '.join(c.patient_evidence)[:80]}...")
        else:
            print("\n  No specific criteria evaluated.")

    print("=" * 75)
    print("  ALL NEON POSTGRESQL DATABASE EVALUATIONS COMPLETED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    main()
