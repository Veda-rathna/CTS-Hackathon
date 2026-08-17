import os
import sys

os.environ["USE_MOCK_REPOSITORIES"] = "false"
sys.path.insert(0, r"c:\Users\navee\Desktop\cts_hackathon\CTS-Hackathon\prior-auth-api")
sys.stdout.reconfigure(line_buffering=True)

from app.schemas.triage import TriageRequest
from scripts.demo_output import DEMOS, build_service

service = build_service()

for i, demo in enumerate(DEMOS, 1):
    name = demo["name"]
    req_data = {k: v for k, v in demo.items() if k != "name"}
    req = TriageRequest(**req_data)
    print(f"\n==================== [{i}/7] {name} ====================", flush=True)
    print(f"Proc: {req.procedure_code} | Dx: {req.diagnosis_codes} | State: {req.state}", flush=True)
    print(f"Notes: {req.clinical_notes}", flush=True)
    try:
        resp = service.evaluate(req)
        print(f"DECISION: {resp.decision}", flush=True)
        print(f"Reason: {resp.reason}", flush=True)
        print(f"Criteria:", flush=True)
        for c in (resp.criteria or []):
            print(f"  • [{c.criterion_id}] ({c.evaluator.value if hasattr(c.evaluator, 'value') else c.evaluator} | {'Mandatory' if c.mandatory else 'Informational'}): {c.status.value if hasattr(c.status, 'value') else c.status}", flush=True)
            print(f"    Text: {c.criterion}", flush=True)
            if c.explanation:
                first_line = c.explanation.split('\n')[0][:120]
                print(f"    Expl: {first_line}", flush=True)
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
        import traceback; traceback.print_exc()

print("\n==================== ALL 7 SCENARIOS COMPLETED ====================", flush=True)
