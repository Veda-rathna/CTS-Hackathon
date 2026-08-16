# Audit Phase 1 — CMS Coverage API Runtime Fallback

## 1. Executive Summary

**PHASE 1 STATUS: NOT READY**

Phase 1 CMS Coverage API Runtime Fallback is conceptually outlined but **is not structurally ready or safe for a production hackathon demo.** 

While the local-first logic correctly queries the database and safely defaults to `REQUEST_MORE_INFORMATION` when evidence is missing, the actual CMS runtime fallback pathway is broken. The `CMSCoverageClient` completely lacks the `search_by_hcpcs` method, causing an immediate `AttributeError` crash in production when a local cache miss occurs. Furthermore, `PolicyEvidenceResolver` contains placeholder comments instead of actual normalization and upsert logic, meaning even if the CMS API call succeeded, the data would never be cached or used.

Because the CMS `/v1/search` endpoint fundamentally fails to support HCPCS searches (returning 400 errors), a real-time runtime fallback is architecturally impossible with the current CMS API, making Phase 2 (Background Synchronization) strictly mandatory.

---

## 2. Architecture Audit

**Actual Execution Flow:**
```text
PA Request
 ↓
TriageService.evaluate() [app/services/triage_service.py]
 ↓
PolicyEvidenceResolver.resolve_evidence() [app/services/policy_evidence_resolver.py]
 ↓
PostgresPolicyRepository.find_policies_for_procedure() [app/repositories/postgres/policy_repository.py]
 ↓
LOCAL MISS
 ↓
PolicyEvidenceResolver invokes `self._cms.search_by_hcpcs(procedure_code)`
 ↓
CRASH: AttributeError in CMSCoverageClient (method does not exist)
 ↓
PolicyEvidenceResolver catches Exception
 ↓
Returns `status="UNAVAILABLE", policies=[]`
 ↓
TriageService safely routes to `TriageDecision.PEND` (Decision Safety check passes)
```

**Key Finding:** The intended architecture breaks at the `search_by_hcpcs` boundary because it is mocked in tests but absent in the real client.

---

## 3. CMS API Audit

| Component | Status | Finding |
| :--- | :--- | :--- |
| **Authentication** | ✅ VERIFIED | `GET /v1/metadata/license-agreement/` successfully retrieves the nested `data[0]["Token"]`. |
| **Token refresh** | ✅ VERIFIED | 401 responses successfully trigger `_get_token()` and retry the request up to `max_retries`. |
| **LCD endpoint** | ✅ VERIFIED | `v1/data/lcd` successfully retrieves documents. |
| **Article endpoint** | ✅ VERIFIED | `v1/data/article` successfully retrieves documents. |
| **NCD endpoint** | ✅ VERIFIED | `v1/data/ncd` successfully retrieves documents. |
| **Search by HCPCS**| ❌ BROKEN | Method `search_by_hcpcs` is completely absent from `CMSCoverageClient`. The CMS API `/v1/search` endpoint itself is also known to return 400s. |
| **ID handling** | ✅ VERIFIED | `get_document` correctly strips "L" and "A" prefixes conditionally before calling endpoints. |
| **Error handling** | ⚠️ PARTIAL | `httpx.HTTPStatusError` is caught safely, but missing Python methods cause internal `AttributeError`s. |

---

## 4. Local-First/Fallback Audit

* **LOCAL HIT:** Works. The repository returns populated `PolicyMatch` objects, circumventing the CMS client.
* **LOCAL MISS:** Fails. Triggers the missing `search_by_hcpcs` method and throws an `AttributeError`.
* **LOCAL INCOMPLETE:** ❌ NOT IMPLEMENTED. The resolver only checks `if local_policies:` (if the list is empty). It does not check if the evidence is complete or sufficient.
* **LOCAL STALE:** ❌ NOT IMPLEMENTED. The resolver does not read `retrieved_at` or `last_updated` dates to trigger a refresh.
* **CMS ERROR:** ✅ VERIFIED. Wrapped in a try/except block; returns `status="UNAVAILABLE"` safely.

---

## 5. Database Audit

