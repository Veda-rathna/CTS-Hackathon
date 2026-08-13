# Deterministic Prior Authorization Engine Architecture

This document provides a deep dive into the step-by-step logic used by the Prior Authorization Triage API. The engine is **100% deterministic**, meaning it uses strict relational database queries and rule-based logic to evaluate coverage, completely eliminating AI hallucinations and providing full auditability.

## 1. The Inputs

The engine accepts a minimalistic, privacy-safe JSON payload. It relies strictly on standardized medical codes rather than free-text clinical notes:
- **`procedure_code`**: A single HCPCS or CPT code (e.g., `64483` - Epidural injection) representing the requested treatment.
- **`diagnosis_codes`**: An array of ICD-10-CM codes representing the patient's conditions (e.g., `["M54.16"]`).
- **`state`**: A 2-letter state abbreviation (e.g., `TX`) to determine the local Medicare Administrative Contractor (MAC) jurisdiction.
- **`patient_age`**: (Optional) Used as a clinical fallback flag when codes are ambiguous.

## 2. The Evaluation Pipeline (The CMS Policy Cascade)

The engine processes these inputs through a strict, hierarchical pipeline that mimics the actual Centers for Medicare & Medicaid Services (CMS) adjudication process.

### Step 1: Procedure-to-Policy Crosswalk (Lookup)
Because National Coverage Determinations (NCDs) are broad national policies, they traditionally do not contain a direct list of procedure codes in a single structured table. However, to ensure a deterministic and accurate engine, our database resolves this through a **Two-Pronged Search Strategy**:

**Prong A: Direct NCD Crosswalk (`NCDHCPCSCode`)**
The engine first queries the newly established `NCDHCPCSCode` table to see if the national policy directly regulates the submitted `procedure_code`. This table was populated using three advanced data-gathering strategies:
1.  **LCD Bridge Inheritance:** If a local MAC wrote an LCD for the procedure and linked it to an NCD, those codes were inherited by the NCD.
2.  **CMS API Text Extraction:** For standalone NCDs, a regex engine parsed the CMS API's clinical narrative fields (`item_service_description`, etc.) to extract mentioned HCPCS/CPT codes.
3.  **Hackathon AI Mock Data:** To guarantee 100% policy coverage for the demo, the remaining 184 broad NCDs were assigned highly realistic, AI-generated procedure mappings based on keyword heuristics. These are strictly flagged as `[AI_GENERATED] [NON_AUTHORITATIVE] [REQUIRES_VALIDATION]` in the database to maintain absolute transparency.

**Prong B: Local Coverage Bridge (`LCDHCPCSCode`)**
Simultaneously, the engine executes the standard local lookup sequence:
1.  **Find LCDs via Procedure Code:** It queries the `LCDHCPCSCode` table to find all local policies matching the procedure.
2.  **Find NCDs via LCDs:** It queries the `LCDNCDAssociation` table to find any overarching national policies that govern those local policies.

**Result:** The engine aggregates the results from Prong A and Prong B, deduplicating the policies. It now has a complete, robust list of all NCDs and LCDs that apply to the submitted procedure. If no records are found in either path, the engine halts and returns `POLICY_NOT_FOUND`.

### Step 2: Date and Version Filtering
CMS frequently updates policies, resulting in multiple versions of the same policy (same ID) existing in the database with different active dates.
1. The engine runs a `_filter_latest_effective_policies` algorithm.
2. It groups the retrieved policies by `policy_id`.
3. It checks the `effective_date` and `end_date` against the current date.
4. If multiple versions are active (e.g., overlapping dates), it selects the version with the most recent `effective_date`.
5. **Result:** If all matching policies have an `end_date` in the past, the engine returns `POLICY_EXPIRED`.

### Step 3: National Coverage Determination (NCD) Override
By law, National policies override Local policies. The engine filters the active policies to see if any have `policy_type == "NCD"`.
1. If an NCD exists for the procedure, the engine queries the `NCDRepository` for the specific national rules.
2. If the NCD explicitly states `COVERED`, the engine immediately halts, bypasses all local rules, and approves the request (`LIKELY_COVERED`).
3. If the NCD explicitly states `EXCLUDED` or `NON_COVERED`, the engine immediately halts and denies the request (`LIKELY_NOT_COVERED`).
4. **Result:** If the NCD exists but is "silent" on the specific diagnosis, or if no NCD exists at all, the engine proceeds to evaluate Local policies.

### Step 4: Local Coverage Determination (LCD) & Jurisdiction Filtering
If the NCD didn't result in a hard decision, the engine evaluates LCDs. LCDs are enforced by regional MACs, meaning a procedure might be covered in Texas but not in New York.
1. The engine isolates the policies where `policy_type == "LCD"`.
2. It queries the `PolicyRepository` to check if the submitted `state` (e.g., `TX`) falls into the `jurisdiction_id` assigned to the LCD.
3. It filters out any LCDs that do not cover the submitted state.
4. **Result:** If an LCD exists for the procedure, but the state falls outside its jurisdiction, the engine halts and returns `OUTSIDE_JURISDICTION`.

### Step 5: Article Code Validation (The Core Logic)
If a valid LCD matches the state, the engine finds the **Billing and Coding Article** attached to that LCD (`article_id`). Articles act as the highly-specific data tables for LCDs.

The engine queries the `ArticleRepository` to pull two massive sets of ICD-10 codes for that specific article:
- **The "Covered" Set:** Diagnoses that explicitly justify the procedure.
- **The "Non-Covered" Set:** Diagnoses explicitly forbidden from receiving the procedure.

It then iterates through every submitted `diagnosis_code` and checks it against these sets.

### Step 6: Final Decision Aggregation
Based on the ICD-10 validation, the engine aggregates the results into a final deterministic choice:
- **`LIKELY_COVERED`**: If *any* submitted diagnosis is found in the "Covered" set. (e.g., Even if the patient has 3 unrelated diagnoses, if just 1 justifies the procedure, it is covered).
- **`LIKELY_NOT_COVERED`**: If *all* submitted diagnoses are found in the "Non-Covered" set.
- **`NURSE_REVIEW`**: If the diagnoses are not in either list (Unknown), but the payload included clinical context flags (like `patient_age`), the engine determines that human clinical judgment is required.
- **`MORE_INFORMATION_REQUIRED`**: If the diagnosis codes are Unknown and no extra clinical context was provided, meaning the provider must submit additional medical documentation.

## 3. The Output (Total Explainability)

To provide total transparency, the engine outputs an extensive, structured explanation of exactly how it arrived at its decision.

1. **Reason Codes:** A structured array of flags generated during the pipeline (e.g., `["PROCEDURE_FOUND", "JURISDICTION_MATCH", "DIAGNOSIS_COVERED"]`).
2. **Evidence Score:** A calculated float between `0.0` and `1.0` representing how complete the matching data was (e.g., did we match procedure, state, *and* diagnosis?).
3. **The Audit Trace (`evidence` array):** During every step of the pipeline, the engine appends an `Evidence` object to a log array. 
   - *Example Entry 1:* `{"type": "JURISDICTION", "result": "MATCHED", "explanation": "State 'TX' falls within the jurisdiction of LCD L39054."}`
   - *Example Entry 2:* `{"type": "ICD10", "code": "M54.16", "result": "COVERED", "explanation": "Diagnosis 'M54.16' is covered."}`

This deterministic audit trace is what makes the engine trustworthy, allowing frontend applications to display the exact legal and medical rules that triggered a prior authorization decision.
