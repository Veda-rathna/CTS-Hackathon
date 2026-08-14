# Prior Authorization Triage & Policy Companion (CTS Hackathon)

> **Use Case UC02 — Utilization Management**

A production-ready **FastAPI** backend solution that evaluates Medicare prior authorization requests against official CMS coverage policies using a hybrid adjudication architecture: **Deterministic SQL lookups**, **pgvector RAG vector search**, and **local LLM semantic criterion evaluation (Qwen3 via LM Studio)**.

---

## 📋 Problem Statement (UC02)

> **"Before some treatments happen, the insurer has to say yes first — that pre-check is called 'prior authorization' or 'prior auth'. Prototype a system that takes an incoming request, extracts the key clinical and administrative facts, checks it against a configurable coverage rule set, and recommends approve, pend for nurse review, or request more information — with the reasoning shown."**

### The Challenge
Prior authorization decides whether a requested service meets a health plan's coverage and medical necessity rules before care is delivered. It is one of the most scrutinized payer-provider friction points today because **speed, accuracy, transparency, and experience** (member & provider) all matter simultaneously.

### Solution Requirements
- **Fact Extraction**: Procedure code (HCPCS/CPT), diagnosis codes (ICD-10-CM), state (MAC jurisdiction), patient demographics, clinical notes.
- **Coverage Rule Set**: CMS Medicare Coverage Database (National Coverage Determinations [NCD], Local Coverage Determinations [LCD], Billing/Coding Articles [LCA]).
- **3-Tier Decision Engine**: Recommends `APPROVE`, `PEND` (for nurse review), or `REQUEST_MORE_INFORMATION`.
- **Explainability & Transparency**: Complete evidence audit trace showing matched policies, RAG similarity scores, and LLM reasoning.

---

## 🛠️ Hybrid Architecture & Adjudication Pipeline

Our engine mirrors the official CMS adjudication hierarchy, enforced by a **deterministic + RAG + LLM cascade**:

```
                               ┌─────────────────────────┐
                               │   Prior Auth Request    │
                               │  CPT, ICD10, State, Notes│
                               └────────────┬────────────┘
                                            │
                                            ▼
                              ┌───────────────────────────┐
                              │ 1. Policy Lookup (SQL)    │
                              │    Find Candidate NCD/LCD │
                              └─────────────┬─────────────┘
                                            │
                                            ▼
                              ┌───────────────────────────┐
                              │ 2. NCD Evaluation         │
                              │    pgvector RAG + LLM     │
                              └─────────────┬─────────────┘
                                            │
               ┌────────────────────────────┼────────────────────────────┐
               │ COVERED                    │ EXCLUDED                   │ NOT_ADDRESSED
               ▼                            ▼                            ▼
        ┌──────────────┐             ┌──────────────┐        ┌───────────────────────┐
        │   APPROVE    │             │     PEND     │        │ 3. Jurisdiction Check │
        └──────────────┘             └──────────────┘        │    State in MAC Zone? │
                                                             └───────────┬───────────┘
                                                                         │ MATCHED
                                                                         ▼
                                                             ┌───────────────────────┐
                                                             │ 4. LCD Evaluation     │
                                                             │    RAG + LLM + SQL    │
                                                             └───────────┬───────────┘
                                                                         │ COVERED
                                                                         ▼
                                                             ┌───────────────────────┐
                                                             │ 5. Article Evaluation │
                                                             │    ICD-10 Code Matrix │
                                                             └───────────┬───────────┘
                                                                         │
                                                                         ▼
                                                             ┌───────────────────────┐
                                                             │ 6. Decision Engine    │
                                                             │    APPROVE / PEND /   │
                                                             │    REQUEST_MORE_INFO  │
                                                             └───────────────────────┘
```

### Key Technical Pillars

1. **CMS Adjudication Cascade**:
   - **NCD Override (First Priority)**: National policies take precedence. If an NCD explicitly covers or excludes the procedure for the diagnosis, adjudication halts early.
   - **MAC Jurisdiction Verification (Second Priority)**: Validates state abbreviations against regional Medicare Administrative Contractor (MAC) jurisdictions.
   - **LCD Evaluation (Third Priority)**: RAG vector search over active Local Coverage Determinations.
   - **Article ICD-10 Matrix (Fourth Priority)**: Deterministic SQL validation against `article_icd10_covered` and `article_icd10_noncovered` code lists.

