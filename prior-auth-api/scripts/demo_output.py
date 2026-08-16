"""
Demo script — Prior Authorization Triage Output (Live PostgreSQL Dataset)
========================================================================
Runs the triage engine using live NEON POSTGRESQL repositories and Bedrock / LM Studio LLM.
Prints the full human-readable audit report for 25 CMS policy test cases (5 for each core case type).

Run from the prior-auth-api directory:
    python scripts/demo_output.py
"""
import os
import sys
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["USE_MOCK_REPOSITORIES"] = "false"

# ── LLM Auto-Detection ──────────────────────────────────────────────────────────
from app.core.config import get_settings
_settings = get_settings()
_LLM_AVAILABLE = _settings.llm_enabled

if not _LLM_AVAILABLE:
    try:
        _probe = httpx.get("http://127.0.0.1:1234/v1/models", timeout=2.0)
        if _probe.status_code == 200 and _probe.json().get("data"):
            _LLM_AVAILABLE = True
    except Exception:
        pass

if _LLM_AVAILABLE:
    os.environ["LLM_ENABLED"] = "true"
    _llm_mode = f"LIVE — {_settings.llm_model} via {_settings.llm_provider.upper()}"
else:
    os.environ["LLM_ENABLED"] = "false"
    _llm_mode = "OFFLINE — LLM provider not detected"

import logging
logging.getLogger("app").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)

sys.stdout.reconfigure(encoding="utf-8")

from app.schemas.triage import TriageRequest
from app.services.triage_service import TriageService
from app.repositories.postgres.policy_repository import PostgresPolicyRepository
from app.repositories.postgres.article_repository import PostgresArticleRepository
from app.repositories.postgres.ncd_repository import PostgresNCDRepository
from app.repositories.postgres.lcd_repository import PostgresLCDRepository
from app.repositories.policy_chunk_repository import PolicyChunkRepository
from app.services.rag.embedding_service import EmbeddingService
from app.services.llm.client import LLMClient
from app.services.evaluation.structured_evaluator import StructuredEvaluator
from app.services.evaluation.semantic_evaluator import SemanticEvaluator
from app.services.evaluation.multi_evaluator import MultiEvaluator

# ── Demo scenarios (6 Real CMS Dataset Test Cases) ──────────────────────────────

DEMOS = [
    {
        "name": "APPROVE — Covered Knee Osteoarthritis Hyaluronan Injection (PA-REAL-001)",
        "procedure_code": "20610",
        "diagnosis_codes": ["M17.11"],
        "state": "TX",
        "patient_age": 51,
        "clinical_notes": "Intraarticular knee injection of hyaluronan for unilateral primary osteoarthritis right knee.",
    },
    {
        "name": "APPROVE — Covered Lumbar Radiculopathy Epidural Steroid Injection (PA-REAL-002)",
        "procedure_code": "64483",
        "diagnosis_codes": ["M54.16"],
        "state": "TX",
        "patient_age": 47,
        "clinical_notes": "Epidural injection, lumbar or sacral. Patient presents with lumbar radiculopathy confirmed on MRI. Conservative physical therapy was tried for 8 weeks without adequate relief.",
    },
    {
        "name": "PEND/DENY — Mandatory Requirement Failed (Non-Covered Joint Pain for Trigger Point Injection) (PA-REAL-003)",
        "procedure_code": "20552",
        "diagnosis_codes": ["M25.50"],
        "state": "TX",
        "patient_age": 61,
        "clinical_notes": "Injection(s), single or multiple trigger point(s), 1 or 2 muscle(s) for pain in unspecified joint.",
    },
    {
        "name": "NEED_MORE_INFORMATION — Missing Required Clinical Documentation (Unlisted Headache for Epidural) (PA-REAL-004)",
        "procedure_code": "64483",
        "diagnosis_codes": ["R51.9"],
        "state": "TX",
        "patient_age": 67,
        "clinical_notes": "Epidural injection, lumbar or sacral for unspecified headache.",
    },
    {
        "name": "PEND/DENY — Explicit Policy Exclusion under NCD 373 (PA-REAL-005)",
        "procedure_code": "20552",
        "diagnosis_codes": ["M25.50"],
        "state": "TX",
        "patient_age": 57,
        "clinical_notes": "Trigger point injection for acupuncture-related indications.",
    },
    {
        "name": "NEED_MORE_INFORMATION — Unknown/Incomplete Diagnosis (Administrative Exam Code for Knee Injection) (PA-REAL-006)",
        "procedure_code": "20610",
        "diagnosis_codes": ["Z00.00"],
        "state": "TX",
        "patient_age": 44,
        "clinical_notes": "Intraarticular knee injection of hyaluronan for general medical examination.",
    },
    {
        "name": "APPROVE — Intravenous Immune Globulin Covered under National Policy NCD 158 (PA-REAL-007)",
        "procedure_code": "J1561",
        "diagnosis_codes": ["L10.0"],
        "state": "TX",
        "patient_age": 58,
        "clinical_notes": "Intravenous immune globulin infusion for biopsy-proven pemphigus vulgaris refractory to standard systemic corticosteroid therapy.",
    },
]

