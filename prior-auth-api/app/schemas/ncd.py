"""Pydantic schemas for NCD-related API responses."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class NCDResponse(BaseModel):
    """Full NCD record returned by GET /ncds/{ncd_id}."""

    id: str
    title: str
    effective_date: date | None = None
    end_date: date | None = None
    description: str | None = None
    manual_section: str | None = None
    decision: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "N123",
                    "title": "Transcutaneous Electrical Nerve Stimulation (TENS) for Acute Pain",
                    "effective_date": "2012-03-01",
                    "end_date": None,
                    "description": "Coverage determination for TENS devices.",
                    "manual_section": "160.7.1",
                    "decision": "COVERED_WITH_CONDITIONS",
                }
            ]
        }
    }
