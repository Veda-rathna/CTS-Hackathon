"""Common/shared Pydantic schemas used across multiple endpoints."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response returned for all 4xx and 5xx responses."""

    code: str
    message: str
    details: dict[str, Any] | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "RESOURCE_NOT_FOUND",
                    "message": "Article A12345 was not found.",
                    "details": None,
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """Response schema for the health check endpoint."""

    status: str
    service: str
    version: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "ok",
                    "service": "prior-authorization-api",
                    "version": "1.0.0",
                }
            ]
        }
    }


class DBHealthResponse(BaseModel):
    """Response schema for the database health check endpoint."""

    status: str
    database: str
    mode: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "ok",
                    "database": "connected",
                    "mode": "postgresql",
                }
            ]
        }
    }
