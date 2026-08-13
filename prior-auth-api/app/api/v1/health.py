"""Health check endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.common import DBHealthResponse, HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Application health check",
    description=(
        "Returns the current health status of the API. "
        "Always returns ``200 OK`` if the application is running."
    ),
)
def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="prior-authorization-api",
        version=settings.app_version,
    )


@router.get(
    "/db",
    response_model=DBHealthResponse,
    summary="Database connectivity health check",
    description=(
        "Checks whether the configured data store is reachable. "
        "In mock mode this always returns ``mock`` status without touching a database."
    ),
)
def db_health_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> DBHealthResponse:
    if settings.use_mock_repositories:
        return DBHealthResponse(
            status="ok",
            database="mock",
            mode="mock",
        )

    from app.db.session import check_db_connection

    connected = check_db_connection()
    return DBHealthResponse(
        status="ok" if connected else "degraded",
        database="connected" if connected else "unreachable",
        mode="postgresql",
    )


@router.get(
    "/ready",
    response_model=DBHealthResponse,
    summary="Readiness check",
    description="Alias for the DB health check to verify the service is fully ready.",
)
def readiness_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> DBHealthResponse:
    return db_health_check(settings)


@router.get(
    "/version",
    summary="API version check",
)
def version_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    return {
        "service": "prior-auth-triage-api",
        "version": settings.app_version,
    }
