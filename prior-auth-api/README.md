# Prior Authorization Triage & Policy Companion — Backend API

> **CTS Hackathon | Use Case UC02 — Utilization Management**

A production-ready **FastAPI** backend that evaluates Medicare prior authorization requests by checking procedure and diagnosis codes against CMS National Coverage Determinations (NCDs), Local Coverage Determinations (LCDs), and Billing/Coding Articles — using a hybrid pipeline of **deterministic SQL lookups**, **RAG-based vector search (pgvector)**, and **local LLM evaluation (Qwen3 via LM Studio)**.

---

> ⚠️ **DISCLAIMER**: This API provides policy-matching results **only**. It does **not** constitute clinical advice, a guarantee of insurance coverage, or an actual prior authorization decision. Always verify with the applicable Medicare Administrative Contractor (MAC).

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Solution Overview](#solution-overview)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Environment Configuration](#environment-configuration)
- [Quick Start — Mock Mode](#quick-start--mock-mode-no-database)
- [Full Setup — PostgreSQL Mode](#full-setup--postgresql-mode)
- [Docker Setup](#docker-setup)
- [LM Studio Setup](#lm-studio-setup-local-llm)
- [Database Seeding & Vector Ingestion](#database-seeding--vector-ingestion)
- [API Endpoints Reference](#api-endpoints-reference)
- [Triage Pipeline — Step by Step](#triage-pipeline--step-by-step)
- [Decision Logic](#decision-logic)
- [Evaluator Strategies](#evaluator-strategies)
- [Request & Response Schema](#request--response-schema)
- [Mock Data Reference](#mock-data-reference)
- [Running Tests](#running-tests)
- [Scripts Reference](#scripts-reference)
- [Database Schema](#database-schema)
- [Privacy & Security Notes](#privacy--security-notes)

---

## Problem Statement

> *"Before some treatments happen, the insurer has to say yes first — that pre-check is called 'prior authorization'. Prototype a system that takes an incoming request, extracts key clinical and administrative facts, checks it against a configurable coverage rule set, and recommends **approve**, **pend for nurse review**, or **request more information** — with the reasoning shown."*

Prior authorization is one of the most friction-heavy processes in healthcare administration. Speed, accuracy, transparency, and auditability all matter simultaneously. This API solves that by implementing the actual CMS adjudication hierarchy in code.

---

## Solution Overview

The engine processes a clinical request through a strict, hierarchical pipeline that mirrors the real CMS adjudication process:

```
┌────────────────────────────────────────────────────┐
│               Prior Auth Request                   │
│  procedure_code + diagnosis_codes + state + notes  │
└────────────────────────┬───────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────┐
          │   1. Find Candidate      │
          │   Policies (SQL)         │
          │   NCD + LCD for HCPCS    │
          └──────────┬───────────────┘
                     │
          ┌──────────▼───────────────┐
          │   2. NCD Evaluation      │ ── COVERED  → APPROVE
          │   RAG + LLM + SQL        │ ── EXCLUDED → PEND
          └──────────┬───────────────┘
                     │ NOT_ADDRESSED
          ┌──────────▼───────────────┐
          │   3. Jurisdiction Check  │ ── state NOT in zone → REQUEST_MORE_INFO
          │   state in LCD zone?     │
          └──────────┬───────────────┘
                     │ MATCHED
          ┌──────────▼───────────────┐
          │   4. LCD Evaluation      │ ── EXCLUDED → PEND
          │   RAG + LLM + SQL        │
          └──────────┬───────────────┘
                     │ COVERED
          ┌──────────▼───────────────┐
          │   5. Article Evaluation  │
          │   HCPCS check (SQL)      │
          │   ICD-10 check (SQL)     │
          └──────────┬───────────────┘
                     │
          ┌──────────▼───────────────┐
          │   6. Decision Engine     │
          │   APPROVE / PEND /       │
          │   REQUEST_MORE_INFO      │
          └──────────────────────────┘
```

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
| Embeddings Model | sentence-transformers (all-MiniLM-L6-v2) | 3.4.1 |
| LLM Runtime | LM Studio (local) + Qwen3-4B | — |
| LLM HTTP Client | httpx | 0.28.0 |
| HTML Parser | BeautifulSoup4 | 4.12.3 |
| Testing | pytest + pytest-asyncio | 8.3.4 |
| Containerization | Docker + Docker Compose | — |
| Database | PostgreSQL 16 with pgvector extension | — |

---

## System Architecture

```
Browser / Frontend (React / Streamlit / Postman)
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
              │            Service Layer                    │
              │  triage_service.py   (12-phase engine)      │
              │  decision_engine.py  (final verdict)        │
              │  llm/client.py       (Qwen3 via LM Studio)  │
              │  rag/embedding_service.py                   │
              │  rag/document_processor.py                  │
              │  evaluation/multi_evaluator.py              │
              │  evaluation/structured_evaluator.py (SQL)   │
              │  evaluation/rule_evaluator.py    (Regex)    │
              │  evaluation/semantic_evaluator.py  (LLM)    │
              │  evaluation/evidence_fusion.py              │
              └─────────┬──────────────────────────────────┘
                        │
              ┌─────────▼──────────────────────────────────┐
              │        Repository Interface (ABCs)          │
              └──────┬───────────────────────┬─────────────┘
                     │                       │
         ┌───────────▼────────┐  ┌───────────▼─────────────┐
         │ Mock Repositories  │  │  Postgres Repositories   │
         │ (in-memory, no DB) │  │  (SQLAlchemy + psycopg)  │
         └────────────────────┘  │  PolicyChunkRepository   │
                                 │  (pgvector cosine search)│
                                 └───────────┬─────────────┘
                                             │
                                  ┌──────────▼──────────┐
                                  │    PostgreSQL 16     │
                                  │  + pgvector ext.     │
                                  │  ncds, lcds,         │
                                  │  articles,           │
                                  │  policy_chunks       │
                                  │  (384-dim vectors)   │
                                  └─────────────────────┘
```

**Key Design Principle**: Switching between Mock and PostgreSQL only requires one env var change (`USE_MOCK_REPOSITORIES`). No routes, schemas, or services need to change.

---

## Project Structure

```
prior-auth-api/
│
├── app/                                  ← Python application package
│   ├── main.py                           ← FastAPI app entry point
│   │
│   ├── api/v1/                           ← HTTP Route Handlers (no logic)
│   │   ├── router.py                     ← Aggregates all sub-routers
│   │   ├── triage.py                     ← POST /triage  ← CORE ENDPOINT
│   │   ├── articles.py                   ← GET /articles/{id}/*
│   │   ├── lcds.py                       ← GET /lcds/{id}
│   │   ├── ncds.py                       ← GET /ncds/{id}
│   │   ├── policies.py                   ← GET /policies/search
│   │   └── health.py                     ← GET /health, /health/db
│   │
│   ├── core/
│   │   ├── config.py                     ← Settings class (reads .env, LRU cached)
│   │   └── logging.py                    ← Standard logging setup
│   │
│   ├── db/
│   │   ├── session.py                    ← SQLAlchemy engine + get_db() dependency
│   │   └── base.py                       ← Imports all models for Alembic
│   │
│   ├── models/                           ← SQLAlchemy ORM (database tables)
│   │   ├── base.py                       ← DeclarativeBase
│   │   ├── ncd.py                        ← NCD, NCDHCPCSCode, LCDNCDAssociation
│   │   ├── lcd.py                        ← LCD, LCDHCPCSCode, LCDIcd10Covered/NonCovered
│   │   ├── article.py                    ← Article, ArticleHcpcsCode, ArticleIcd10*
│   │   ├── policy_chunk.py               ← PolicyChunk (pgvector, 384-dim embedding)
│   │   ├── contractor.py                 ← Contractor (Medicare Admin Contractors)
│   │   ├── jurisdiction.py               ← Jurisdiction + JurisdictionState
│   │   └── state.py                      ← US State lookup
│   │
│   ├── schemas/                          ← Pydantic models (API contracts)
│   │   ├── triage.py                     ← TriageRequest, TriageResponse, TriageDecision
│   │   ├── evaluation.py                 ← EvaluatedCriterion, CriterionType, EvaluationStatus
│   │   ├── policy.py                     ← PolicyMatch (internal)
│   │   ├── article.py                    ← ArticleDetail response
│   │   ├── lcd.py                        ← LCDDetail response
│   │   ├── ncd.py                        ← NCDDetail response
│   │   └── common.py                     ← Shared pagination models
│   │
│   ├── services/                         ← Business Logic Layer
│   │   ├── triage_service.py             ← 12-PHASE TRIAGE ENGINE (core of project)
│   │   ├── decision_engine.py            ← Maps NCD+LCD+Article results → final verdict
│   │   ├── article_service.py            ← Article lookup wrapper
│   │   ├── lcd_service.py                ← LCD lookup wrapper
│   │   ├── ncd_service.py                ← NCD lookup wrapper
│   │   ├── policy_service.py             ← Policy search wrapper
│   │   │
│   │   ├── llm/
│   │   │   └── client.py                 ← LLMClient → Qwen3 via LM Studio HTTP API
│   │   │
│   │   ├── rag/
│   │   │   ├── embedding_service.py      ← Sentence-Transformers (384-dim)
│   │   │   └── document_processor.py    ← HTML→text→chunks (NCD/LCD ingestion)
│   │   │
│   │   └── evaluation/
│   │       ├── criterion_extractor.py    ← Regex: bullets + phrases from chunks
│   │       ├── criterion_classifier.py   ← STRUCTURED / RULE_BASED / SEMANTIC
│   │       ├── multi_evaluator.py        ← Strategy router
│   │       ├── structured_evaluator.py   ← SQL code-list checks (deterministic)
│   │       ├── rule_evaluator.py         ← Age/date rules (deterministic regex)
│   │       ├── semantic_evaluator.py     ← Delegates to LLMClient
│   │       └── evidence_fusion.py        ← Merges criteria → coverage decision
│   │
│   ├── repositories/                     ← Data Access Layer
│   │   ├── interfaces/                   ← Abstract base classes
│   │   │   ├── article_repository.py
│   │   │   ├── lcd_repository.py
│   │   │   ├── ncd_repository.py
│   │   │   └── policy_repository.py
│   │   ├── postgres/                     ← Real PostgreSQL implementations
│   │   │   ├── article_repository.py
│   │   │   ├── lcd_repository.py
│   │   │   ├── ncd_repository.py
│   │   │   └── policy_repository.py
│   │   ├── mock/                         ← In-memory demo implementations
│   │   │   ├── article_repository.py
│   │   │   ├── lcd_repository.py
│   │   │   ├── ncd_repository.py
│   │   │   └── policy_repository.py
│   │   └── policy_chunk_repository.py    ← pgvector cosine-distance search
│   │
│   ├── dependencies/
│   │   └── repositories.py               ← FastAPI DI wiring (full service graph)
│   │
│   └── exceptions/
│       └── handlers.py                   ← 400/404/500 JSON error responses
│
├── alembic/                              ← Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── scripts/                              ← Standalone utility scripts
│   ├── seed_db.py                        ← Seeds PostgreSQL with real CMS data (25KB)
│   ├── ingest_ncds.py                    ← RAG ingestion: chunks + embeddings → DB
│   ├── init_vector_db.py                 ← Installs pgvector, creates policy_chunks
│   ├── fetch_ncd_hcpcs.py                ← Fetches NCD HCPCS codes from CMS
│   ├── generate_mock_ncds.py             ← Generates synthetic NCD test data
│   ├── find_icd_codes.py                 ← Find ICD-10 codes by prefix in DB
│   ├── find_chunks.py                    ← Inspect ingested vector chunks
│   ├── validate_db.py                    ← DB content validation + row counts
│   ├── debug_lmstudio.py                 ← Test LM Studio connectivity
│   ├── test_icd_prefix_requests.py       ← Live API ICD-10 prefix tests (21KB)
│   ├── test_e2e.py                       ← End-to-end integration test
│   ├── test_llm.py                       ← LLM client connectivity test
│   ├── test_live_qwen.py                 ← Live Qwen model evaluation test
│   └── test_llm_scenarios.py             ← Multiple LLM scenario tests
│
├── tests/                                ← Pytest test suite (mock-based)
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_articles.py
│   ├── test_lcds.py
│   ├── test_ncds.py
│   ├── test_policies.py
│   ├── test_triage.py
│   └── test_rag_pipeline.py
│
├── docs/
│   ├── engine_explanation.md             ← Deep-dive: adjudication logic
│   ├── data-contract.md                  ← DB integration guide for data team
│   └── walkthrough.md
│
├── .env                                  ← Local secrets (not committed to git)
├── .env.example                          ← Template for all env variables
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── alembic.ini
```

---

## Environment Configuration

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

### All Environment Variables

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `Prior Authorization Triage API` | Application display name |
| `APP_VERSION` | `1.0.0` | API version string |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/prior_auth` | PostgreSQL connection |
| `USE_MOCK_REPOSITORIES` | `true` | `true` = in-memory, no DB needed. `false` = real PostgreSQL |
| `API_V1_PREFIX` | `/api/v1` | Base path prefix for all routes |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Comma-separated allowed CORS origins |
| `LOG_LEVEL` | `INFO` | Python logging level (`DEBUG`/`INFO`/`WARNING`/`ERROR`) |
| `LLM_ENABLED` | `true` | Enable or disable LLM calls |
| `LLM_PROVIDER` | `lmstudio` | LLM backend identifier |
| `LLM_BASE_URL` | `http://127.0.0.1:1234/v1` | LM Studio OpenAI-compatible endpoint |
| `LLM_MODEL` | `qwen/qwen3-4b-2507` | Model identifier to call |
| `LLM_TEMPERATURE` | `0.0` | Temperature (0.0 = fully deterministic) |

---

## Quick Start — Mock Mode (No Database)

The fastest way to run the project. **No PostgreSQL or LM Studio required.**

### Step 1 — Clone & navigate

```bash
git clone <repo-url>
cd CTS-Hackathon/prior-auth-api
```

### Step 2 — Create virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure environment

```bash
copy .env.example .env   # Windows
cp .env.example .env     # Linux/macOS
```

Ensure `USE_MOCK_REPOSITORIES=true` in `.env` (this is the default).

### Step 5 — Run the server

```bash
uvicorn app.main:app --reload
```

### Step 6 — Test it

```bash
curl -X POST http://localhost:8000/api/v1/triage \
  -H "Content-Type: application/json" \
  -d "{\"procedure_code\":\"64483\",\"diagnosis_codes\":[\"M54.16\"],\"state\":\"TX\",\"patient_age\":65}"
```

Expected: `"decision": "APPROVE"` with full evidence trace.

### Step 7 — Interactive docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Full Setup — PostgreSQL Mode

### Prerequisites
- PostgreSQL 16 with the **pgvector** extension
- LM Studio running locally with Qwen3-4B loaded (optional)

### Step 1 — Start PostgreSQL (Docker)

```bash
docker run -d \
  --name prior-auth-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=prior_auth \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### Step 2 — Update `.env`

```env
USE_MOCK_REPOSITORIES=false
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/prior_auth
LLM_ENABLED=true
LLM_BASE_URL=http://127.0.0.1:1234/v1
LLM_MODEL=qwen/qwen3-4b-2507
```

### Step 3 — Run database migrations

```bash
alembic upgrade head
```

### Step 4 — Initialize vector database

```bash
python scripts/init_vector_db.py
```

### Step 5 — Seed with CMS data

```bash
python scripts/seed_db.py
```

### Step 6 — Ingest policy documents (RAG)

```bash
python scripts/ingest_ncds.py
```

Chunks NCD/LCD documents, generates 384-dim embeddings, inserts into `policy_chunks`.

### Step 7 — Run the server

```bash
uvicorn app.main:app --reload
```

---

## Docker Setup

### Run the full stack

```bash
docker compose up --build
```

Starts:
- **API** at http://localhost:8000 (mock mode by default)
- **PostgreSQL** at port 5432

### Switch to PostgreSQL in Docker

```bash
USE_MOCK_REPOSITORIES=false docker compose up --build
```

Then run migrations and seeding:

```bash
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed_db.py
docker compose exec api python scripts/ingest_ncds.py
```

### Generate a new migration

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

---

## LM Studio Setup (Local LLM)

The semantic evaluator uses a locally running LLM to evaluate narrative policy criteria against patient clinical notes.

### Step 1 — Download LM Studio
https://lmstudio.ai/

### Step 2 — Download Qwen3-4B
Search for `qwen/qwen3-4b-2507` in LM Studio's model browser and download.

### Step 3 — Start the local server
Go to the **Local Server** tab in LM Studio and click **Start Server** (default port: `1234`).

### Step 4 — Verify connectivity

```bash
python scripts/debug_lmstudio.py
```

### Step 5 — Test live evaluation

```bash
python scripts/test_live_qwen.py
```

> **If LM Studio is unavailable**: Set `LLM_ENABLED=false`. Semantic criteria will return `UNKNOWN` (safe fallback) and the engine still works deterministically via SQL + rules.

---

## Database Seeding & Vector Ingestion

```bash
# Validate DB state
python scripts/validate_db.py

# Find ICD-10 codes by prefix in DB
python scripts/find_icd_codes.py

# Inspect vector chunks
python scripts/find_chunks.py

# Generate mock NCD test data
python scripts/generate_mock_ncds.py

# Fetch NCD HCPCS mappings from CMS
python scripts/fetch_ncd_hcpcs.py
```

---

## API Endpoints Reference

All endpoints are prefixed with `/api/v1`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/triage` | **Core endpoint** — run prior auth triage |
| `GET` | `/health` | Application health check |
| `GET` | `/health/db` | Database connectivity check |
| `GET` | `/articles/{article_id}` | Get CMS Article by ID |
| `GET` | `/articles/{article_id}/hcpcs` | Get HCPCS/CPT codes for an article |
| `GET` | `/articles/{article_id}/icd10-covered` | Get covered ICD-10 codes |
| `GET` | `/articles/{article_id}/icd10-noncovered` | Get explicitly non-covered ICD-10 codes |
| `GET` | `/lcds/{lcd_id}` | Get LCD (Local Coverage Determination) |
| `GET` | `/ncds/{ncd_id}` | Get NCD (National Coverage Determination) |
| `GET` | `/policies/search?procedure_code=&state=` | Search policies by procedure + state |

---

## Triage Pipeline — Step by Step

The `TriageService.evaluate()` method implements a **12-phase pipeline**:

### Phase 1 — Input Normalization
Procedure and diagnosis codes uppercased and stripped. State uppercased.

### Phase 2 — Query Embedding
Combines `procedure + diagnoses + clinical_notes` → runs through `sentence-transformers/all-MiniLM-L6-v2` → 384-dim float vector for all RAG searches.

### Phase 3 — Policy Discovery
`PolicyRepository.find_policies_for_procedure(code)` — queries:
- `ncd_hcpcs_codes` → direct NCD match
- `lcd_hcpcs_codes` + `lcd_ncd_associations` → local-to-national bridge
Returns list of `PolicyMatch` objects. If none → `REQUEST_MORE_INFORMATION`.

### Phase 4 — Date Filtering
Removes expired policies (`end_date < today`). Keeps latest version per `policy_id`. If all expired → `POLICY_EXPIRED`.

### Phase 5 — NCD Vector Search (RAG)
pgvector cosine distance search restricted to NCD candidate IDs. Threshold 0.8. Returns top-5 semantically similar chunks.

### Phase 6 — NCD Criterion Extraction
`CriterionExtractor.extract_from_chunk()` — regex parsing:
- Bullet points: `[-*•]` and `1.` style lists
- Requirement phrases: `"documentation must demonstrate..."`, `"patient has..."`, etc.
- Fallback: whole chunk if < 500 chars

### Phase 7 — NCD Criterion Classification
`CriterionClassifier.classify()` assigns:
- `STRUCTURED` — code/list references → SQL evaluator
- `RULE_BASED` — age, date conditions → Rule evaluator
- `SEMANTIC` — narrative clinical language → LLM evaluator

### Phase 8 — NCD Strategy Evaluation
`MultiEvaluator.evaluate()` dispatches to:
- **StructuredEvaluator** — SQL code table lookups (deterministic)
- **RuleEvaluator** — regex age/date comparison (deterministic)
- **SemanticEvaluator** — `LLMClient.evaluate_criterion()` → Qwen3 returns `SATISFIED/NOT_SATISFIED/UNKNOWN`

### Phase 9 — NCD Evidence Fusion
`EvidenceFusion.resolve_decision()` authority hierarchy:
- Any mandatory `NOT_SATISFIED` → `EXCLUDED` (immediate)
- Any `UNKNOWN` → `UNKNOWN`
- Any `SATISFIED` → `COVERED`
- Empty → `NOT_ADDRESSED`
- Fallback: if no RAG chunks, checks `NCD.decision` string field directly

### Phase 10 — Jurisdiction Check
If `ncd_result == NOT_ADDRESSED`: validates submitted `state` against LCD jurisdiction via SQL join: `state → JurisdictionState → Jurisdiction → LCD`. No match → `REQUEST_MORE_INFORMATION`.

### Phase 11 — LCD Evaluation
Same RAG → Extract → Classify → Evaluate → Fuse pipeline applied to the jurisdiction-matched LCD.

### Phase 12 — Article Evaluation (Deterministic SQL)
Only if `lcd_result == COVERED` and LCD has an `article_id`:
- **HCPCS check**: `procedure_code in {article_hcpcs_codes}` → `SATISFIED/NOT_SATISFIED`
- **ICD-10 check**: each diagnosis code checked against `covered_set` and `noncovered_set`

---

## Decision Logic

| Condition | Final Decision |
|---|---|
| `missing` list non-empty | `REQUEST_MORE_INFORMATION` |
| `ncd_result == EXCLUDED` | `PEND` + warning |
| `lcd_result == EXCLUDED` | `PEND` + warning |
| `article_result == EXCLUDED` | `PEND` + warning |
| Any result `UNKNOWN` | `PEND` (ambiguous) |
| All results `NOT_ADDRESSED` | `PEND` |
| `article_result == COVERED` | **APPROVE** |
| `lcd_result == COVERED` | **APPROVE** |
| `ncd_result == COVERED` | **APPROVE** |
| Fallback | `PEND` |

### Decision Values

| Value | Meaning |
|---|---|
| `APPROVE` | Procedure + diagnosis codes match an active policy. Coverage criteria satisfied. |
| `PEND` | Explicit exclusion found, or ambiguous evidence. Requires manual/nurse review. |
| `REQUEST_MORE_INFORMATION` | Missing required data (no policy, outside jurisdiction, diagnosis not found). |

---

## Evaluator Strategies

### Structured Evaluator (SQL — Highest Authority)
Checks code presence against actual database tables. 100% deterministic. Cannot be overridden by LLM.

### Rule Evaluator (Regex — High Authority)
Handles numerical and categorical conditions:
- **Age rules**: extracts operators (`>=`, `<=`, `>`, `<`, `==`) + numeric value, compares to `patient_age`
- **Date rules**: parses `YYYY-MM-DD` from criterion text, compares to `service_date`

### Semantic Evaluator (LLM — Lower Authority)
For narrative criteria requiring clinical language understanding:
- Example: *"Patient must have failed conservative treatment for at least 6 weeks"*
- Returns `SATISFIED / NOT_SATISFIED / UNKNOWN` + quoted patient evidence
- Falls back to `UNKNOWN` if LLM disabled or no clinical notes

### Authority Hierarchy
```
SQL (STRUCTURED) > Rule (RULE_BASED) > LLM (SEMANTIC)
```
A mandatory `NOT_SATISFIED` from SQL immediately returns `EXCLUDED` — no LLM can override this.

---

## Request & Response Schema

### `POST /api/v1/triage` — Request Body

```json
{
  "procedure_code": "64483",
  "diagnosis_codes": ["M54.16", "M54.17"],
  "state": "TX",
  "patient_age": 65,
  "clinical_notes": "Patient has lumbar radiculopathy. Failed 6 weeks of physical therapy and NSAIDs.",
  "service_date": "2025-01-15"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `procedure_code` | string | ✅ | HCPCS or CPT code (e.g. `"64483"`) |
| `diagnosis_codes` | string[] | ✅ | One or more ICD-10-CM codes |
| `state` | string (2-char) | ❌ | US state abbreviation (e.g. `"TX"`) |
| `patient_age` | integer ≥ 0 | ❌ | Patient age in years |
| `clinical_notes` | string | ❌ | Free-text clinical notes for LLM semantic evaluation |
| `service_date` | string (ISO 8601) | ❌ | Date of service for policy effective-date validation |

### `POST /api/v1/triage` — Response Body

```json
{
  "decision": "APPROVE",
  "evidence_score": 0.9,
  "requires_prior_authorization": null,
  "reason": "Decision Engine output: APPROVE. Reason codes: ARTICLE_CRITERIA_SATISFIED",
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
    "ncd":          {"policy_id": null,     "result": "NOT_ADDRESSED"},
    "jurisdiction": {"state": "TX",         "result": "MATCHED"},
    "lcd":          {"policy_id": "L39054", "result": "COVERED"},
    "article":      {"policy_id": "A12345", "result": "COVERED"}
  },
  "matched_codes": {
    "procedure": "64483",
    "diagnosis": ["M54.16"]
  },
  "diagnosis_evaluation": [
    {"code": "M54.16", "status": "COVERED"}
  ],
  "evidence": [
    {
      "type": "JURISDICTION",
      "identifier": "J5",
      "state": "TX",
      "result": "MATCHED",
      "explanation": "State 'TX' matches jurisdiction of LCD L39054."
    },
    {
      "type": "HCPCS",
      "identifier": "A12345",
      "code": "64483",
      "result": "MATCHED",
      "explanation": "Procedure code '64483' is listed in article A12345."
    },
    {
      "type": "ICD10",
      "identifier": "A12345",
      "code": "M54.16",
      "result": "COVERED",
      "explanation": "Diagnosis 'M54.16' is covered."
    }
  ],
  "rag_evidence": [
    {
      "policy_id": "L39054",
      "policy_type": "LCD",
      "section": "indication",
      "chunk_id": "42",
      "text": "Epidural injections are covered for lumbar radiculopathy when...",
      "similarity_score": 0.91,
      "source": "CMS"
    }
  ],
  "criteria": [
    {
      "criterion_id": "ARTICLE-A12345-HCPCS",
      "policy_type": "ARTICLE",
      "policy_id": "A12345",
      "criterion": "The requested procedure must be an applicable service under the Article.",
      "criterion_type": "STRUCTURED",
      "evaluator": "SQL",
      "status": "SATISFIED",
      "patient_evidence": ["Submitted HCPCS: 64483"],
      "policy_evidence": ["Article A12345 contains HCPCS 64483 in its coverage list."],
      "mandatory": true,
      "authoritative": true
    }
  ],
  "missing_information": [],
  "warnings": []
}
```

| Response Field | Type | Description |
|---|---|---|
| `decision` | enum | `APPROVE` / `PEND` / `REQUEST_MORE_INFORMATION` |
| `evidence_score` | float 0.0–1.0 | Deterministic evidence-completeness score (not ML) |
| `requires_prior_authorization` | bool or null | Explicit PA requirement from policy; null if unknown |
| `reason` | string | Human-readable decision explanation |
| `reason_codes` | string[] | Machine-readable reason flags |
| `policies` | MatchedPolicy[] | All policies that matched the request |
| `policy_path` | dict | NCD→Jurisdiction→LCD→Article evaluation chain |
| `evidence` | Evidence[] | Audit trail of every evaluation step |
| `rag_evidence` | RagEvidence[] | Vector search chunks used for evaluation |
| `criteria` | EvaluatedCriterion[] | Every criterion checked with status + evidence |
| `missing_information` | string[] | What data is missing to make a determination |
| `warnings` | string[] | Non-fatal warnings from the evaluation |

---

## Mock Data Reference

When `USE_MOCK_REPOSITORIES=true`, the following demo data is available:

| Entity | ID | Details |
|---|---|---|
| **Article** | `A12345` | Active, covers procedure `64483` |
| **Article** | `A99999` | Retired (tests expired policy path) |
| **LCD** | `L39054` | Active, Jurisdiction J5, linked to `A12345` |
| **LCD** | `L99001` | Expired (end date in past) |
| **NCD** | `N123` | Basic NCD record |
| **Jurisdiction** | `J5` | States: TX, NM, OK, LA, AR, MS, CO |
| **Procedure** | `64483` | Epidural Steroid Injection |
| **Covered ICD-10** | `M54.16` | Radiculopathy, lumbar region |
| **Covered ICD-10** | `M54.17` | Radiculopathy, lumbosacral region |
| **Covered ICD-10** | `M54.4` | Lumbago with sciatica |
| **Non-covered ICD-10** | `Z00.00` | General adult medical examination |
| **Non-covered ICD-10** | `Z00.01` | General adult exam with abnormal findings |

### Quick Test Scenarios

```bash
# APPROVE — procedure matches, TX in J5 jurisdiction, diagnosis covered
curl -X POST http://localhost:8000/api/v1/triage \
  -H "Content-Type: application/json" \
  -d "{\"procedure_code\":\"64483\",\"diagnosis_codes\":[\"M54.16\"],\"state\":\"TX\"}"

# PEND — diagnosis explicitly non-covered
curl -X POST http://localhost:8000/api/v1/triage \
  -H "Content-Type: application/json" \
  -d "{\"procedure_code\":\"64483\",\"diagnosis_codes\":[\"Z00.00\"],\"state\":\"TX\"}"

# REQUEST_MORE_INFORMATION — diagnosis not in any policy list
curl -X POST http://localhost:8000/api/v1/triage \
  -H "Content-Type: application/json" \
  -d "{\"procedure_code\":\"64483\",\"diagnosis_codes\":[\"A01.00\"],\"state\":\"TX\"}"

# REQUEST_MORE_INFORMATION — state outside jurisdiction J5
curl -X POST http://localhost:8000/api/v1/triage \
  -H "Content-Type: application/json" \
  -d "{\"procedure_code\":\"64483\",\"diagnosis_codes\":[\"M54.16\"],\"state\":\"NY\"}"
```

---

## Running Tests

All tests run against **mock repositories** — no database or LLM required.

```bash
# Full test suite
pytest tests/ -v

# Specific file
pytest tests/test_triage.py -v

# With coverage
pytest tests/ --cov=app --cov-report=term-missing

# Triage + RAG only
pytest tests/test_triage.py tests/test_rag_pipeline.py -v
```

### Test Coverage

| File | What's Tested |
|---|---|
| `test_health.py` | `/health` and `/health/db` liveness checks |
| `test_articles.py` | Article retrieval, HCPCS codes, covered/noncovered ICD-10 |
| `test_lcds.py` | LCD retrieval by ID |
| `test_ncds.py` | NCD retrieval by ID |
| `test_policies.py` | Policy search by code and state |
| `test_triage.py` | Full triage: APPROVE, PEND, REQUEST_MORE_INFO scenarios |
| `test_rag_pipeline.py` | Document chunking, embedding generation |

---

## Scripts Reference

Run from the `prior-auth-api/` directory with your virtual environment active.

```bash
# DB management
python scripts/validate_db.py         # Check DB state + row counts
python scripts/seed_db.py             # Seed PostgreSQL with CMS policy data
python scripts/init_vector_db.py      # Install pgvector, create policy_chunks table
python scripts/ingest_ncds.py         # RAG ingestion: chunk + embed → DB

# Data utilities
python scripts/fetch_ncd_hcpcs.py     # Fetch NCD HCPCS codes from CMS
python scripts/generate_mock_ncds.py  # Generate synthetic NCD test data
python scripts/find_icd_codes.py      # Find ICD-10 codes by prefix in DB
python scripts/find_chunks.py         # Inspect vector chunks in DB

# Testing
python scripts/debug_lmstudio.py        # Test LM Studio connectivity
python scripts/test_icd_prefix_requests.py  # Comprehensive live API ICD tests
python scripts/test_e2e.py              # End-to-end API integration test
python scripts/test_llm.py              # LLM client test
python scripts/test_live_qwen.py        # Live Qwen model evaluation test
python scripts/test_llm_scenarios.py    # Multiple LLM scenario tests
```

---

## Database Schema

### Entity Relationship

```
Contractor (Medicare Admin Contractors)
    └── 1:N  Jurisdiction (e.g. J5)
                   └── 1:N  JurisdictionState (TX, NM, OK, LA...)
                   └── 1:N  LCD (Local Coverage Determination)
                                ├── 1:N  LCDHCPCSCode
                                ├── 1:N  LCDIcd10Covered
                                ├── 1:N  LCDIcd10NonCovered
                                └── associated_article_ids → Article
                                            ├── 1:N  ArticleHcpcsCode
                                            ├── 1:N  ArticleIcd10Covered
                                            └── 1:N  ArticleIcd10NonCovered

NCD (National)  [PK: document_id + document_version]
    └── 1:N  NCDHCPCSCode
    └── N:M  LCD  (via LCDNCDAssociation)

PolicyChunk  [pgvector store]
    ├── policy_type  (NCD | LCD)
    ├── policy_id
    ├── section
    ├── chunk_text
    └── embedding    Vector(384)
```

### Key Tables

| Table | Primary Key | Purpose |
|---|---|---|
| `ncds` | `(document_id, document_version)` | National Coverage Determinations |
| `ncd_hcpcs_codes` | `(ncd_id, ncd_version, hcpcs_code)` | HCPCS codes per NCD |
| `lcds` | `(lcd_id, lcd_version)` | Local Coverage Determinations |
| `lcd_hcpcs_codes` | `(lcd_id, lcd_version, hcpcs_code)` | HCPCS codes per LCD |
| `lcd_icd10_covered` | `(lcd_id, lcd_version, icd10_code)` | Covered diagnoses per LCD |
| `lcd_icd10_noncovered` | `(lcd_id, lcd_version, icd10_code)` | Excluded diagnoses per LCD |
| `lcd_ncd_associations` | `id (auto)` | Many-to-many LCD↔NCD links |
| `articles` | `(article_id, article_version)` | CMS Billing/Coding Articles |
| `article_hcpcs` | `(article_id, article_version, hcpcs_code_id)` | HCPCS codes per Article |
| `article_icd10_covered` | `(article_id, article_version, icd10_code_id)` | Covered diagnoses per Article |
| `article_icd10_noncovered` | `(article_id, article_version, icd10_code_id)` | Excluded diagnoses per Article |
| `jurisdictions` | `jurisdiction_id` | MAC jurisdictions (J5, J6, ...) |
| `jurisdiction_states` | `(jurisdiction_id, state)` | State → jurisdiction mapping |
| `contractors` | `contractor_id` | Medicare Administrative Contractors |
| `policy_chunks` | `id (auto)` | Vector store: 384-dim embeddings for RAG |

---

## Privacy & Security Notes

### What this API accepts
- Procedure code (HCPCS/CPT)
- Diagnosis codes (ICD-10)
- US state (2-letter abbreviation)
- Patient age (optional integer)
- Clinical notes (optional free text — no identifiers)
- Service date (optional)

### What this API does NOT accept
- Patient name, SSN, Date of Birth, or any other PHI
- Insurance member IDs or provider NPIs

### Authentication
Currently open for hackathon/demo use. For production, add:
- JWT / OAuth2 middleware to FastAPI
- Rate limiting (`slowapi`)
- HTTPS termination at load balancer or reverse proxy

---

## Integration Guide for Data Team

To connect real CMS data, **only update**:
- `app/models/` — adjust column/table names
- `app/repositories/postgres/` — adjust SQL queries

**Do NOT change** (stable contract):
- `app/api/` — routers
- `app/schemas/` — Pydantic models
- `app/services/` — business logic

See [`docs/data-contract.md`](docs/data-contract.md) for the complete field-by-field integration specification.

---

## Authors

| Contributor | Role |
|---|---|
| Vedarathna | Backend API, Triage Engine, RAG Pipeline |
| Nikhil | Data Collection & Relationship Mapping |
| Naveen Krishnan | Data Collection & Relationship Mapping |

---

*Swagger UI: http://localhost:8000/docs | ReDoc: http://localhost:8000/redoc | OpenAPI: http://localhost:8000/openapi.json*

---

## Architecture

```
Frontend (React / Streamlit / etc.)
    │  HTTP/JSON
    ▼
FastAPI Router / API Layer          ← no SQL, no business logic
    │
    ▼
Service / Business Logic Layer      ← Strict Cascade: NCD → LCD → Article
    │
    ▼
Repository Interface (Protocol)     ← abstract contract
    │
    ├──────────────────────────┐
    ▼                          ▼
Mock Repository          PostgreSQL Repository
(in-memory, demo data)         │
                               ▼
                          SQLAlchemy 2.x
                               │
                               ▼
                          PostgreSQL (psycopg3)
```

**Key design principle**: Switching from mock to PostgreSQL only requires changing `USE_MOCK_REPOSITORIES=false` in the environment. No routers, schemas, or services need to change.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Application health check |
| `GET` | `/api/v1/health/db` | Database connectivity check |
| `GET` | `/api/v1/articles/{article_id}` | Get CMS Article |
| `GET` | `/api/v1/articles/{article_id}/icd10-covered` | Covered ICD-10 codes |
| `GET` | `/api/v1/articles/{article_id}/icd10-noncovered` | Non-covered ICD-10 codes |
| `GET` | `/api/v1/articles/{article_id}/hcpcs` | HCPCS/CPT codes |
| `GET` | `/api/v1/lcds/{lcd_id}` | Get LCD |
| `GET` | `/api/v1/ncds/{ncd_id}` | Get NCD |
| `GET` | `/api/v1/policies/search` | Search policies by code/state |
| `POST` | `/api/v1/triage` | Run prior authorization triage |

Full interactive documentation: **http://localhost:8000/docs**

---

## Quick Start (Local)

### 1. Clone and navigate

```bash
cd prior-auth-api
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

The default `.env` uses `USE_MOCK_REPOSITORIES=true` so no database is required.

### 5. Run the server

```bash
uvicorn app.main:app --reload
```

### 6. Open API docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Mock Mode (Default)

When `USE_MOCK_REPOSITORIES=true` the API runs entirely on in-memory data.

**No PostgreSQL connection is required.**

### Demo data included:

| Entity | ID |
|---|---|
| Article | `A12345` (active) |
| Article | `A99999` (retired) |
| LCD | `L39054` (active, Jurisdiction J5 / TX) |
| LCD | `L99001` (expired) |
| NCD | `N123` |
| Jurisdiction | `J5` (TX, NM, OK, LA, AR, MS, CO) |
| Procedure | `64483` |
| Covered ICD-10 | `M54.16`, `M54.17`, `M54.4` |
| Non-covered ICD-10 | `Z00.00`, `Z00.01` |

### Try it:

```bash
curl -X POST http://localhost:8000/api/v1/triage \
  -H "Content-Type: application/json" \
  -d '{
    "procedure_code": "64483",
    "diagnosis_codes": ["M54.16"],
    "state": "TX",
    "payer": "Medicare"
  }'
```

Expected response: `"decision": "LIKELY_COVERED"` with full evidence.

---

## PostgreSQL Mode

When the data team delivers the final schema:

### 1. Update environment

```env
USE_MOCK_REPOSITORIES=false
DATABASE_URL=postgresql+psycopg://user:password@host:5432/prior_auth
```

### 2. Run migrations

```bash
alembic upgrade head
```

### 3. (Optional) Generate a new migration after schema changes

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

### 4. Integration scope

When integrating the real CMS data:

**Update only:**
- `app/models/` — adjust column/table names
- `app/repositories/postgres/` — adjust queries if needed

**Do NOT change:**
- `app/api/` — routers remain stable
- `app/schemas/` — API contract remains stable
- `app/services/` — business logic remains stable

---

## Running Tests

All tests run against mock repositories. No database required.

```bash
pytest tests/ -v
```

---

## Docker

### Run everything with Docker Compose

```bash
docker compose up --build
```

This starts:
- `api` on http://localhost:8000 (mock mode by default)
- `postgres` on port 5432

### Switch to PostgreSQL in Docker

```bash
USE_MOCK_REPOSITORIES=false docker compose up --build
```

Then in a separate terminal:

```bash
docker compose exec api alembic upgrade head
```

---

## Triage Decision Values

| Decision | Meaning |
|---|---|
| `LIKELY_COVERED` | An NCD explicitly covers it, OR ≥1 diagnosis code matches covered list in an active LCD/Article |
| `LIKELY_NOT_COVERED` | An NCD explicitly excludes it, OR all diagnosis codes are explicitly non-covered |
| `MORE_INFORMATION_REQUIRED` | Policy found but diagnosis codes not in covered or non-covered list, and no clinical context supplied |
| `NURSE_REVIEW` | Ambiguous diagnosis coding but clinical context (like patient age) is provided, requiring manual review |
| `POLICY_NOT_FOUND` | No policy references this procedure code |
| `OUTSIDE_JURISDICTION` | Policy found but submitted state is not in its jurisdiction |
| `POLICY_EXPIRED` | All matching policies have expired |

### Confidence Score

The `confidence` field (0.0–1.0) is a **deterministic evidence-completeness score**, NOT a machine-learning probability.

| Evidence Dimension | Points |
|---|---|
| Procedure match | +0.25 |
| Diagnosis match | +0.30 |
| Jurisdiction match | +0.20 |
| Active policy | +0.15 |
| Article match | +0.10 |

### `requires_prior_authorization`

This field is kept separate from `decision`. It is `null` when the available policy data does not explicitly state authorization requirements. The backend **never invents insurance rules**.

---

## Project Structure

```
prior-auth-api/
├── app/
│   ├── main.py                    FastAPI application
│   ├── api/v1/                    Routers (health, articles, lcds, ncds, policies, triage)
│   ├── schemas/                   Pydantic API models
│   ├── services/                  Business logic
│   ├── repositories/
│   │   ├── interfaces/            Protocol ABCs
│   │   ├── mock/                  In-memory implementations
│   │   └── postgres/              SQLAlchemy implementations
│   ├── models/                    SQLAlchemy ORM models
│   ├── db/                        Engine + session factory
│   ├── dependencies/              FastAPI DI wiring
│   ├── core/                      Config + logging
│   └── exceptions/                Custom errors + handlers
├── tests/                         pytest suite (all mock-based)
├── alembic/                       DB migrations
├── Dockerfile
├── docker-compose.yml
└── docs/data-contract.md          Integration guide for data team
```

---

## Privacy Note

This API accepts only the minimum clinical codes required for policy lookup:
- Procedure code (HCPCS/CPT)
- Diagnosis codes (ICD-10)
- State (optional)
- Payer (optional)
- Patient age (optional)

It does **not** accept or log: patient name, SSN, DOB, or any other PHI.

Authentication can be added as a future enhancement (JWT, OAuth2).
