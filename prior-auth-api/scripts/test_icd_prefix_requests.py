import os
import sys
import json
import csv
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine
from app.schemas.triage import TriageRequest
from app.services.triage_service import TriageService
from app.repositories.postgres.policy_repository import PostgresPolicyRepository
from app.repositories.postgres.article_repository import PostgresArticleRepository
from app.repositories.postgres.ncd_repository import PostgresNCDRepository
from app.repositories.postgres.lcd_repository import PostgresLCDRepository
from app.repositories.policy_chunk_repository import PolicyChunkRepository
from app.services.llm.client import LLMClient
from app.services.rag.embedding_service import EmbeddingService
from app.services.evaluation.multi_evaluator import MultiEvaluator
from app.services.evaluation.structured_evaluator import StructuredEvaluator
from app.services.evaluation.rule_evaluator import RuleEvaluator
from app.services.evaluation.semantic_evaluator import SemanticEvaluator
from app.core.config import get_settings

# Ensure output encoding is utf-8 for Windows consoles
sys.stdout.reconfigure(encoding='utf-8')

# ============================================================
# TEST REQUESTS
# ============================================================

TEST_REQUESTS = [

    # J PREFIX
    {
        "name": "Primary osteoarthritis, left elbow",
        "procedure_code": "G0151",
        "diagnosis_codes": ["M19.022"],
        "state": "IA",
        "patient_age": 72,
        "clinical_notes": "Patient presents with documented condition corresponding to the submitted diagnosis."
    }
    
]





