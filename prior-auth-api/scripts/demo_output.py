"""
Demo script — Prior Authorization Triage Output
================================================
Runs the triage engine using MOCK repositories (no PostgreSQL, no LLM required).
Prints the full human-readable audit report for 4 sample scenarios.

Run from the prior-auth-api directory:
    python scripts/demo_output.py
"""
import os
import sys
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["USE_MOCK_REPOSITORIES"] = "true"
os.environ["DATABASE_URL"] = "postgresql+psycopg://test:test@localhost:5432/test"

# ── LLM Auto-Detection ──────────────────────────────────────────────────────────
# Try to reach LM Studio at the default address. If it's running and has a model
# loaded, enable the LLM so semantic criteria (QWEN) return SATISFIED/NOT_SATISFIED
# instead of UNKNOWN. If not reachable, fall back gracefully.
_LLM_AVAILABLE = False
try:
    _probe = httpx.get("http://127.0.0.1:1234/v1/models", timeout=2.0)
    if _probe.status_code == 200:
        _models = _probe.json().get("data", [])
        if _models:
            _LLM_AVAILABLE = True
except Exception:
    pass

if _LLM_AVAILABLE:
    os.environ["LLM_ENABLED"] = "true"
    _llm_mode = "LIVE — Qwen via LM Studio"
else:
    os.environ["LLM_ENABLED"] = "false"
    _llm_mode = "OFFLINE — LM Studio not detected (start it to enable semantic evaluation)"

sys.stdout.reconfigure(encoding="utf-8")

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
from app.services.evaluation.semantic_evaluator import SemanticEvaluator
from app.services.evaluation.multi_evaluator import MultiEvaluator
from app.core.config import get_settings

# ── Demo scenarios ─────────────────────────────────────────────────────────────

DEMOS = [
    {
        "name": "APPROVE — Covered dx + J5 state (TX) [LCD Path]",
        "procedure_code": "64483",
        "diagnosis_codes": ["M54.16"],
        "state": "TX",
        "patient_age": 55,
        "clinical_notes": "Patient presents with lumbar radiculopathy confirmed on MRI. Conservative therapy was tried for 8 weeks without relief.",
    },
    {
        "name": "PEND — Explicitly non-covered diagnosis [LCD Path]",
        "procedure_code": "64483",
        "diagnosis_codes": ["Z00.00"],
        "state": "TX",
        "patient_age": 40,
        "clinical_notes": "Routine general examination. No structural pathology identified.",
    },
    {
        "name": "APPROVE — Stem Cell Transplant covered by NCD 110.23 [NCD RAG Path]",
        "procedure_code": "38240",
        "diagnosis_codes": ["C91.10"],
        "state": "TX",
        "patient_age": 52,
        "clinical_notes": (
            "Patient diagnosed with chronic lymphocytic leukemia (CLL), relapsed after "
            "first-line therapy. Allogeneic hematopoietic stem cell transplantation "
            "recommended as curative intent option. Patient has good performance status "
            "and adequate cardiopulmonary function documented."
        ),
    },
    {
        "name": "APPROVE — AFP lab test covered by NCD 190.25 [NCD RAG Path]",
        "procedure_code": "82105",
        "diagnosis_codes": ["C22.0"],
        "state": "CA",
        "patient_age": 67,
        "clinical_notes": (
            "Hepatocellular carcinoma in high-risk patient with alcoholic cirrhosis. "
            "AFP serum test ordered to monitor response to treatment."
        ),
    },
    {
        # NCD N123 (160.7.1) — TENS for Acute Post-Operative Pain
        # Data source: CMS NCD 160.7.1 — TENS is covered for acute pain as a
        # transcutaneous surface neurostimulator when conservative therapy fails.
        # HCPCS 64550 is the applicable code.
        "name": "APPROVE — TENS covered by NCD 160.7.1 [NCD RAG + NCD Decision Path]",
        "procedure_code": "64550",
        "diagnosis_codes": ["G89.29"],  # Chronic pain, not elsewhere classified
        "state": "TX",
        "patient_age": 48,
        "clinical_notes": (
            "Patient presents with chronic pain syndrome following lumbar surgery. "
            "Conservative pharmacological therapy has been tried for over 6 weeks without "
            "satisfactory relief. TENS (transcutaneous electrical nerve stimulation) "
            "requested as adjunct pain management."
        ),
    },
    {
        "name": "REQUEST_MORE_INFORMATION — Outside jurisdiction (CA) [LCD Path]",
        "procedure_code": "64483",
        "diagnosis_codes": ["M54.17"],
        "state": "CA",
        "patient_age": 63,
        "clinical_notes": "Lumbosacral radiculopathy.",
    },
    {
        "name": "REQUEST_MORE_INFORMATION — No matching policy",
        "procedure_code": "99999",
        "diagnosis_codes": ["M54.16"],
        "state": "TX",
        "patient_age": 45,
        "clinical_notes": "Unknown procedure code.",
    },
]

# ── Setup ──────────────────────────────────────────────────────────────────────

def build_service():
    settings = get_settings()
    settings.use_mock_repositories = True
    settings.llm_enabled = False

    class _MockEmbed:
        def embed_text(self, text): return []

    article_repo = MockArticleRepository()
    lcd_repo = MockLCDRepository()
    ncd_repo = MockNCDRepository()

    return TriageService(
        policy_repository=MockPolicyRepository(),
        article_repository=article_repo,
        ncd_repository=ncd_repo,
        chunk_repository=MockPolicyChunkRepository(),
        evaluator=MultiEvaluator(
            StructuredEvaluator(article_repo, lcd_repo, ncd_repo),
            RuleEvaluator(),
            SemanticEvaluator(LLMClient()),
        ),
        embedding_service=_MockEmbed(),
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
    print(f"\n{SEP}")
    print("  PRIOR AUTHORIZATION TRIAGE & POLICY COMPANION")
    print("  Output Explainability Demo  (mock mode)")
    print(f"  LLM Mode       : {_llm_mode}")
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
