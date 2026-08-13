"""Pydantic schemas for LCD-related API responses."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.schemas.article import CodeEntry


class JurisdictionSummary(BaseModel):
    """Minimal jurisdiction info embedded in LCD responses."""

    id: str
    name: str | None = None


class ContractorSummary(BaseModel):
    """Minimal contractor/MAC info embedded in LCD responses."""

    id: str
    name: str | None = None


class LCDResponse(BaseModel):
    """Full LCD record returned by GET /lcds/{lcd_id}."""

    id: str
    title: str
    version: str | None = None
    effective_date: date | None = None
    end_date: date | None = None
    jurisdiction: JurisdictionSummary | None = None
    contractor: ContractorSummary | None = None
    associated_article_ids: list[str] = []
    hcpcs_codes: list[CodeEntry] = []
    icd10_covered: list[CodeEntry] = []
    icd10_noncovered: list[CodeEntry] = []

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "L39054",
                    "title": "Epidural Injections for Pain Management",
                    "version": "1",
                    "effective_date": "2023-01-01",
                    "end_date": None,
                    "jurisdiction": {"id": "J5", "name": "Jurisdiction 5"},
                    "contractor": {"id": "12301", "name": "Novitas Solutions"},
                    "associated_article_ids": ["A12345"],
                    "hcpcs_codes": [
                        {"code": "64483", "description": "Transforaminal epidural injection, lumbar/sacral"},
                    ],
                    "icd10_covered": [
                        {"code": "M54.16", "description": "Radiculopathy, lumbar region"},
                    ],
                    "icd10_noncovered": [
                        {"code": "Z00.00", "description": "General adult examination"},
                    ],
                }
            ]
        }
    }
