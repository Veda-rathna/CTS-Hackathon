"""FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload

API documentation:
    http://localhost:8000/docs
    http://localhost:8000/redoc
    http://localhost:8000/openapi.json
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.exceptions.handlers import register_exception_handlers

# ── Configure logging before anything else ────────────────────────────────────
configure_logging()

settings = get_settings()

# ── FastAPI application ───────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "## Prior Authorization Triage & Policy Companion\n\n"
        "Helps healthcare professionals determine which Medicare coverage policies "
        "(NCD, LCD, Articles) may apply to a proposed medical service **before** "
        "treatment or claim processing.\n\n"
        "### Key Endpoints\n"
        "- `POST /api/v1/triage` — Submit a procedure + diagnosis for policy triage\n"
        "- `GET /api/v1/policies/search` — Search policies by code and state\n"
        "- `GET /api/v1/articles/{id}` — Retrieve a CMS Article\n"
        "- `GET /api/v1/lcds/{id}` — Retrieve a Local Coverage Determination\n"
        "- `GET /api/v1/ncds/{id}` — Retrieve a National Coverage Determination\n\n"
        "### Important Disclaimer\n"
        "> **This API provides policy-matching results only.  "
        "It does NOT constitute clinical advice, guarantee of insurance coverage, "
        "or a prior authorization decision.  Always verify with the applicable "
        "Medicare Administrative Contractor (MAC).**\n\n"
        "### Architecture\n"
        "Repository pattern with mock and PostgreSQL backends selectable via "
        "`USE_MOCK_REPOSITORIES` environment variable."
    ),
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Vedarathna",
    },
    license_info={
        "name": "MIT",
    },
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ────────────────────────────────────────────────────────

register_exception_handlers(app)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(v1_router, prefix=settings.api_v1_prefix)
