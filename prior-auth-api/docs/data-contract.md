# Data Integration Contract

This document describes what the FastAPI backend expects from the PostgreSQL database so that the data team can prepare the CMS data independently.

---

## Purpose

The FastAPI backend is designed so that:

1. **The API routers and schemas are stable** — they will not change when the database schema is finalised.
2. **Only the SQLAlchemy models and PostgreSQL repositories need updating** when the real CMS data schema is available.

---

## Core Questions the API Must Answer

The database must ultimately allow the API to answer:

| Question | Required Data |
|---|---|
| Which policies cover procedure `64483`? | HCPCS/CPT → Article/LCD/NCD mapping |
| Which ICD-10 codes are covered for this policy? | Article covered ICD-10 list |
| Which ICD-10 codes are non-covered? | Article non-covered ICD-10 list |
| Which jurisdiction governs this LCD? | LCD → Jurisdiction mapping |
| Which states are in jurisdiction J5? | Jurisdiction → State mapping |
| Is this policy currently effective? | Effective date + end date |
| Which article is associated with this LCD? | LCD → Article mapping |

---

## Expected Entity Relationships

```
Contractor
    │
    └── 1:N Jurisdiction
              │
              └── 1:N LCD
                    │
                    ├── N:M Article (via LCD-Article association)
                    │         │
                    │         ├── ICD-10 Covered codes
                    │         ├── ICD-10 Non-covered codes
                    │         └── HCPCS/CPT codes
                    │
                    ├── LCD ICD-10 Covered codes
                    ├── LCD ICD-10 Non-covered codes
                    └── LCD HCPCS/CPT codes

NCD (standalone, may reference contractor)
```

---

## Expected CMS Data Fields

### Article

| Field | Type | Notes |
|---|---|---|
| article_id | string | Primary key (e.g. `A12345`) |
| version | string | |
| display_id | string | |
| title | string | |
| publication_number | string | |
| effective_date | date | ISO 8601 |
| end_date | date | Null if still active |
| description | text | |
| status | string | e.g. `ACTIVE`, `RETIRED` |

### Article ICD-10 Covered

| Field | Type |
|---|---|
| article_id | FK → Article |
| icd10_code | string |
| description | string |

### Article ICD-10 Non-Covered

| Field | Type |
|---|---|
| article_id | FK → Article |
| icd10_code | string |
| description | string |

### Article HCPCS/CPT

| Field | Type |
|---|---|
| article_id | FK → Article |
| hcpcs_code | string |
| description | string |

### LCD

| Field | Type |
|---|---|
| lcd_id | string |
| title | string |
| version | string |
| effective_date | date |
| end_date | date |
| jurisdiction_id | FK → Jurisdiction |
| contractor_id | FK → Contractor |

### NCD

| Field | Type |
|---|---|
| ncd_id | string |
| title | string |
| effective_date | date |
| end_date | date |
| description | text |
| manual_section | string |
| decision | string |

### Contractor

| Field | Type |
|---|---|
| contractor_id | string |
| name | string |
| region | string |

### Jurisdiction

| Field | Type | Notes |
|---|---|---|
| jurisdiction_id | string | e.g. `J5` |
| name | string | |
| states | text | Comma-separated state abbreviations |
| contractor_id | FK → Contractor | |

---

## Integration Steps for the Data Team

1. Create the PostgreSQL database and tables following the entity relationships above.
2. Load CMS data (NCD, LCD, Articles, codes) into the tables.
3. In the FastAPI project, set `USE_MOCK_REPOSITORIES=false` and `DATABASE_URL` to point to the database.
4. Run `alembic upgrade head` to apply the ORM schema.
5. If the actual table/column names differ from the SQLAlchemy models, update:
   - `app/models/article.py`
   - `app/models/lcd.py`
   - `app/models/ncd.py`
   - `app/models/contractor.py`
   - `app/models/jurisdiction.py`
   - `app/repositories/postgres/*.py` (adjust queries)
6. Do NOT change `app/api/`, `app/schemas/`, or `app/services/`.

---

## Notes

- The exact table names are not fixed — only the field semantics matter.
- If the CMS data has a different structure (e.g. HCPCS codes stored directly on LCD vs. via article), update the PostgreSQL repository only.
- The mock data provides a working example of the expected data shape.
