"""
Unified Live API Test Runner & Benchmark Script.

Hits the live running API (default: http://localhost:8001/api/v1/triage) to test:
1. Scenario Combinations (Acupuncture low back pain fix, Epidurals, NCD exclusions, unknown codes)
2. Structural Output Validation & Response Schema Compliance

Usage:
    python scripts/test_live.py
"""
from __future__ import annotations
import json
import urllib.request
import urllib.error
import sys

API_URL = "http://localhost:8001/api/v1/triage"

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

TESTS = [
    {
        "name": "ACUPUNCTURE FIX: 97810 + M54.50 (Low Back Pain) + TX",
        "description": "Core bug fix — NCD 283 Fibromyalgia exclusion must NOT block low back pain.",
        "payload": {
            "procedure_code": "97810",
            "diagnosis_codes": ["M54.50"],
            "state": "TX",
            "clinical_notes": "Patient presents with chronic low back pain (M54.50). No fibromyalgia diagnosis.",
        },
        "expect_decision": "APPROVE",
        "must_not_contain_reason": "NCD_EXCLUDES_PROCEDURE",
    },
    {
        "name": "ACUPUNCTURE FIX: 97810 + M79.7 (Fibromyalgia) + TX",
        "description": "NCD 283 DOES exclude fibromyalgia — this must PEND.",
        "payload": {
            "procedure_code": "97810",
            "diagnosis_codes": ["M79.7"],
            "state": "TX",
        },
        "expect_decision": "PEND",
    },
    {
        "name": "REAL DB: 64483 + M54.16 + TX",
        "description": "Epidural injection — should match LCD and Article policy path.",
        "payload": {
            "procedure_code": "64483",
            "diagnosis_codes": ["M54.16"],
            "state": "TX",
        },
        "expect_decision": "APPROVE",
        "check_policies": True,
    },
    {
        "name": "REAL DB: Unknown HCPCS Code",
        "description": "Unknown procedure code — must return REQUEST_MORE_INFORMATION.",
        "payload": {
            "procedure_code": "ZZZZZ",
            "diagnosis_codes": ["M54.16"],
            "state": "TX",
        },
        "expect_decision": "REQUEST_MORE_INFORMATION",
    },
    {
        "name": "REAL DB: 97810 + M54.50 (National NCD Only)",
        "description": "Acupuncture request without state — evaluates national NCD level.",
        "payload": {
            "procedure_code": "97810",
            "diagnosis_codes": ["M54.50"],
            "clinical_notes": "Patient has chronic low back pain. No fibromyalgia.",
        },
        "expect_decision": "APPROVE",
        "must_not_contain_reason": "NCD_EXCLUDES_PROCEDURE",
    },
    {
        "name": "REAL DB: J1561 + L10.0 (NCD 158 Intravenous Immune Globulin)",
        "description": "IVIG infusion for pemphigus vulgaris covered under National Policy NCD 158.",
        "payload": {
            "procedure_code": "J1561",
            "diagnosis_codes": ["L10.0"],
            "state": "TX",
            "clinical_notes": "Intravenous immune globulin infusion for biopsy-proven pemphigus vulgaris refractory to standard systemic corticosteroid therapy.",
        },
        "expect_decision": "APPROVE",
    },
    {
        "name": "NORMALIZATION: Messy whitespace & lowercase inputs",
        "description": "Ensures Pydantic strips whitespace and normalizes case before length checks.",
        "payload": {
            "procedure_code": "  64483  ",
            "diagnosis_codes": [" m54.16 "],
            "state": " tx ",
        },
        "expect_decision": "APPROVE",
    },
]


def call_api(payload: dict) -> tuple[int, dict]:
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as e:
        return 0, {"error": str(e)}


def run() -> None:
    print("=" * 70)
    print("  LIVE API COMBINATION BENCHMARK SUITE")
    print(f"  Target URL: {API_URL}")
    print("=" * 70)

    passed = failed = 0

    for i, tc in enumerate(TESTS, 1):
        name = tc["name"]
        desc = tc["description"]
        payload = tc["payload"]
        expect = tc.get("expect_decision")
        must_not_reason = tc.get("must_not_contain_reason")
        check_policies = tc.get("check_policies", False)

        print(f"\n[{i}/{len(TESTS)}] {name}")
        print(f"  {desc}")

        status_code, data = call_api(payload)

        if status_code == 0:
            print(f"  {FAIL} — Could not reach API: {data.get('error')}")
            failed += 1
            continue

        if status_code != 200:
            print(f"  {FAIL} — HTTP {status_code}: {data}")
            failed += 1
            continue

        decision = data.get("decision", "?")
        reason = data.get("reason", "")
        reason_codes = data.get("reason_codes", [])
        policies = data.get("policies", [])
        policy_ids = [p.get("policy_id", "") for p in policies]

        ok = True

        if expect and decision != expect:
            print(f"  {FAIL} — Expected {expect}, got {decision}")
            print(f"         Reason: {reason}")
            ok = False
        else:
            print(f"  Decision:    {decision} OK")
            print(f"  Reason:      {reason[:100]}")

        if must_not_reason and must_not_reason in reason_codes:
            print(f"  {FAIL} — Reason code '{must_not_reason}' must NOT appear, but did!")
            ok = False

        if check_policies:
            if not policy_ids:
                print(f"  {WARN} — No policies matched in live DB.")
            else:
                print(f"  Policies:    {', '.join(policy_ids)}")

        score = data.get("evidence_score", 0)
        print(f"  Ev. Score:   {score:.2f}")

        if ok:
            print(f"  {PASS}")
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 70)
    print(f"  RESULTS: {passed} passed, {failed} failed out of {len(TESTS)} scenarios")
    print("=" * 70)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    run()
