import os
import sys
import uuid
import time
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.pa_request import CanonicalPARequest, PAService, PADiagnosis, PAPatient
from app.services.normalization.normalization_service import NormalizationService
from app.services.pa_request.pa_request_service import PARequestService
from app.schemas.triage import TriageResponse
from app.db.session import SessionLocal
from app.repositories.synthea_repository import SyntheaRepository
from app.models.synthea import SyntheaPatient

def get_real_patient_ids(limit=5):
    """Fetch a few real patient IDs from the database to use in test cases."""
    with SessionLocal() as db:
        patients = db.query(SyntheaPatient).limit(limit).all()
        return [p.id for p in patients]

def generate_test_cases():
    """Generate 100 diverse edge-case test payloads."""
    test_cases = []
    
    real_patient_ids = get_real_patient_ids()
    valid_id = real_patient_ids[0] if real_patient_ids else "mock-valid-id"
    
    # Base structure
    def build_payload(patient_id, proc_code, diag_code, clinical_notes=None, state="MA", age=65):
        payload = {
            "pa_request_id": f"PA-{uuid.uuid4().hex[:8].upper()}",
            "patient": {"patient_id": patient_id, "state": state, "age": age},
            "service": {"procedure_code": proc_code} if proc_code else None,
            "diagnoses": [{"icd10_code": diag_code}] if diag_code else [],
            "clinical_notes": clinical_notes
        }
        return payload

    # 1-10: Valid patient, various notes (testing fusion)
    for i in range(10):
        notes = f"Clinical note {i} " * (i * 2) if i % 2 == 0 else None
        test_cases.append({
            "name": f"Valid Patient, Notes Length {len(notes) if notes else 0}",
            "payload": build_payload(valid_id, "64483", "M54.16", notes),
            "expected_success": True
        })

    # 11-20: Invalid / missing patient IDs
    for i in range(10):
        invalid_id = f"INVALID_{uuid.uuid4()}" if i % 2 == 0 else None
        test_cases.append({
            "name": f"Invalid/Null Patient ID (ID: {invalid_id})",
            "payload": build_payload(invalid_id, "E0601", "G47.33", "Some notes"),
            "expected_success": True 
        })
        
    # 21-30: Missing critical fields (should trigger validation errors in PARequestService)
    for i in range(10):
        proc = "64483" if i % 2 == 0 else None
        diag = "M54.16" if i % 2 != 0 else None
        test_cases.append({
            "name": f"Missing Fields (Proc: {bool(proc)}, Diag: {bool(diag)})",
            "payload": build_payload(valid_id, proc, diag, None),
            "expected_success": False
        })

    # 31-40: Malformed/Extreme codes
    for i in range(10):
        proc = "x" * (i * 10) or "X"
        diag = "y" * (i * 10) or "Y"
        test_cases.append({
            "name": f"Extreme Code Lengths (Proc len: {len(proc)}, Diag len: {len(diag)})",
            "payload": build_payload(valid_id, proc, diag, None),
            "expected_success": True
        })

    # 41-50: SQL Injection attempts / Weird characters in notes
    for i in range(10):
        weird_notes = "Robert'); DROP TABLE Students;--" + chr(1000 + i) * 5
        test_cases.append({
            "name": f"Weird Characters / SQL Injection strings {i}",
            "payload": build_payload(valid_id, "64483", "M54.16", weird_notes),
            "expected_success": True
        })

    # 51-60: Extreme Ages (Negative should fail Pydantic validation)
    for i in range(10):
        age = -50 if i % 2 == 0 else 150 + i
        test_cases.append({
            "name": f"Extreme Age ({age})",
            "payload": build_payload(valid_id, "64483", "M54.16", None, age=age),
            "expected_success": False if age < 0 else True
        })

    # 61-70: Weird States
    for i in range(10):
        state = "massachusetts" if i % 2 == 0 else "ZZ"
        test_cases.append({
            "name": f"State Normalization ({state})",
            "payload": build_payload(valid_id, "64483", "M54.16", None, state=state),
            "expected_success": True
        })

    # 71-80: Huge Clinical Notes (10KB to 100KB)
    for i in range(10):
        huge_notes = "Very long clinical note block " * (300 * (i + 1))
        test_cases.append({
            "name": f"Huge Clinical Notes ({len(huge_notes)} chars)",
            "payload": build_payload(valid_id, "64483", "M54.16", huge_notes),
            "expected_success": True
        })

    # 81-90: Emojis and Complex Unicode
    for i in range(10):
        emoji_notes = "Patient complains of 🤕 back pain and 🩸 bleeding. Needs 🏥 ASAP! ✨" * (i + 1)
        test_cases.append({
            "name": f"Emoji & Unicode Notes (Len: {len(emoji_notes)})",
            "payload": build_payload(valid_id, "64483", "M54.16", emoji_notes),
            "expected_success": True
        })

    # 91-100: Empty arrays / whitespace only
    for i in range(10):
        whitespace_notes = "   \n \t  " * (i + 1)
        test_cases.append({
            "name": f"Whitespace only notes {i}",
            "payload": build_payload(valid_id, "64483", "M54.16", whitespace_notes),
            "expected_success": True
        })

    return test_cases