* **Mock Repository:** Supports basic in-memory appending via `_POLICIES.append()`.
* **PostgreSQL Repository:** ⚠️ PARTIALLY IMPLEMENTED. `upsert_policy` handles versions and duplicates correctly via SQLAlchemy merges, but it is **never actually called** by the Phase 1 `PolicyEvidenceResolver`.
* **Duplicates & Versions:** PostgreSQL schema supports composite primary keys (`ID` + `Version`), preventing uncontrolled duplicates, provided the normalizer passes the correct version.
* **Provenance:** PostgreSQL schema supports `source`, `retrieved_at`, and `content_hash`, but Phase 1 logic does not populate these fields.

---

## 6. Normalization Audit

**Implementation:** ❌ BROKEN / MOCKED
* `PolicyEvidenceResolver` contains a literal comment: `# Normalize and Upsert logic would go here... For Phase 1, if we find something, we'll pretend we cached it.`
* The script `test_cms_normalization.py` contains standalone script-level normalization into a `PolicyMatch` object.

**Critical Data Loss:**
The test normalization converts CMS JSON exclusively into a flat `PolicyMatch` object. It completely discards:
* `hcpcs_codes` list
* `icd10_covered` list
* `icd10_noncovered` list

Because `TriageService` relies on deterministic database checks (e.g., `LCDIcd10Covered` table) for its Decision Engine, returning a flat `PolicyMatch` without upserting the related tables means the Triage Engine would never realize the newly cached policy covers the requested codes.

---

## 7. End-to-End Test (Real PA Request trace)

```text
PA Request (procedure: 00000, diagnosis: A00)
 ↓
TriageService.evaluate()
 ↓
PolicyEvidenceResolver.resolve_evidence('00000', ['A00'])
 ↓
Local DB lookup (returns [])
 ↓
CMSCoverageClient.search_by_hcpcs('00000') 
 ↓
❌ AttributeError: 'CMSCoverageClient' object has no attribute 'search_by_hcpcs'
 ↓
Resolver Exception Handler logs "CMS API Fallback failed"
 ↓
Returns {'status': 'UNAVAILABLE', 'policies': []}
 ↓
TriageService checks `if not evidence_result.get("policies"):`
 ↓
Generates reason: "Policy evidence is currently unavailable (CMS API error). Manual review required."
 ↓
✅ Final Decision: PEND (Safe routing)
```

---

## 8. Test Results

* **`scripts/test_cms_normalization.py`**: **PASSED (Deceptively)**. It works because it manually calls `client.get_document("L39054")` bypassing the broken `search_by_hcpcs` method, and uses `MockPolicyRepository` which accepts flat `PolicyMatch` objects.
* **Real Triage Request (Missing HCPCS)**: **FAILED (Gracefully)**. Crashes on `search_by_hcpcs` but caught by `PolicyEvidenceResolver` try/except block.

---

## 9. Critical Issues

1. **CRITICAL:** `CMSCoverageClient.search_by_hcpcs` is unimplemented. Real-time fallback is impossible.
2. **CRITICAL:** `PolicyEvidenceResolver` does not execute normalization or upserts. It returns empty policies for CMS hits.
3. **CRITICAL:** The prototype normalizer flattens CMS policies into `PolicyMatch` objects, discarding `HCPCS` and `ICD-10` lists. The DB relations (`LCDHCPCSCode`, `LCDIcd10Covered`) will never be populated, breaking the Triage Engine.

---

## 10. Recommended Fixes

| Problem | Why it matters | Recommended fix | Priority |
| :--- | :--- | :--- | :--- |
| CMS `/v1/search` by HCPCS returns 400 | Runtime fallback is physically impossible. | **Proceed with Phase 2 Background Synchronization** using official CMS reports instead of runtime lookups. | CRITICAL |
| Missing Normalization | CMS data is discarded instead of cached. | Create a dedicated `CMSNormalizer` class that maps CMS JSON to full SQLAlchemy relational models (LCD, Article, relations). | CRITICAL |
| `PolicyEvidenceResolver` is stubbed | Cache misses never populate the database. | Connect the `CMSNormalizer` and `PostgresPolicyRepository.upsert_policy()` inside the resolver (or sync worker). | HIGH |

---

## 11. Phase 1 Final Verdict

**PHASE 1 STATUS:**
**NOT READY**

**CMS fallback:**
FAIL

**Local-first:**
PASS

**Normalization:**
FAIL

**Caching:**
FAIL

**PostgreSQL:**
PARTIAL

**PA integration:**
PASS

**Decision safety:**
PASS *(Fails safely by routing to PEND/REQUEST_MORE_INFO)*
