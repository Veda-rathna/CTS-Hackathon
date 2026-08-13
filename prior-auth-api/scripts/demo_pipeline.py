import json
import sys
import os

# Ensure the app module can be found when running directly as a script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app
def run_demo():
    client = TestClient(app)
    
    print("======================================================")
    print(" DEMO 1: LIKELY COVERED (Happy Path)")
    print("======================================================")
    
    request_1 = {
        "procedure_code": "64483", # Epidural injection
        "diagnosis_codes": ["M54.16"], # Radiculopathy (covered by LCD)
        "state": "TX",
        "patient_age": 65,
        "clinical_notes": "Patient presents with severe lower back pain and sciatica."
    }
    
    print("\n[INPUT REQUEST]")
    print(json.dumps(request_1, indent=2))
    
    response_1 = client.post("/api/v1/triage", json=request_1)
    
    print("\n[PIPELINE OUTPUT]")
    print(json.dumps(response_1.json(), indent=2))


    print("\n\n======================================================")
    print(" DEMO 2: LIKELY NOT COVERED (Explicit Exclusion)")
    print("======================================================")
    
    request_2 = {
        "procedure_code": "64483",
        "diagnosis_codes": ["Z00.00"], # General medical exam (explicitly non-covered)
        "state": "TX",
    }
    
    print("\n[INPUT REQUEST]")
    print(json.dumps(request_2, indent=2))
    
    response_2 = client.post("/api/v1/triage", json=request_2)
    
    print("\n[PIPELINE OUTPUT]")
    print(json.dumps(response_2.json(), indent=2))
    
    
    print("\n\n======================================================")
    print(" DEMO 3: OUTSIDE JURISDICTION")
    print("======================================================")
    
    request_3 = {
        "procedure_code": "64483",
        "diagnosis_codes": ["M54.16"],
        "state": "ZZ", # Invalid state
    }
    
    print("\n[INPUT REQUEST]")
    print(json.dumps(request_3, indent=2))
    
    response_3 = client.post("/api/v1/triage", json=request_3)
    
    print("\n[PIPELINE OUTPUT]")
    print(json.dumps(response_3.json(), indent=2))

    print("\n\n======================================================")
    print(" DEMO 4: NEW DIAGNOSIS CHECK (M00.111)")
    print("======================================================")
    
    request_4 = {
        "procedure_code": "64483",
        "diagnosis_codes": ["M00.111"], # Pneumococcal arthritis, right shoulder
        "state": "TX",
    }
    
    print("\n[INPUT REQUEST]")
    print(json.dumps(request_4, indent=2))
    
    response_4 = client.post("/api/v1/triage", json=request_4)
    
    print("\n[PIPELINE OUTPUT]")
    print(json.dumps(response_4.json(), indent=2))
    print("\n\n======================================================")
    print(" DEMO 5: SEMANTIC EVALUATION (LM Studio / Qwen3-4B)")
    print("======================================================")
    
    request_5 = {
        "procedure_code": "64483",
        "diagnosis_codes": ["M54.16"], # Valid ICD-10
        "state": "TX",
        "patient_age": 65,
        "clinical_notes": "Patient completed conservative treatment for seven months with persistent symptoms despite physical therapy."
    }
    
    print("\n[INPUT REQUEST]")
    print(json.dumps(request_5, indent=2))
    
    response_5 = client.post("/api/v1/triage", json=request_5)
    
    print("\n[PIPELINE OUTPUT]")
    print(json.dumps(response_5.json(), indent=2))

if __name__ == "__main__":
    from app.core.config import get_settings
    settings = get_settings()
    settings.llm_enabled = True
    settings.llm_provider = "lmstudio"
    settings.llm_model = "qwen/qwen3-4b-2507"
    settings.llm_base_url = "http://127.0.0.1:1234/v1"
    run_demo()
