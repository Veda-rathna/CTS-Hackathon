# Prior Authorization Triage & Policy Companion (CTS Hackathon)

A production-ready solution addressing Use Case **UC02: Prior Authorization Triage and Policy Companion** under Utilization Management.

---

## 📋 Problem Statement (UC02)

> **"Before some treatments happen, the insurer has to say yes first — that pre-check is called 'prior authorization' or 'prior auth'. Prototype a system that takes an incoming request, extracts the key clinical and administrative facts, checks it against a configurable coverage rule set, and recommends approve, pend for nurse review, or request more information — with the reasoning shown."**

### The Challenge
Prior authorization decides whether a requested service meets a health plan's coverage and medical necessity rules before care is delivered. It is one of the most scrutinized payer-provider friction points today because **speed, accuracy, transparency, and experience** (member & provider) all matter simultaneously.

### Data Scope
- **Synthea synthetic patient records** (FHIR/CSV) for request context
- **CMS Medicare Coverage Database** (National Coverage Determinations [NCD], Local Coverage Determinations [LCD], Local Coverage Articles [LCA])
- **Publicly posted payer medical policy text**

---

## 🛠️ Our Solution & Architectural Approach

We built a modular, production-ready **FastAPI backend** designed to cleanly separate clinical rule evaluation from underlying database models.

```
                  [ Prior Auth Request ]
                             │
                             ▼
                   Extract Request Facts
                   (HCPCS, ICD-10, Age, State)
                             │
                             ▼
                 1. Evaluate NCD Policies
                 ┌───────────┼───────────┐
                 ▼           ▼           ▼
              [COVERED]  [EXCLUDED]  [NOT ADDRESSED]
                 │           │           │
                 ▼           ▼           │
              APPROVE       DENY         │
                                         ▼
                             2. Evaluate LCD Policies
                             ┌───────────┼───────────┐
                             ▼           ▼           ▼
                          [COVERED]  [EXCLUDED]  [UNKNOWN/OUT JURISD.]
                             │           │           │
                             ▼           ▼           ▼
                         To Article     DENY      OUTSIDE JURISD. /
                                                  PEND (More Info)
                                 │
                                 ▼
                     3. Evaluate LCA (Articles)
                     ┌───────────┼───────────┐
                     ▼           ▼           ▼
                   [HCPCS]    [ICD-10]    [Other Coding]
                     │           │           │
                     └───────────┼───────────┘
                                 ▼
                          Final Decision
                     ┌───────────┴───────────┐
                     ▼                       ▼
               [Match Found]          [Ambiguous Match]
                     │                       │
           ┌─────────┴─────────┐   ┌─────────┴─────────┐
           ▼                   ▼   ▼                   ▼
        APPROVE              DENY  NURSE REVIEW    PEND / MORE INFO
                                  (Clinical Flags) (No Flags)
```

### Key Technical Pillars

1. **Deterministic Cascade Execution**:
   - **NCD Evaluator (First Priority)**: Resolves policies at the national level. If an NCD covers or excludes the procedure, the request halts early.
   - **LCD Evaluator (Second Priority)**: Runs localized administrative checks. Validates state codes against Regional Medicare Administrative Contractor (MAC) jurisdictions.
   - **Article Evaluator (Third Priority)**: Validates granular coding lists (HCPCS/CPT and ICD-10 covered/non-covered associations).

2. **Smart Fallbacks & Nurse Review**:
   - Matches the flowchart's **Nurse Review** node. When diagnosis codes are not explicitly covered or denied, the engine evaluates available clinical flags (such as patient age or administrative details) to pend the request for human verification (`NURSE_REVIEW`) rather than rejecting it or outputting a generic error.

3. **Repository Pattern (Dual Mock/Postgres Backends)**:
   - **Zero Code-Leakage**: The API layer, schemas, and business services have zero knowledge of database syntax, SQL, or SQLAlchemy.
   - **Configurable Mode**: Toggle `USE_MOCK_REPOSITORIES=true` in `.env` to run the engine fully in memory on static mock records (ideal for rapid frontend prototyping and demo environments). Setting it to `false` automatically spins up real PostgreSQL querying.

---

## 📂 Project Directory Structure

```
CTS-Hackathon/
├── prior-auth-api/             # FastAPI Application Root
│   ├── app/
│   │   ├── api/v1/             # REST Endpoints (triage, policies, articles, LCDs, health)
│   │   ├── schemas/            # Strict Pydantic API Data Models
│   │   ├── services/           # Cascade triage engine and business rules
│   │   ├── repositories/       # Data Access Interfaces (Mock & Postgres implementations)
│   │   ├── models/             # SQLAlchemy ORM schemas
│   │   └── dependencies/       # Dependency Injection wiring
│   ├── tests/                  # Pytest suite (38 test cases passing)
│   ├── alembic/                # Database migrations
│   ├── docs/                   # Data contract integration guides
│   ├── Dockerfile
│   └── docker-compose.yml
└── README.md                   # Workspace root details (this file)
```

---

## ⚡ Quick Start

### 1. Run the Backend API (Mock Mode)

No database configuration is required to test the logic:

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

# Copy configuration
cp .env.example .env

# Run server
uvicorn app.main:app --reload
```
Navigate to **[http://localhost:8000/docs](http://localhost:8000/docs)** to view the interactive Swagger OpenAPI specification.

### 2. Run Test Suite
```bash
pytest tests/ -v
```
All 38 test suites covering the triage evaluation logic, NCD cascade, and Nurse Review routing must resolve to `PASSED`.