def run_tests():
    settings = get_settings()
    settings.use_mock_repositories = False # Force PostgreSQL
    settings.llm_enabled = True # Force Qwen
    
    results = []
    
    with Session(engine) as session:
        # Initialize the production pipeline
        policy_repo = PostgresPolicyRepository()
        article_repo = PostgresArticleRepository()
        ncd_repo = PostgresNCDRepository()
        lcd_repo = PostgresLCDRepository()
        
        llm_client = LLMClient()
        embedding_service = EmbeddingService()
        
        structured_eval = StructuredEvaluator(article_repo, lcd_repo, ncd_repo)
        rule_eval = RuleEvaluator()
        semantic_eval = SemanticEvaluator(llm_client)
        
        evaluator = MultiEvaluator(structured_eval, rule_eval, semantic_eval)
        
        for i, req_data in enumerate(TEST_REQUESTS, 1):
            print(f"\n{'='*60}\nTEST #{i}\n{'='*60}\n")
            
            # Print exact request
            print("REQUEST INPUT\n-------------")
            print(json.dumps(req_data, indent=4))
            print()
            
            req_data_copy = dict(req_data)
            test_name = req_data.pop("name")
            request = TriageRequest(**req_data)
            
            chunk_repo = PolicyChunkRepository(session)
            
            triage_service = TriageService(
                policy_repository=policy_repo,
                article_repository=article_repo,
                ncd_repository=ncd_repo,
                chunk_repository=chunk_repo,
                evaluator=evaluator,
                embedding_service=embedding_service
            )
            
            # Determine Prefix
            icd10_code = request.diagnosis_codes[0]
            icd10_prefix = icd10_code[0].upper()
            
            # Execute Pipeline
            try:
                response = triage_service.evaluate(request)
                error_msg = ""
            except Exception as e:
                response = None
                error_msg = str(e)
                print(f"❌ ERROR: {e}")
            
            # Parse response for output
            ncd_id = ""
            ncd_result = "NOT_ADDRESSED"
            rag_used = "NO"
            lcd_id = ""
            lcd_result = "NOT_ADDRESSED"
            article_id = ""
            article_result = "NOT_ADDRESSED"
            llm_used = "NO"
            final_decision = ""
            reason_codes = []
            
            structured_json = {
                "request": req_data_copy,
                "error": error_msg
            }
            
            if response:
                try:
                    path = response.policy_path.model_dump()
                except AttributeError:
                    path = response.policy_path
                
                if not path:
                    path = {}
                elif not isinstance(path, dict):
                    path = path.__dict__
                    
                ncd_info = path.get("ncd", {})
                if not isinstance(ncd_info, dict): ncd_info = ncd_info.__dict__
                ncd_id = ncd_info.get("policy_id", "")
                ncd_result = ncd_info.get("result", "NOT_ADDRESSED")
                
                lcd_info = path.get("lcd", {})
                if not isinstance(lcd_info, dict): lcd_info = lcd_info.__dict__
                lcd_id = lcd_info.get("policy_id", "")
                lcd_result = lcd_info.get("result", "NOT_ADDRESSED")
                
                art_info = path.get("article", {})
                if not isinstance(art_info, dict): art_info = art_info.__dict__
                article_id = art_info.get("policy_id", "")
                article_result = art_info.get("result", "NOT_ADDRESSED")
                
                jur_info = path.get("jurisdiction", {})
                if not isinstance(jur_info, dict): jur_info = jur_info.__dict__
                jurisdiction_result = jur_info.get("result", "NOT_ADDRESSED")
                
                final_decision = response.decision.value if hasattr(response.decision, 'value') else response.decision
                reason_codes = response.reason_codes
                
                # Code matching separation
                code_matching_hcpcs = None
                code_matching_icd10 = []
                policy_evidence = []
                
                for ev in response.evidence:
                    ev_dict = ev.model_dump() if hasattr(ev, 'model_dump') else (ev if isinstance(ev, dict) else ev.__dict__)
                    typ = ev_dict.get('type')
                    if typ == "HCPCS":
                        code_matching_hcpcs = ev_dict
                    elif typ == "ICD10":
                        code_matching_icd10.append(ev_dict)
                    else:
                        policy_evidence.append(ev_dict)
                
                sat = 0
                nsat = 0
                unk = 0
                
                criteria_list = []
                
                for crit in response.criteria:
                    c_dict = crit.model_dump() if hasattr(crit, 'model_dump') else (crit if isinstance(crit, dict) else crit.__dict__)
                    eval_type = c_dict.get('evaluator')
                    if hasattr(eval_type, 'value'): eval_type = eval_type.value
                    status_val = c_dict.get('status')
                    if hasattr(status_val, 'value'): status_val = status_val.value
                    c_dict['evaluator'] = eval_type
                    c_dict['status'] = status_val
                    
                    if eval_type == "LLM" and status_val != "NOT_EVALUATED":
                        llm_used = "YES"
                    
                    if status_val == "SATISFIED": sat += 1
                    elif status_val == "NOT_SATISFIED": nsat += 1
                    else: unk += 1
                    
                    criteria_list.append(c_dict)
                
                if criteria_list:
                    rag_used = "YES"
                
                overall_pol = ncd_result if ncd_result not in ("NOT_ADDRESSED", "", None) else (lcd_result if article_result in ("NOT_ADDRESSED", "", None) else article_result)

                structured_json.update({
                    "policy_path": path,
                    "policy_evidence": policy_evidence,
                    "rag_evidence": [r.model_dump() if hasattr(r, 'model_dump') else r.__dict__ for r in response.rag_evidence] if hasattr(response, 'rag_evidence') else [],
                    "code_matching": ([code_matching_hcpcs] if code_matching_hcpcs else []) + code_matching_icd10,
                    "policy_evaluation": {
                        "criteria": criteria_list,
                        "overall_result": overall_pol
                    },
                    "evidence_fusion": {
                        "satisfied": sat,
                        "not_satisfied": nsat,
                        "unknown": unk,
                        "result": overall_pol
                    },
                    "final_decision": {
                        "decision": final_decision,
                        "reason": response.reason,
                        "reason_codes": reason_codes
                    }
                })

                
                print("\n\n" + "="*60 + "\nPRIOR AUTHORIZATION EVALUATION\n" + "="*60)
                print("\nREQUEST\n" + "-"*60)
                print(f"\nProcedure Code:\n    {request.procedure_code}")
                print(f"\nDiagnosis:\n    {request.diagnosis_codes[0]}")
                print(f"\nState:\n    {request.state}")
                print(f"\nPatient Age:\n    {request.patient_age}")
                print(f"\nClinical Notes:\n    {request.clinical_notes}")
                
                print("\n\n" + "="*60 + "\nPOLICY IDENTIFICATION\n" + "="*60)
                print(f"\nNCD:\n    {ncd_id if ncd_id else ncd_result}")
                
                jurisdiction_str = f"{request.state} → LCD {lcd_id}" if lcd_id else jurisdiction_result
                print(f"\nJurisdiction:\n    {jurisdiction_str}")
                
                if lcd_id:
                    lcd_title = ""
                    for p in response.policies:
                        if p.policy_type == "LCD" and p.policy_id == lcd_id:
                            lcd_title = p.title or "Epidural Steroid Injections for Pain Management"
                    print(f"\nLCD:\n    {lcd_id}\n    {lcd_title}")
                if article_id:
                    print(f"\nArticle:\n    {article_id}")
                
                print("\n\n" + "="*60 + "\nPOLICY EVIDENCE\n" + "="*60)
                
                # Check for RAG Evidence first
                if hasattr(response, 'rag_evidence') and response.rag_evidence:
                    for ev in response.rag_evidence:
                        print(f"\nSource:\n    {ev.policy_type} {ev.policy_id}")
                        print(f"\nSection:\n    {ev.section or 'Coverage Indications'}")
                        
                        text = ev.text.strip().replace("\n", "\n    ")
                        print(f"\nRetrieved Evidence:\n    {text}")
                        if ev.similarity_score is not None:
                            print(f"\nRAG Similarity:\n    {ev.similarity_score:.4f}")
                        else:
                            print(f"\nRAG Similarity:\n    N/A")
                elif code_matching_hcpcs and code_matching_hcpcs.get('result') == 'EXCLUDED' and code_matching_hcpcs.get('identifier') == ncd_id:
                    print(f"\nSource:\n    NCD {ncd_id}")
                    print(f"\nSection:\n    Coverage Indications")
                    print(f"\nRetrieved/Structured Evidence:\n    Explicit NCD exclusion.")
                else:
                    print(f"\nRAG:\n    NOT USED")
                    print(f"\nReason:\n    No semantic policy criterion was identified in the applicable policy evidence.")
                
                print("\n\n" + "="*60 + "\nCODE MATCHING\n" + "="*60)
                if code_matching_hcpcs:
                    print("\nHCPCS\n" + "-"*60)
                    print(f"\nSubmitted:\n    {code_matching_hcpcs.get('code')}")
                    
                    src_id = code_matching_hcpcs.get('identifier')
                    if src_id == ncd_id:
                        src_str = f"NCD {src_id}"
                    elif src_id == lcd_id:
                        src_str = f"LCD {src_id}"
                    else:
                        src_str = f"Article {src_id}"
                        
                    print(f"\nPolicy:\n    {src_str}")
                    print(f"\nDatabase Result:\n    {code_matching_hcpcs.get('result')}")
                
                if code_matching_icd10:
                    for icd in code_matching_icd10:
                        print("\n\nICD-10\n" + "-"*60)
                        print(f"\nSubmitted:\n    {icd.get('code')}")
                        
                        src_id = icd.get('identifier')
                        if src_id == ncd_id:
                            src_str = f"NCD {src_id}"
                        elif src_id == lcd_id:
                            src_str = f"LCD {src_id}"
                        else:
                            src_str = f"Article {src_id}"
                            
                        print(f"\nPolicy:\n    {src_str}")
                        print(f"\nDatabase Result:\n    {icd.get('result')}")
                
                print("\n\n" + "="*60 + "\nPOLICY CRITERIA\n" + "="*60)
                for idx, c in enumerate(criteria_list, 1):
                    print(f"\nC{idx}\n" + "-"*60)
                    req = c.get('criterion').replace("\n", "\n    ")
                    print(f"\nRequirement:\n    {req}")
                    
                    c_type = c.get('criterion_type', c.get('type'))
                    if hasattr(c_type, 'value'): c_type = c_type.value
                    print(f"\nType:\n    {c_type}")
                    
                    eval_type = c.get('evaluator')
                    if eval_type == "LLM":
                        eval_type = "QWEN"
                    print(f"\nEvaluator:\n    {eval_type}")
                    
                    print(f"\nPolicy Evidence:")
                    for poe in c.get('policy_evidence', []):
                        poe_formatted = poe.replace("\n", "\n    ")
                        print(f"    {poe_formatted}")
                        
                    print(f"\nPatient Evidence:")
                    for pe in c.get('patient_evidence', []):
                        print(f"    {pe}")
                        
                    print(f"\nResult:\n    {c.get('status')}")
                    
                    explanation = c.get('status') + " by " + eval_type
                    if eval_type == "SQL":
                        if "HCPCS" in c.get('criterion_id', ''):
                            explanation = f"The submitted procedure code {request.procedure_code} was evaluated against the policy data. Evaluated as {c.get('status')} by SQL."
                        elif "ICD10" in c.get('criterion_id', ''):
                            explanation = f"The submitted diagnosis {request.diagnosis_codes[0]} was evaluated against the policy data. Evaluated as {c.get('status')} by SQL."
                    elif eval_type == "QWEN":
                        explanation = f"The submitted clinical documentation was reviewed against this semantic requirement. Evaluated as {c.get('status')} by Qwen."
                        
                    # Fix formatting for explanation
                    print(f"\nExplanation:\n    {explanation}\n")
                    
                print("\n\n" + "="*60 + "\nEVIDENCE FUSION\n" + "="*60)
                print(f"\nSATISFIED:\n    {sat}")
                print(f"\nNOT_SATISFIED:\n    {nsat}")
                print(f"\nUNKNOWN:\n    {unk}")
                print(f"\nPolicy Result:\n    {structured_json['evidence_fusion']['result']}")
                
                print("\n\n" + "="*60 + "\nFINAL DECISION\n" + "="*60)
                print(f"\nDecision:\n    {final_decision}")
                
                print("\nDecision Basis:\n")
                if final_decision == "APPROVE":
                    print("    All mandatory policy criteria were satisfied.\n")
                elif final_decision == "PEND":
                    print("    The request could not be automatically approved due to unmet or unknown criteria.\n")
                else:
                    print("    Additional information is required to make a decision.\n")
                    
                for c in criteria_list:
                    req_short = c.get('criterion').split('.')[0][:40] + "..."
                    eval_type = c.get('evaluator')
                    if eval_type == "LLM":
                        eval_type = "QWEN"
                    
                    suffix = f" by {eval_type}" if eval_type == "QWEN" else ""
                    print(f"    • {req_short} → {c.get('status')}{suffix}")
                    
                print(f"\n    Evidence Fusion:\n        {structured_json['evidence_fusion']['result']}")
                print(f"\n    DecisionEngine:\n        {structured_json['evidence_fusion']['result']} → {final_decision}\n")

                if final_decision not in ["APPROVE", "PEND", "REQUEST_MORE_INFORMATION"]:
                    print(f"\n❌ INVALID FINAL DECISION CONTRACT: {final_decision}")

            # Collect results
            results.append({
                "test_name": test_name,
                "icd10_prefix": icd10_prefix,
                "icd10": icd10_code,
                "procedure_code": request.procedure_code,
                "state": request.state,
                "ncd_id": ncd_id,
                "ncd_result": ncd_result,
                "rag_used": rag_used,
                "lcd_id": lcd_id,
                "lcd_result": lcd_result,
                "article_id": article_id,
                "article_result": article_result,
                "llm_used": llm_used,
                "final_decision": final_decision,
                "reason_codes": ";".join(reason_codes),
                "error": error_msg,
                "structured_json": structured_json
            })

    # Print Summary
    print("\n" + "="*60)
    print("ICD PREFIX SUMMARY")
    print("="*60 + "\n")
    
    for prefix in ["M", "E", "J"]:
        prefix_tests = [r for r in results if r["icd10_prefix"] == prefix]
        approves = len([r for r in prefix_tests if r["final_decision"] == "APPROVE"])
        pends = len([r for r in prefix_tests if r["final_decision"] == "PEND"])
        rmis = len([r for r in prefix_tests if r["final_decision"] == "REQUEST_MORE_INFORMATION"])
        errors = len([r for r in prefix_tests if r["error"]])
        
        print(f"{prefix} PREFIX")
        print(f"    Tests: {len(prefix_tests)}")
        print(f"    APPROVE: {approves}")
        print(f"    PEND: {pends}")
        print(f"    REQUEST_MORE_INFORMATION: {rmis}")
        print(f"    Errors: {errors}\n")

    # Print Table
    print("\n" + "="*60)
    print("COMPARISON TABLE")
    print("="*60 + "\n")
    
    header = "Prefix | ICD-10 | HCPCS | State | NCD | LCD | Article | LLM | Decision"
    print(header)
    print("-" * len(header))
    for r in results:
        ncd_id = str(r['ncd_id']) if r['ncd_id'] is not None else ""
        lcd_id = str(r['lcd_id']) if r['lcd_id'] is not None else ""
        art_id = str(r['article_id']) if r['article_id'] is not None else ""
        print(f"{r['icd10_prefix']:<6} | {r['icd10']:<6} | {r['procedure_code']:<5} | {r['state']:<5} | {ncd_id:<3} | {lcd_id:<3} | {art_id:<7} | {r['llm_used']:<3} | {r['final_decision']}")
        
    # Save Results
    os.makedirs("reports", exist_ok=True)
    
    with open("reports/icd_prefix_requests.json", "w") as f:
        json_export = [r["structured_json"] for r in results]
        json.dump(json_export, f, indent=4)
        
    with open("reports/icd_prefix_requests.csv", "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "test_name", "icd10_prefix", "icd10", "procedure_code", "state",
            "ncd_id", "ncd_result", "rag_used", "lcd_id", "lcd_result", 
            "article_id", "article_result", "llm_used", "final_decision",
            "reason_codes", "error"
        ], extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)

if __name__ == "__main__":
    run_tests()
