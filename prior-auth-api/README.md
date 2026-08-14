# Prior Authorization Triage & Policy Companion — Backend API

> **CTS Hackathon | Use Case UC02 — Utilization Management**

A production-ready **FastAPI** backend that evaluates Medicare prior authorization requests by checking procedure and diagnosis codes against CMS National Coverage Determinations (NCDs), Local Coverage Determinations (LCDs), and Billing/Coding Articles — using a hybrid pipeline of **deterministic SQL lookups**, **RAG-based vector search (pgvector)**, and **local LLM evaluation (Qwen3 via LM Studio)**.

---

> ⚠️ **DISCLAIMER**: This API provides policy-matching results **only**. It does **not** constitute clinical advice, a guarantee of insurance coverage, or an actual prior authorization decision. Always verify with the applicable Medicare Administrative Contractor (MAC).

---

## Table of Contents

- [Problem Statement Alignment](#problem-statement-alignment)
- [Solution Overview](#solution-overview)
- [Master Documentation](#master-documentation)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Environment Configuration](#environment-configuration)
- [Quick Start — Unified CLI (`manage.py`)](#quick-start--unified-cli-managepy)
- [Full Setup — PostgreSQL Mode](#full-setup--postgresql-mode)
- [Docker Setup](#docker-setup)
- [API Endpoints Reference](#api-endpoints-reference)
- [Decision Logic & Authority Hierarchy](#decision-logic--authority-hierarchy)
- [Request & Response Schemas](#request--response-schemas)
- [Running Test Suites](#running-test-suites)
- [Scripts Reference](#scripts-reference)

---

## Problem Statement Alignment

> *"Before some treatments happen, the insurer has to say yes first — that pre-check is called 'prior authorization' or 'prior auth'. Prototype a system that takes an incoming request, extracts the key clinical and administrative facts, checks it against a configurable coverage rule set, and recommends **approve**, **pend for nurse review**, or **request more information** — with the reasoning shown."*

Prior authorization is one of the most friction-heavy processes in healthcare administration. Speed, accuracy, transparency, and auditability all matter simultaneously. This API solves that by implementing the actual CMS adjudication hierarchy in code.

---

## Solution Overview

The engine processes a clinical request through a strict, hierarchical pipeline that mirrors the real CMS adjudication process:

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

---

## Master Documentation

Detailed technical documentation is available in **[`../DOCUMENTATION.md`](../DOCUMENTATION.md)**:

- **System Architecture**: High-level module design, repository patterns, vector models.
- **Engine Deep Dive**: Detailed breakdown of the CMS Coverage Cascade & Evidence Fusion rules.
- **Data Integration Contract**: Entity-relationship schema (Contractor → Jurisdiction → LCD → Article).
- **UC02 Gaps & Production Roadmap**: Gap matrix (Synthea FHIR ingestion, longitudinal prior claims, HITL nurse review queue, 50-state MAC scaling) and 3-phase enterprise deployment roadmap.

---

## Technology Stack

| Component | Technology | Version |
|---|---|---|
| Web Framework | FastAPI | 0.115.5 |
| ASGI Server | Uvicorn | 0.32.1 |
| Data Validation | Pydantic v2 | 2.10.3 |
| Settings Management | pydantic-settings | 2.6.1 |
| ORM | SQLAlchemy | 2.0.36 |
| Database Driver | psycopg (v3) | 3.2.3 |
| Migrations | Alembic | 1.14.0 |
| Vector Search | pgvector | 0.3.6 |
| Embeddings Model | sentence-transformers (`all-MiniLM-L6-v2`) | 3.4.1 |
| LLM Runtime | LM Studio (local) + Qwen3-4B | — |
| LLM HTTP Client | httpx | 0.28.0 |
| Testing | pytest + pytest-asyncio | 8.3.4 |
| Containerization | Docker + Docker Compose | — |
| Database | PostgreSQL 16 with pgvector extension | — |

---

## System Architecture

```
Browser / Frontend / EHR / Client
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

---

## Project Structure

```
prior-auth-api/
├── manage.py                     ← CENTRAL CLI RUNNER (serve, test, setup-db, test-live)
├── app/
│   ├── api/v1/                   # REST Route Handlers (triage, policies, articles, lcds, ncds, health)
│   ├── core/                     # Application Settings & Configuration
│   ├── db/                       # SQLAlchemy Session & Engine
│   ├── models/                   # ORM Models (NCD, LCD, Article, PolicyChunk)
│   ├── schemas/                  # Pydantic Input/Output Contracts
│   ├── services/                 # Business Logic & Engine (TriageService, DecisionEngine, EvidenceFusion)
│   └── repositories/             # Interface, Mock, and Postgres Repositories
├── scripts/                      # Streamlined Data & Test Utility Scripts
│   ├── db_setup.py               # Unified DB Init + Seeding + pgvector Embedding Ingestion
│   ├── test_live.py              # Unified Live API Verification Suite
│   ├── fetch_ncd_hcpcs.py        # CMS API harvester
│   ├── seed_db.py                # Database seeder
│   └── test_icd_prefix_requests.py # Systematic ICD prefix benchmark
├── tests/                        # 68 Pytest Unit & Integration Tests
│   ├── test_triage_engine.py     # Master Adjudication Engine & Edge Case Tests (46 tests)
│   └── test_domain_routers.py    # Master Domain Router Endpoint Tests (22 tests)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Environment Configuration

```bash
copy .env.example .env   # Windows
cp .env.example .env     # Linux/macOS
```

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `Prior Authorization Triage API` | Display name |
| `APP_VERSION` | `1.0.0` | API version |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/prior_auth` | Database connection |
| `USE_MOCK_REPOSITORIES` | `true` | `true` = in-memory mode, `false` = real PostgreSQL |
| `LLM_ENABLED` | `true` | Enable/disable LLM semantic criteria evaluation |
| `LLM_BASE_URL` | `http://127.0.0.1:1234/v1` | Local LLM server endpoint |
| `LLM_MODEL` | `qwen/qwen3-4b-2507` | Model identifier |

---

## Quick Start — Unified CLI (`manage.py`)

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

# Run Pytest suite (68 tests)
python manage.py test

# Run Live API verification suite
python manage.py test-live
```

---

## Full Setup — PostgreSQL Mode

```bash
# 1. Start PostgreSQL with pgvector via Docker
docker run -d \
  --name prior-auth-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=prior_auth \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# 2. Update .env
# Set USE_MOCK_REPOSITORIES=false

# 3. Run single-command DB setup (migrations + pgvector init + seeding + vector ingestion)
python manage.py setup-db
```

---

## API Endpoints Reference

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

## Decision Logic & Authority Hierarchy

The `DecisionEngine` returns one of three public decision states:

- **`APPROVE`**: Valid covered diagnosis matched in Article list, or NCD/LCD criteria satisfied.
- **`PEND`**: Explicit policy exclusion (`NCD_EXCLUDES_PROCEDURE`, `LCD_EXCLUDES_PROCEDURE`, `ARTICLE_EXCLUDES_PROCEDURE`) or ambiguous evidence requiring nurse review.
- **`REQUEST_MORE_INFORMATION`**: Procedure not found in policies, diagnosis not in any list, state outside jurisdiction, or missing required fields.

---

## Request & Response Schemas

### Request (`POST /api/v1/triage`)
```json
{
  "procedure_code": "64483",
  "diagnosis_codes": ["M54.16"],
  "state": "TX",
  "patient_age": 55,
  "clinical_notes": "Patient presents with chronic lumbar radiculopathy."
}
```

### Response (`200 OK`)
```json
{
  "decision": "APPROVE",
  "evidence_score": 1.0,
  "requires_prior_authorization": true,
  "reason": "Procedure code '64483' is covered under Article A12345.",
  "reason_codes": ["ARTICLE_CRITERIA_SATISFIED"],
  "policies": [
    {
      "policy_type": "LCD",
      "policy_id": "L39054",
      "title": "Epidural Injections for Pain Management",
      "article_id": "A12345"
    }
  ],
  "policy_path": {
    "ncd": {"policy_id": null, "result": "NOT_ADDRESSED"},
    "jurisdiction": {"state": "TX", "result": "MATCHED"},
    "lcd": {"policy_id": "L39054", "result": "COVERED"},
    "article": {"policy_id": "A12345", "result": "COVERED"}
  },
  "matched_codes": {
    "procedure": "64483",
    "diagnosis": ["M54.16"]
  },
  "evidence": [
    {"type": "HCPCS", "identifier": "A12345", "code": "64483", "result": "MATCHED", "explanation": "Procedure code '64483' is listed in article A12345."},
    {"type": "ICD10", "identifier": "A12345", "code": "M54.16", "result": "COVERED", "explanation": "Diagnosis code 'M54.16' is listed as covered in article A12345."},
    {"type": "JURISDICTION", "identifier": "J5", "state": "TX", "result": "MATCHED", "explanation": "State 'TX' matches jurisdiction of LCD L39054."}
  ]
}
```

---

## Running Test Suites

```bash
python manage.py test
```

Result: **68 tests passing in ~9.8s**.

---

*CTS Hackathon — Use Case UC02 Utilization Management Solution*