# ── Setup ──────────────────────────────────────────────────────────────────────

def build_service():
    settings = get_settings()
    settings.use_mock_repositories = False

    from app.db.session import SessionLocal

    db = SessionLocal()
    article_repo = PostgresArticleRepository()
    lcd_repo = PostgresLCDRepository()
    ncd_repo = PostgresNCDRepository()
    policy_repo = PostgresPolicyRepository()
    chunk_repo = PolicyChunkRepository(db)
    embedding_service = EmbeddingService()

    llm_client = LLMClient()
    llm_client.enabled = _LLM_AVAILABLE

    return TriageService(
        policy_repository=policy_repo,
        article_repository=article_repo,
        ncd_repository=ncd_repo,
        lcd_repository=lcd_repo,
        chunk_repository=chunk_repo,
        evaluator=MultiEvaluator(
            StructuredEvaluator(article_repo, lcd_repo, ncd_repo),
            SemanticEvaluator(llm_client),
        ),
        embedding_service=embedding_service,
    )

# ── Report printer ─────────────────────────────────────────────────────────────

SEP  = "=" * 65
THIN = "-" * 65

def print_report(name, req, resp):
    print(f"\n\n{SEP}\n  {name}\n{SEP}")

    # REQUEST
    print(f"\nREQUEST\n{THIN}")
    print(f"  Procedure Code : {req.procedure_code}")
    print(f"  Diagnosis      : {', '.join(req.diagnosis_codes)}")
    print(f"  State          : {req.state or '(not provided)'}")
    print(f"  Patient Age    : {req.patient_age or '(not provided)'}")
    if getattr(req, "clinical_notes", None):
        print(f"  Clinical Notes : {req.clinical_notes}")

    # POLICY IDENTIFICATION
    print(f"\nPOLICY IDENTIFICATION\n{THIN}")
    path = resp.policy_path or {}
    ncd_info = path.get("ncd") or {}
    lcd_info = path.get("lcd") or {}
    art_info = path.get("article") or {}
    jur_info = path.get("jurisdiction") or {}
    ncd_id = ncd_info.get("policy_id", "") or ""
    lcd_id = lcd_info.get("policy_id", "") or ""
    art_id = art_info.get("policy_id", "") or ""
    print(f"  NCD            : {ncd_id or ncd_info.get('result','NOT_ADDRESSED')}")
    print(f"  Jurisdiction   : {req.state or '?'} → {jur_info.get('result','NOT_ADDRESSED')}")
    if lcd_id:
        title = next((p.title for p in resp.policies if p.policy_type == "LCD" and p.policy_id == lcd_id), "")
        print(f"  LCD            : {lcd_id}  {title}")
    if art_id:
        print(f"  Article        : {art_id}")

    # POLICY EVIDENCE
    print(f"\nPOLICY EVIDENCE\n{THIN}")
    if resp.rag_evidence:
        for ev in resp.rag_evidence:
            print(f"  Source     : {ev.policy_type} {ev.policy_id}")
            print(f"  Section    : {ev.section or 'Coverage Indications'}")
            print(f"  Text       : {ev.text.strip()[:200]}")
            score = ev.similarity_score
            print(f"  Similarity : {f'{score:.4f}' if score is not None else 'N/A'}")
    else:
        print("  RAG : NOT USED — no semantic criterion identified")

    # CODE MATCHING
    hcpcs_ev = [e for e in resp.evidence if getattr(e, "type", None) == "HCPCS"]
    icd_ev   = [e for e in resp.evidence if getattr(e, "type", None) == "ICD10"]
    if hcpcs_ev or icd_ev:
        print(f"\nCODE MATCHING\n{THIN}")
        for ev in hcpcs_ev:
            src = f"NCD {ev.identifier}" if ev.identifier == ncd_id else (f"LCD {ev.identifier}" if ev.identifier == lcd_id else f"Article {ev.identifier}")
            print(f"  HCPCS {ev.code} → {src} → {ev.result}")
        for ev in icd_ev:
            src = f"NCD {ev.identifier}" if ev.identifier == ncd_id else (f"LCD {ev.identifier}" if ev.identifier == lcd_id else f"Article {ev.identifier}")
            print(f"  ICD-10 {ev.code} → {src} → {ev.result}")

    # POLICY CRITERIA
    if resp.criteria:
        print(f"\nPOLICY CRITERIA\n{THIN}")
        for i, c in enumerate(resp.criteria, 1):
            ev_label = "QWEN" if c.evaluator.value == "LLM" else c.evaluator.value
            print(f"\n  C{i}  [{ev_label}]  {c.criterion_id}")
            print(f"  Requirement  : {c.criterion[:110].replace(chr(10), ' ')}{'...' if len(c.criterion) > 110 else ''}")
            print(f"  Type         : {c.criterion_type.value}")
            print(f"  Result       : {c.status.value}")
            if c.policy_evidence:
                print(f"  Policy Ev.   : {'; '.join(c.policy_evidence[:2])}")
            if c.patient_evidence:
                print(f"  Patient Ev.  : {'; '.join(c.patient_evidence)}")
            explanation = c.explanation or f"Evaluated as {c.status.value} by {ev_label}."
            print(f"  Explanation  : {explanation}")

    # EVIDENCE FUSION
    print(f"\nEVIDENCE FUSION\n{THIN}")
    sat  = sum(1 for c in resp.criteria if c.status.value == "SATISFIED")
    nsat = sum(1 for c in resp.criteria if c.status.value == "NOT_SATISFIED")
    unk  = sum(1 for c in resp.criteria if c.status.value == "UNKNOWN")
    print(f"  Criteria SATISFIED     : {sat}")
    print(f"  Criteria NOT_SATISFIED : {nsat}")
    print(f"  Criteria UNKNOWN       : {unk}")
    print(f"  Evidence Fusion Result : {resp.evidence_fusion_result or 'NOT_ADDRESSED'}")

    # FINAL DECISION
    decision = resp.decision.value
    icons = {"APPROVE": "✅", "PEND": "⚠️", "REQUEST_MORE_INFORMATION": "ℹ️"}
    print(f"\nFINAL DECISION\n{THIN}")
    print(f"  {icons.get(decision, '?')}  Decision    : {decision}")
    print(f"  Reason      : {resp.reason}")
    print(f"  Reason Codes: {', '.join(resp.reason_codes)}")
    print(f"\n  Decision Basis:")
    for line in (resp.decision_basis or "").split("\n"):
        print(f"    {line}")


def main():
    service = build_service()

    repo_mode = "LIVE NEON POSTGRESQL"
    print(f"\n{SEP}")
    print("  PRIOR AUTHORIZATION TRIAGE & POLICY COMPANION")
    print(f"  Output Explainability Demo  ({repo_mode})")
    print(f"  LLM Mode       : {_llm_mode}")
    print(f"  Repository Mode: {repo_mode}")
    print(SEP)

    for demo in DEMOS:
        name = demo["name"]
        req_data = {k: v for k, v in demo.items() if k != "name"}
        req = TriageRequest(**req_data)
        try:
            resp = service.evaluate(req)
            print_report(name, req, resp)
        except Exception as e:
            print(f"\n❌  ERROR — {name}: {e}")
            import traceback; traceback.print_exc()

    print(f"\n{SEP}\n  END OF DEMO\n{SEP}\n")


if __name__ == "__main__":
    main()

