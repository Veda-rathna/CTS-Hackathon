import os
import sys

os.environ["USE_MOCK_REPOSITORIES"] = "false"
sys.path.insert(0, r"c:\Users\navee\Desktop\cts_hackathon\CTS-Hackathon\prior-auth-api")

from app.schemas.triage import TriageRequest
from scripts.demo_output import DEMOS, build_service, print_report

def run_all_seven():
    service = build_service()
    print("=================================================================")
    print("          EVALUATING ALL 7 LIVE DEMO CASES")
    print("=================================================================")
    for demo in DEMOS:
        name = demo["name"]
        req_data = {k: v for k, v in demo.items() if k != "name"}
        req = TriageRequest(**req_data)
        try:
            resp = service.evaluate(req)
            print(f"\n[{demo.get('procedure_code')}] {name}")
            print(f"  Decision: {resp.decision}")
            print(f"  Reason  : {resp.reason}")
            print(f"  Criteria ({len(resp.evaluated_criteria)}):")
            for c in resp.evaluated_criteria:
                print(f"    • [{c.evaluator.value if hasattr(c.evaluator, 'value') else c.evaluator}] {c.criterion_id} ({'Mandatory' if c.mandatory else 'Informational'}): {c.status.value if hasattr(c.status, 'value') else c.status}")
                print(f"      Text: {repr(c.criterion[:90])}")
        except Exception as e:
            print(f"\n❌ ERROR in {name}: {e}")
            import traceback; traceback.print_exc()

if __name__ == "__main__":
    run_all_seven()
