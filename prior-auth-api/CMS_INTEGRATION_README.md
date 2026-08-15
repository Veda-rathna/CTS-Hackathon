# CMS Coverage API Integration - Phase 1

This document summarizes the changes made to implement the **Phase 1: CMS Coverage API Runtime Fallback** for the Prior Authorization (PA) system. This serves as a foundation for proceeding with Phase 2 (the Background Synchronization Module).

## What Was Implemented

### 1. CMS API Client (`app/services/cms_client.py`)
We implemented a robust HTTP client specifically for the CMS Medicare Coverage Database (MCD) API:
- **Dynamic Authentication:** The CMS API requires a license agreement token rather than a static API key. The client automatically sends a `GET` request to `/v1/metadata/license-agreement/`, parses the deeply nested JSON (`data[0]["Token"]`), and injects it as a `Bearer` token into subsequent requests.
- **Auto-Renewal:** If a token expires and the API returns a `401 Unauthorized`, the client automatically fetches a new token and retries the request.
- **ID Normalization:** Handled CMS API idiosyncrasies, such as stripping the "L" prefix from LCD IDs (e.g., `L39054` becomes `39054`) before making the request.

### 2. Policy Evidence Resolver (`app/services/policy_evidence_resolver.py`)
This new layer sits between the `TriageService` and the database repositories to handle the "Local-First, CMS-Fallback" logic:
- **Local Lookup:** Queries the local database first for policies matching a given HCPCS/Diagnosis code.
- **API Fallback:** If local data is missing or incomplete, it reaches out to the CMS API.
- **Data Normalization:** Converts the massive, complex JSON responses from CMS into our streamlined `PolicyMatch` Pydantic models.
- **Local Caching:** Pushes the newly retrieved and normalized policy back into the local database via `upsert_policy()` so future requests for the same code are instantly served locally.

### 3. Repository Updates (`app/repositories/...`)
- **Interfaces:** Added an `upsert_policy(policy: PolicyMatch)` method to `app/repositories/interfaces/policy_repository.py`.
- **Mock DB:** Implemented the upsert logic in `MockPolicyRepository` to allow for immediate end-to-end testing without breaking the existing Postgres implementation.

### 4. End-to-End Verification (`scripts/test_cms_normalization.py`)
Created a standalone script that proves the pipeline works:
- Fetches a real token.
- Pulls live data for LCD `L39054`.
- Normalizes it successfully into a `PolicyMatch` object.
- Inserts it into the Mock DB.

---

## Moving Forward: Phase 2 (Background Sync Module)

Now that Phase 1 gives us resilience against missing local data *at runtime*, the next step is to proactively keep the local database up to date without waiting for a user request to trigger a cache miss.

### Requirements for the Sync Module
1. **PostgreSQL Implementation:** 
   Update `app/repositories/postgres/policy_repository.py` to fully implement the `upsert_policy` logic using raw SQL or an ORM like SQLAlchemy, replacing the Mock DB for production.
   
2. **Batch Polling / Orchestration:**
   Create a background worker (e.g., Celery, APScheduler, or a standalone Python daemon) that periodically queries the CMS API `/v1/search` or `/v1/data/lcd` endpoints for newly published or updated policies.
   
3. **Delta Syncing:**
   The sync module should keep track of the `last_updated` date of policies in the local database and only fetch policies from CMS that have been modified since that date.
   
4. **Database Pre-Warming:**
   Instead of pulling policies one-by-one during a PA request, the background sync will "pre-warm" the database overnight, ensuring that the runtime fallback is only triggered for absolute edge cases.
