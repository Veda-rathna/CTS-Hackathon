"""Pydantic schemas for Article-related API responses."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class ArticleResponse(BaseModel):
    """Full article record returned by GET /articles/{article_id}."""

    id: str
    version: str | None = None
    display_id: str | None = None
    title: str
    publication_number: str | None = None
    effective_date: date | None = None
    end_date: date | None = None
    description: str | None = None
    status: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "A12345",
                    "version": "1",
                    "display_id": "A12345",
                    "title": "Injections — Epidural Steroid (Medicare)",
                    "publication_number": "100-3",
                    "effective_date": "2023-01-01",
                    "end_date": None,
                    "description": "Coverage criteria for epidural steroid injections.",
                    "status": "ACTIVE",
                }
            ]
        }
    }


class CodeEntry(BaseModel):
    """A single code entry (ICD-10 or HCPCS/CPT) within an article."""

    code: str
    description: str | None = None


class ICD10CodesResponse(BaseModel):
    """List of ICD-10 codes (covered or non-covered) for an article."""

    article_id: str
    codes: list[CodeEntry]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "article_id": "A12345",
                    "codes": [
                        {"code": "M54.16", "description": "Radiculopathy, lumbar region"},
                        {"code": "M54.17", "description": "Radiculopathy, lumbosacral region"},
                    ],
                }
            ]
        }
    }


class HCPCSCodesResponse(BaseModel):
    """List of HCPCS/CPT codes referenced in an article."""

    article_id: str
    codes: list[CodeEntry]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "article_id": "A12345",
                    "codes": [
                        {"code": "64483", "description": "Injection(s), anesthetic agent and/or steroid, transforaminal epidural; lumbar or sacral, single level"},
                        {"code": "64484", "description": "Injection(s), anesthetic agent and/or steroid, transforaminal epidural; lumbar or sacral, each additional level"},
                    ],
                }
            ]
        }
    }
