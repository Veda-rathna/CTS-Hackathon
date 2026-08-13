import json
import csv
import os
import re

# Load the unmapped NCDs
with open('unmapped_ncds.json', 'r') as f:
    ncd_dict = json.load(f)

# Rules for realistic mock mappings
rules = [
    (r'Acupuncture', '97810'), # Acupuncture, 1 or more needles
    (r'Abortion', '59840'), # Induced abortion
    (r'Bed|Mattress|Corset|Pump|Equipment|Wheelchair|Shoe|Aid|Cane|Monitor', 'E1399'), # Durable medical equipment
    (r'Blood|Transfusion', '36430'), # Blood transfusion service
    (r'Cardiac|Heart|Pacemaker|Defibrillator', '33206'), # Insertion of heart pacemaker
    (r'Surgery|Transplant|Resection|Bypass|Appendectomy|Keratoplasty', '33945'), # Heart transplant (generic surgery)
    (r'Test|Assay|Antigen|Panel|Testing|Screening|Smear|Occult|Glucose', '80050'), # General health panel
    (r'Therapy|Rehabilitation|Counseling', '97110'), # Therapeutic procedure
    (r'Stimulation|Stimulator', '64550'), # Application of surface neurostimulator
    (r'Imaging|PET|Tomography|X-Ray|Scanning|MRI', '70551'), # MRI
    (r'Lens|Eye|Ocular', '66984'), # Cataract surgery with IOL
    (r'Prostate', '55866'), # Laparoscopy, surgical prostatectomy
]

output_file = os.path.join('Filtered_Data', 'mock_ncd_mappings.csv')
os.makedirs('Filtered_Data', exist_ok=True)

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['ncd_id', 'hcpcs_code', 'description'])
    
    for ncd_id, title in ncd_dict.items():
        assigned_code = '99201' # Default: Office/outpatient visit
        for pattern, code in rules:
            if re.search(pattern, title, re.IGNORECASE):
                assigned_code = code
                break
        
        # Add the required disclaimer
        description = f"[AI_GENERATED] [NON_AUTHORITATIVE] [REQUIRES_VALIDATION] Simulated mapping for '{title}'"
        writer.writerow([ncd_id, assigned_code, description])

print(f"Generated {len(ncd_dict)} mock mappings in {output_file}")
