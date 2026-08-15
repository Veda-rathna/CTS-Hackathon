"""API v1 master router — aggregates all sub-routers."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import articles, extract, health, lcds, ncds, policies, triage

router = APIRouter()

router.include_router(health.router)
router.include_router(extract.router)
router.include_router(articles.router)
router.include_router(lcds.router)
router.include_router(ncds.router)
router.include_router(policies.router)
router.include_router(triage.router)