2. **Authority Hierarchy in Evidence Fusion**:
   $$\text{Structured (SQL)} > \text{Rule-based} > \text{Semantic (LLM)}$$
   - Authoritative SQL code checks **always** override LLM outputs.
   - LLM `UNKNOWN` results pass through to secondary policy layers without causing false rejections.
   - Timeout circuit breaker (5s connect / 20s read) prevents server hangs if the LLM is offline.

3. **Repository Pattern (Mock & PostgreSQL Modes)**:
   - Toggle `USE_MOCK_REPOSITORIES=true` for instant in-memory execution without a database.
   - Toggle `USE_MOCK_REPOSITORIES=false` for full PostgreSQL + pgvector vector search.

---

## ⚡ Quick Start

### 1. Unified CLI Runner (`manage.py`)

Navigate to `prior-auth-api` and use `manage.py` for all tasks:

```bash
cd prior-auth-api

# Create & activate environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI dev server (port 8001)
python manage.py serve

# Run Pytest suite
python manage.py test

# Run Live API verification test suite
python manage.py test-live

# Full Database Setup (Init pgvector → Seed CMS data → Ingest RAG embeddings)
python manage.py setup-db
```

### 2. Interactive Documentation & Endpoints

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **API Health Check**: `GET http://localhost:8001/api/v1/health`
- **Core Triage Endpoint**: `POST http://localhost:8001/api/v1/triage`

---

## 📂 Project Directory Structure

```
CTS-Hackathon/
├── DOCUMENTATION.md            # MASTER TECHNICAL DOCUMENTATION (Architecture + Adjudication + Roadmap)
├── README.md                   # Workspace root README (this file)
└── prior-auth-api/             # FastAPI Application Root
    ├── manage.py               # CENTRAL CLI RUNNER (serve, test, setup-db, test-live)
    ├── app/
    │   ├── api/v1/             # REST Endpoints (triage, policies, articles, lcds, ncds, health)
    │   ├── schemas/            # Strict Pydantic Data Contracts (TriageRequest, TriageResponse)
    │   ├── services/           # Adjudication Cascade, Decision Engine, Evidence Fusion
    │   ├── repositories/       # Data Access Interfaces (Mock & Postgres implementations)
    │   ├── models/             # SQLAlchemy ORM Data Models (NCD, LCD, Article, PolicyChunk)
    │   ├── core/               # Pydantic BaseSettings & Logging configuration
    │   └── db/                 # Database engine & session factory
    ├── scripts/                # Utility & Test Scripts
    │   ├── db_setup.py         # Unified DB Init + Seeding + pgvector Embedding Ingestion
    │   └── test_live.py        # Unified Live API Verification Suite
    ├── tests/                  # Streamlined Pytest Test Suite
    │   ├── test_triage_engine.py # Master Adjudication Engine & Edge Case Tests (46 tests)
    │   └── test_domain_routers.py # Master Domain Router Endpoint Tests (22 tests)
    ├── Dockerfile
    ├── docker-compose.yml
    └── requirements.txt
```

---

## 📖 Master Documentation Reference

For detailed technical explanations, refer to **[`prior-auth-api/DOCUMENTATION.md`](prior-auth-api/DOCUMENTATION.md)**:
- **System Architecture**: High-level module diagrams, repository pattern, and service graph.
- **Engine Deep Dive**: Detailed breakdown of the 6-step CMS coverage cascade.
- **Data Integration Contract**: Entity-relationship schema (Contractor → Jurisdiction → LCD → Article).
- **UC02 Gaps & Production Roadmap**: Gap matrix (Synthea FHIR ingestion, longitudinal prior claims, HITL nurse review queue, 50-state MAC scaling) and 3-phase enterprise deployment roadmap.

---

*CTS Hackathon — Use Case UC02 Utilization Management Solution*