# Prior Authorization Triage & Policy Companion — Backend API

A production-ready FastAPI backend that helps healthcare professionals determine which Medicare coverage policies (NCD, LCD, Articles) apply to a proposed medical service **before** treatment or claim processing.

> **⚠️ DISCLAIMER**: This API provides policy-matching results only. It does NOT constitute clinical advice, a guarantee of insurance coverage, or a prior authorization decision. Always verify with the applicable Medicare Administrative Contractor (MAC).

---

## Architecture

```
Frontend (React / Streamlit / etc.)
    │  HTTP/JSON
    ▼
FastAPI Router / API Layer          ← no SQL, no business logic
    │
    ▼
Service / Business Logic Layer      ← no SQL, no SQLAlchemy imports
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
| `LIKELY_COVERED` | ≥1 diagnosis code matches covered list in an active, applicable policy |
| `LIKELY_NOT_COVERED` | All diagnosis codes are explicitly non-covered |
| `MORE_INFORMATION_REQUIRED` | Policy found but diagnosis codes not in covered or non-covered list |
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
