# Prior Authorization Triage & Policy Companion — Backend API

> **CTS Hackathon | Use Case UC02 — Utilization Management**

A production-ready **FastAPI** backend that evaluates Medicare prior authorization requests by checking procedure and diagnosis codes against CMS National Coverage Determinations (NCDs), Local Coverage Determinations (LCDs), and Billing/Coding Articles — using a hybrid pipeline of **deterministic SQL lookups**, **RAG-based vector search (pgvector)**, and **local LLM evaluation (Qwen3 via LM Studio)**.

---

> ⚠️ **DISCLAIMER**: This API provides policy-matching results **only**. It does **not** constitute clinical advice, a guarantee of insurance coverage, or an actual prior authorization decision. Always verify with the applicable Medicare Administrative Contractor (MAC).

---

## ⚡ Quick Start — Unified CLI (`manage.py`)

No database or complex setup is required for instant mock testing:

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate     # Windows
source .venv/bin/activate # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server (http://localhost:8001)
python manage.py serve

# Run Pytest suite (100 edge cases)
python manage.py test

# Run Live API verification suite
python manage.py test-live
```

---

## 📡 API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/triage` | **Core Adjudication Engine**: Evaluates request against CMS policies |
| `GET` | `/api/v1/policies/search` | Crosswalk search by procedure, diagnosis, state, policy type |
| `GET` | `/api/v1/ncds/{id}` | Get NCD metadata and decision status |
| `GET` | `/api/v1/lcds/{id}` | Get LCD details and associated article IDs |
| `GET` | `/api/v1/articles/{id}` | Get Billing & Coding Article details |
| `GET` | `/api/v1/articles/{id}/icd10-covered` | List covered ICD-10 codes for an article |
| `GET` | `/api/v1/articles/{id}/icd10-noncovered` | List non-covered ICD-10 codes for an article |
| `GET` | `/api/v1/articles/{id}/hcpcs` | List HCPCS/CPT codes for an article |
| `GET` | `/api/v1/health` | Service health status |
| `GET` | `/api/v1/health/db` | Database connectivity & repository mode status |

---

## 🛑 Phase 1 Audit & CMS Limitations

Based on our Phase 1 Audit of the CMS Coverage API integration, the following architectural realities apply to this backend:

### CMS `/v1/search` Limitation
Real-time, runtime fallback querying of CMS policies by HCPCS code is **architecturally impossible**. The CMS `/v1/search` endpoint does not support HCPCS searches and returns 400 errors. Because of this, `CMSCoverageClient.search_by_hcpcs()` is structurally broken in real-world scenarios.

### Failsafe Adjudication
To prevent crashes during cache misses, the `PolicyEvidenceResolver` safely catches missing local data and broken CMS connections. It returns an `UNAVAILABLE` status, which the `TriageService` handles by safely routing the request to `PEND` or `REQUEST_MORE_INFORMATION` rather than hallucinating an approval or outright denying care.

### Roadmap to Phase 2 (Background Sync)
Because real-time runtime fallback is physically impossible, Phase 2 (**Background Synchronization**) is strictly mandatory for production. A background worker (e.g., Celery) must periodically pull CMS data via the official endpoints (`/v1/data/lcd`, `/v1/data/article`) and deeply normalize the data (including populating all `LCDHCPCSCode` and `LCDIcd10Covered` SQL relations) to "pre-warm" the PostgreSQL database overnight.