def run_edge_cases():
    print("=" * 65)
    print("      RUNNING 100 EDGE-CASE TESTS (MOCKED TRIAGE ENGINE)")
    print("=" * 65)
    
    mock_triage_service = MagicMock()
    mock_triage_service.evaluate.return_value = TriageResponse(
        pa_request_id="MOCK", 
        decision="PEND", 
        criteria=[], 
        rag_evidence=[],
        evidence_score=0.0,
        reason="Mock fallback reason"
    )
    
    normalization_service = NormalizationService()
    
    db = SessionLocal()
    synthea_repo = SyntheaRepository(db)
    
    pa_service = PARequestService(
        normalization_service=normalization_service,
        triage_service=mock_triage_service,
        synthea_repository=synthea_repo
    )
    
    test_cases = generate_test_cases()
    
    passed_tests = 0
    failed_tests = 0
    
    start_time = time.time()
    
    for idx, tc in enumerate(test_cases, start=1):
        name = tc["name"]
        raw_payload = tc["payload"]
        expected_success = tc["expected_success"]
        
        try:
            # Parse dict into Pydantic model
            payload_obj = CanonicalPARequest(**raw_payload)
            pa_service.create_pa_request(payload_obj)
            success = True
            
            if success and expected_success:
                triage_req = mock_triage_service.evaluate.call_args[0][0]
                notes = triage_req.clinical_notes or ""
                
                patient = raw_payload.get("patient")
                if patient and patient.get("patient_id") and "INVALID" not in patient.get("patient_id"):
                     assert "SYNTHEA DATABASE PATIENT HISTORY" in notes or "[System: No prior Synthea medical history found" in notes
                     
                if raw_payload.get("clinical_notes"):
                     assert raw_payload["clinical_notes"].strip() in notes
                     
        except ValueError as e:
            success = False
            error_msg = str(e)
        except Exception as e:
            success = False
            error_msg = f"UNEXPECTED ERROR: {e}"
            
        if success == expected_success:
            passed_tests += 1
            status_str = "[OK] PASS"
            print(f"Test {idx:03d} | {status_str} | {name}")
        else:
            failed_tests += 1
            status_str = "[XX] FAIL"
            print(f"Test {idx:03d} | {status_str} | {name} => {error_msg}")
        
    db.close()
    
    duration = time.time() - start_time
    print("-" * 65)
    print(f"RESULTS: {passed_tests}/100 PASSED, {failed_tests}/100 FAILED.")
    print(f"Executed in {duration:.2f} seconds (LLM evaluation bypassed).")
    print("=" * 65)


if __name__ == "__main__":
    run_edge_cases()
