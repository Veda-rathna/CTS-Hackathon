# Prior Authorization Triage & Policy Companion — Master Documentation

> **CTS Hackathon | Use Case UC02 — Utilization Management**

This document serves as the **single authoritative reference** for the Prior Authorization Triage API. It unifies system architecture, CMS adjudication engine logic, database contracts, and the production gap analysis roadmap into one comprehensive guide.

---

## Table of Contents
- [1. Problem Statement Alignment](#1-problem-statement-alignment)
- [2. System Architecture](#2-system-architecture)
- [3. CMS Adjudication Cascade (Engine Logic)](#3-cms-adjudication-cascade-engine-logic)
- [4. Evidence Fusion & Authority Hierarchy](#4-evidence-fusion--authority-hierarchy)
- [5. Database Schema & Data Contract](#5-database-schema--data-contract)
- [6. RAG Vector Search & LLM Circuit Breaker](#6-rag-vector-search--llm-circuit-breaker)
- [7. UC02 Gaps & Production Roadmap](#7-uc02-gaps--production-roadmap)

---

## 1. Problem Statement Alignment

> *"Before some treatments happen, the insurer has to say yes first — that pre-check is called 'prior authorization' or 'prior auth'. Prototype a system that takes an incoming request, extracts the key clinical and administrative facts, checks it against a configurable coverage rule set, and recommends **approve**, **pend for nurse review**, or **request more information** — with the reasoning shown."*

### Key Fact Extraction & Response Mapping
- **Input Extraction**: Procedure code (HCPCS/CPT), diagnosis codes (ICD-10-CM), state (MAC jurisdiction), patient demographics, clinical notes.
- ** adudication**: Real CMS National Coverage Determinations (NCDs), Local Coverage Determinations (LCDs), and Billing & Coding Articles.
- **3-Tier Decision Output**: `APPROVE`, `PEND`, `REQUEST_MORE_INFORMATION`.
- **Explainability**: Complete audit trace including matched policy IDs, evidence logs, RAG similarity scores, and LLM reasoning.

---

## 2. System Architecture

```
Browser / Frontend / EHR Client
        │  HTTP/JSON
        ▼
┌────────────────────────────────────────────────────────┐
│                  FastAPI Application                   │
│    app/main.py — CORS, Exception Handlers, Routers    │
└───────────────────────┬────────────────────────────────┘
                        │
              ┌─────────▼──────────┐
              │    API Layer       │
              │   app/api/v1/      │  thin routers, no logic
              └─────────┬──────────┘
                        │ FastAPI Depends()
              ┌─────────▼──────────────────────────────────┐
              │            Service Layer                   │
              │  triage_service.py   (Core engine)         │
              │  decision_engine.py  (Final verdict)       │
              │  llm/client.py       (Qwen3 + Circuit Break)│
              │  rag/embedding_service.py                  │
              │  evaluation/multi_evaluator.py             │
              │  evaluation/evidence_fusion.py (Authority) │
              └─────────┬──────────────────────────────────┘
                        │
              ┌─────────▼──────────────────────────────────┐
              │        Repository Interface (ABCs)         │
              └──────┬───────────────────────┬─────────────┘
                     │                       │
         ┌───────────▼────────┐  ┌───────────▼─────────────┐
         │ Mock Repositories  │  │  Postgres Repositories  │
         │ (in-memory, no DB) │  │  (SQLAlchemy + psycopg) │
         └────────────────────┘  │  PolicyChunkRepository  │
                                 │  (pgvector 384d search) │
                                 └───────────┬─────────────┘
                                             │
                                  ┌──────────▼──────────┐
                                  │    PostgreSQL 16    │
                                  │  + pgvector ext.    │
                                  └─────────────────────┘
```

### Module Responsibilities
- **`app/api/v1/`**: Thin FastAPI endpoints (`triage.py`, `ncds.py`, `lcds.py`, `articles.py`, `policies.py`, `health.py`).
- **`app/services/triage_service.py`**: Adjudication cascade orchestrator.
- **`app/services/decision_engine.py`**: Maps internal policy statuses to public enum decisions (`APPROVE`, `PEND`, `REQUEST_MORE_INFORMATION`).
- **`app/services/evaluation/evidence_fusion.py`**: Merges structured and semantic criteria, enforcing authority rules.
- **`app/services/llm/client.py`**: HTTP client for local Qwen LLM via LM Studio with a split timeout circuit breaker (`connect=5s`, `read=20s`).
- **`app/repositories/`**: Repository pattern isolating data access (switchable via `USE_MOCK_REPOSITORIES=true` or `false`).

---

## 3. CMS Adjudication Cascade (Engine Logic)

```
┌─────────────────────────────────────────────────────────────┐
│                   Incoming Triage Request                   │
│   procedure_code  │  diagnosis_codes  │  state  │  notes    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
            ┌────────────────────────────────────┐
            │ 1. Policy Lookup (SQL)             │
            │    Find candidate NCDs & LCDs      │
            └──────────────────┬─────────────────┘
                               │
                               ▼
            ┌────────────────────────────────────┐
            │ 2. National Coverage (NCD)         │
            │    pgvector RAG + LLM + SQL        │
            └──────────────────┬─────────────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       │ COVERED               │ EXCLUDED              │ NOT_ADDRESSED
       ▼                       ▼                       ▼
┌──────────────┐       ┌──────────────┐    ┌──────────────────────┐
│   APPROVE    │       │     PEND     │    │ 3. Jurisdiction Check│
└──────────────┘       └──────────────┘    │    State in MAC zone?│
                                           └───────────┬──────────┘
                                                       │ MATCHED
                                                       ▼
                                           ┌──────────────────────┐
                                           │ 4. Local Rules (LCD) │
                                           │    RAG + LLM + SQL   │
                                           └───────────┬──────────┘
                                                       │ COVERED
                                                       ▼
                                           ┌──────────────────────┐
                                           │ 5. Article Evaluation│
                                           │    ICD-10 SQL Matrix │
                                           └───────────┬──────────┘
                                                       │
                                                       ▼
                                           ┌──────────────────────┐
                                           │ 6. Decision Engine   │
                                           │    APPROVE / PEND /  │
                                           │    REQUEST_MORE_INFO │
                                           └──────────────────────┘
```

### Adjudication Steps
1. **Candidate Policy Retrieval**: Finds NCDs and LCDs matching the requested procedure code. Dates are checked; expired policies return `POLICY_EXPIRED`.
2. **NCD Adjudication**: Evaluates national policies via pgvector RAG (`threshold=0.6`) and LLM criterion classifier.
   - If NCD explicitly covers procedure → `APPROVE`.
   - If NCD explicitly excludes procedure → `PEND`.
   - If NCD is silent or ambiguous for the submitted diagnosis → `NOT_ADDRESSED` (falls through to LCD).
3. **Jurisdiction Check**: Verifies submitted state abbreviation matches the LCD's Medicare Administrative Contractor (MAC) region. If outside jurisdiction → `REQUEST_MORE_INFORMATION`.
4. **LCD Evaluation**: RAG search over active LCD chunks (`threshold=0.8`). If LCD excludes → `PEND`.
5. **Billing & Coding Article Matrix**: SQL validation against `article_icd10_covered` and `article_icd10_noncovered`. If covered diagnosis present → `APPROVE`.

---

## 4. Evidence Fusion & Authority Hierarchy

When combining structured SQL queries and semantic LLM outputs, `EvidenceFusion` enforces:

$$\text{Structured (SQL)} > \text{Rule-based} > \text{Semantic (LLM)}$$

1. **Authoritative SQL Overrides**: A deterministic SQL code match or explicit exclusion ALWAYS takes precedence over LLM text evaluations.
2. **Ambiguous LLM Handling**: If the LLM generates conflicting criteria (e.g., `SATISFIED` for fibromyalgia text + `NOT_SATISFIED` for non-fibromyalgia patient), the NCD layer resolves to `NOT_ADDRESSED` so that local LCD/Article rules can adjudicate cleanly.
3. **LLM Fallback**: If the local LLM service is offline or times out, the client returns `status="UNKNOWN"`, allowing deterministic rules to complete the decision without failing.

---

## 5. Database Schema & Data Contract

### Entity-Relationship Architecture
```
Contractor
    │
    └── 1:N Jurisdiction
              │
              └── 1:N LCD
                    │
                    ├── N:M Article (via LCD-Article association)
                    │         ├── Article ICD-10 Covered Codes
                    │         ├── Article ICD-10 Non-Covered Codes
                    │         └── Article HCPCS Codes
                    │
                    ├── LCD ICD-10 Covered Codes
                    ├── LCD ICD-10 Non-Covered Codes
                    └── LCD HCPCS Codes

NCD (National Coverage Determination, standalone)
    └── NCD HCPCS Crosswalk
```

### Table Definitions
- `ncds`: `ncd_id`, `title`, `effective_date`, `end_date`, `description`, `manual_section`, `decision`.
- `lcds`: `lcd_id`, `title`, `version`, `effective_date`, `end_date`, `jurisdiction_id`, `contractor_id`, `associated_article_ids`.
- `articles`: `article_id`, `title`, `effective_date`, `end_date`, `status`.
- `article_icd10_covered`: `article_id`, `icd10_code`, `description`.
- `article_icd10_noncovered`: `article_id`, `icd10_code`, `description`.
- `article_hcpcs`: `article_id`, `hcpcs_code`, `description`.
- `policy_chunks`: `id`, `policy_id`, `policy_type`, `section`, `chunk_text`, `embedding` (vector(384)).

---

## 6. RAG Vector Search & LLM Circuit Breaker

- **Vector Space**: Embeddings created using SentenceTransformers (`all-MiniLM-L6-v2`, 384 dimensions) and stored in pgvector (`policy_chunks`).
- **Cosine Distance Search**: Vector queries use pgvector's `<=>` operator constrained to policy IDs matching the procedure code.
- **Circuit Breaker**: `httpx.Timeout(connect=5.0, read=20.0, write=5.0, pool=5.0)` prevents long hangs. On `ConnectError` or `TimeoutException`, returns `LLMResponse(status="UNKNOWN")` immediately.

---

## 7. UC02 Gaps & Production Roadmap

### Gap Matrix & Readiness Analysis

| Component | Status | Description & Solution |
|---|---|---|
| **Fact Extraction** | ✅ **Complete** | Standardized Pydantic request schema (`TriageRequest`) with whitespace & case normalization. |
| **Coverage Cascade** | ✅ **Complete** | Full 6-phase adjudication pipeline (NCD → Jurisdiction → LCD → Article). |
| **3-Tier Decision** | ✅ **Complete** | Strictly returns `APPROVE`, `PEND`, or `REQUEST_MORE_INFORMATION`. |
| **Audit Trace** | ✅ **Complete** | Returns detailed evidence chain, RAG chunks, policy paths, and evidence score. |
| **Synthea FHIR Ingestion** | ⚠️ **Partial (85%)** | Accepts free-text notes; native FHIR R4 Bundle parsing planned (`POST /api/v1/triage/fhir`). |
| **Prior Claims History** | ❌ **Roadmap** | Single-encounter payload evaluation; longitudinal prior claims tracking planned for frequency/quantity limits. |
| **Decision Logging DB** | ❌ **Roadmap** | Immutable background audit logger (`triage_audit_logs`) for HIPAA compliance. |
| **HITL Nurse Review** | ❌ **Roadmap** | Review queue endpoints (`/api/v1/review-queue`) for UM nurses to adjudicate `PEND` requests. |
| **50-State MAC Scaling** | ⚠️ **Partial** | Full J5 state mapping (TX, NM, OK, LA, AR, MS, CO); expanding to all 12 MAC regions. |
| **OAuth2 / Security** | ❌ **Roadmap** | Enterprise JWT authentication and tenant isolation (`X-Payer-ID`). |

---

*Unified Master Documentation — Prior Authorization Triage & Policy Companion API*
