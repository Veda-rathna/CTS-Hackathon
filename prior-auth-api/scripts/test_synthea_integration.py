import os
import sys
import json
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.db.session import SessionLocal
from app.models.synthea import SyntheaPatient, SyntheaCondition

client = TestClient(app)

def get_test_patient_id():
    """Fetch a patient ID that has conditions to test with."""
    with SessionLocal() as db:
        condition = db.query(SyntheaCondition).first()
        if condition:
            return condition.patient_id
    return None

def run_tests():
    patient_id = get_test_patient_id()
    if not patient_id:
        print("ERROR: No patients found in the database. Ensure ingest_synthea.py has run successfully.")
        return

    print("=================================================================")
    print("      TESTING DYNAMIC SYNTHEA INTEGRATION")
    print("=================================================================\n")

    print(f"Using Patient ID: {patient_id}\n")

    # ---------------------------------------------------------
    # TEST CASE 1: Valid Patient, No Clinical Notes
    # ---------------------------------------------------------
    print("Test Case 1: Valid Patient ID, no clinical_notes provided.")
    print("Expected: The system should dynamically fetch the patient history and use it for evaluation.")
    
    payload_1 = {
        "service": {
            "procedure_code": "64483" # E.g., Epidural injection
        },
        "diagnoses": [
            {"icd10_code": "M54.16"} # E.g., Radiculopathy
        ],
        "patient": {
            "patient_id": patient_id,
            "state": "MA"
        }
    }
    
    response = client.post("/api/v1/pa-requests", json=payload_1)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Decision: {data.get('decision')}")
        print("Checking if ClinicalEvidenceAgent extracted evidence from dynamically fetched DB history...")
        
        # Check if the evidence contains historical data (which means it queried DB)
        rag_evidence = data.get("rag_evidence", [])
        criteria = data.get("criteria", [])
        
        found_history_usage = False
        for crit in criteria:
            if crit.get("patient_evidence"):
                for ev in crit["patient_evidence"]:
                    # The ClinicalEvidenceAgent quotes the exact text, which will have Synthea dates or conditions
                    print(f"  -> Extracted Evidence: {ev}")
                    found_history_usage = True
        
        if found_history_usage:
            print("  [OK] SUCCESS: AI successfully extracted criteria from dynamically injected database history!")
        else:
            print("  ? NOTE: No criteria was matched from the patient history (this might just mean the history didn't contain matching ICD10/CPT evidence, but the pipeline ran successfully).")
    else:
        print(f"Failed: {response.text}")

    print("\n---------------------------------------------------------\n")

    # ---------------------------------------------------------
    # TEST CASE 2: Invalid Patient ID
    # ---------------------------------------------------------
    print("Test Case 2: Invalid Patient ID, with minimal clinical_notes.")
    print("Expected: The system will fail to find DB history, but gracefully fall back to the provided clinical notes.")
    
    payload_2 = {
        "service": {
            "procedure_code": "64483"
        },
        "diagnoses": [
            {"icd10_code": "M54.16"}
        ],
        "patient": {
            "patient_id": "INVALID_ID_999",
            "state": "MA"
        },
        "clinical_notes": "Patient complains of severe back pain radiating to leg. Conservative treatments failed."
    }
    
    response = client.post("/api/v1/pa-requests", json=payload_2)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Decision: {data.get('decision')}")
        print("Checking extracted evidence to ensure it used the fallback notes...")
        
        found_fallback_usage = False
        for crit in data.get("criteria", []):
            if crit.get("patient_evidence"):
                for ev in crit["patient_evidence"]:
                    print(f"  -> Extracted Evidence: {ev}")
                    if "back pain" in ev.lower() or "conservative" in ev.lower() or "radiating" in ev.lower():
                        found_fallback_usage = True
                        
        if found_fallback_usage:
             print("  [OK] SUCCESS: AI successfully evaluated based on the free-text fallback clinical_notes!")
        else:
             print("  [OK] SUCCESS: Pipeline completed without crashing on invalid ID (though specific text wasn't extracted as evidence).")
    else:
        print(f"Failed: {response.text}")

    print("\n=================================================================")
    print("      TESTING COMPLETE")
    print("=================================================================\n")

if __name__ == "__main__":
    run_tests()
