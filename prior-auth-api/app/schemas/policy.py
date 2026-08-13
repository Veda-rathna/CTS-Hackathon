"""Pydantic schemas for Policy search API responses."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class PolicyMatch(BaseModel):
    """A single matched policy returned by the policy search endpoint."""

    policy_type: str
    """Type of policy: LCD, NCD, or ARTICLE."""

    policy_id: str
    """The policy's primary identifier (e.g. L39054, N123)."""

    title: str | None = None
    article_id: str | None = None
    jurisdiction_id: str | None = None
    effective_date: date | None = None
    end_date: date | None = None

    # Match flags
    procedure_match: bool = False
    diagnosis_match: bool = False
    jurisdiction_match: bool = False
    effective: bool = True


class PolicySearchResponse(BaseModel):
    """Response returned by GET /policies/search."""

    matches: list[PolicyMatch]
    total: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "matches": [
                        {
                            "policy_type": "LCD",
                            "policy_id": "L39054",
                            "title": "Epidural Injections for Pain Management",
                            "article_id": "A12345",
                            "jurisdiction_id": "J5",
                            "effective_date": "2023-01-01",
                            "end_date": None,
                            "procedure_match": True,
                            "diagnosis_match": True,
                            "jurisdiction_match": True,
                            "effective": True,
                        }
                    ],
                    "total": 1,
                }
            ]
        }
    }
