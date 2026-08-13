"""Logging configuration for the application."""
from __future__ import annotations

import logging
import sys

from app.core.config import get_settings


def configure_logging() -> None:
    """Configure root logger based on the LOG_LEVEL setting.

    Call once at application startup in ``main.py``.

    NOTE: Sensitive patient information must never be logged.
    Only procedure codes, policy IDs, and decision outcomes are logged.
    """
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
    )

    # Suppress noisy third-party loggers in development
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger for the given module."""
    return logging.getLogger(name)
