"""Custom application exceptions and FastAPI exception handlers.

Exception hierarchy
-------------------
AppError (base)
├── ResourceNotFoundError   → HTTP 404
├── InvalidPolicyInputError → HTTP 400
├── PolicyEvaluationError   → HTTP 422
└── RepositoryError         → HTTP 503
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# ── Custom exceptions ─────────────────────────────────────────────────────────


class AppError(Exception):
    """Base class for all application-level errors."""

    code: str = "APP_ERROR"
    message: str = "An unexpected error occurred."
    http_status: int = 500

    def __init__(self, message: str | None = None, details: dict | None = None) -> None:
        self.message = message or self.__class__.message
        self.details = details
        super().__init__(self.message)


class ResourceNotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    code = "RESOURCE_NOT_FOUND"
    message = "The requested resource was not found."
    http_status = 404


class InvalidPolicyInputError(AppError):
    """Raised when the caller supplies invalid/inconsistent input."""

    code = "INVALID_INPUT"
    message = "The request contains invalid input."
    http_status = 400


class PolicyEvaluationError(AppError):
    """Raised when the triage engine encounters an irrecoverable logic error."""

    code = "POLICY_EVALUATION_ERROR"
    message = "An error occurred while evaluating the policy."
    http_status = 422


class RepositoryError(AppError):
    """Raised when a repository operation fails (e.g., database unavailable)."""

    code = "REPOSITORY_ERROR"
    message = "A data-access error occurred."
    http_status = 503


# ── FastAPI exception handlers ────────────────────────────────────────────────


def _error_body(code: str, message: str, details: dict | None) -> dict:
    return {"code": code, "message": message, "details": details}


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all custom exception handlers to the FastAPI application."""

    @app.exception_handler(ResourceNotFoundError)
    async def not_found_handler(request: Request, exc: ResourceNotFoundError) -> JSONResponse:
        logger.info("ResourceNotFoundError: %s", exc.message)
        return JSONResponse(
            status_code=exc.http_status,
            content=_error_body(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(InvalidPolicyInputError)
    async def bad_input_handler(request: Request, exc: InvalidPolicyInputError) -> JSONResponse:
        logger.warning("InvalidPolicyInputError: %s", exc.message)
        return JSONResponse(
            status_code=exc.http_status,
            content=_error_body(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(PolicyEvaluationError)
    async def eval_error_handler(request: Request, exc: PolicyEvaluationError) -> JSONResponse:
        logger.error("PolicyEvaluationError: %s", exc.message)
        return JSONResponse(
            status_code=exc.http_status,
            content=_error_body(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RepositoryError)
    async def repo_error_handler(request: Request, exc: RepositoryError) -> JSONResponse:
        logger.error("RepositoryError: %s", exc.message)
        return JSONResponse(
            status_code=exc.http_status,
            content=_error_body(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content=_error_body(
                "INTERNAL_SERVER_ERROR",
                "An unexpected internal error occurred.",
                None,
            ),
        )
