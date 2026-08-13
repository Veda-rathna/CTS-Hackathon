"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All application settings.

    Values are read from environment variables or a ``.env`` file in the
    working directory.  See ``.env.example`` for the full list.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────
    app_name: str = "Prior Authorization Triage API"
    app_version: str = "1.0.0"
    environment: str = "development"

    # ── Database ─────────────────────────────────────────────────────────
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/prior_auth"
    )

    # ── Repository strategy ───────────────────────────────────────────────
    # When True the application runs entirely on in-memory mock data so that
    # the API and services can be exercised without a live PostgreSQL database.
    use_mock_repositories: bool = False

    # ── API ───────────────────────────────────────────────────────────────
    api_v1_prefix: str = "/api/v1"

    # ── CORS ──────────────────────────────────────────────────────────────
    cors_origins: str = (
        "http://localhost:3000,http://localhost:5173,http://localhost:8501"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a parsed list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── Logging ───────────────────────────────────────────────────────────
    log_level: str = "INFO"

    # ── LLM ───────────────────────────────────────────────────────────────
    # Controls the language model used for semantic criterion evaluation.
    # Set LLM_ENABLED=false for deterministic-only operation (no API calls).
    llm_provider: str = "openai"
    llm_model: str = "qwen/qwen3-4b-2507"
    llm_api_key: str = "local"
    llm_base_url: str = "http://127.0.0.1:1234/v1"
    llm_enabled: bool = False
    llm_timeout_seconds: int = 30

    # ── Embedding ─────────────────────────────────────────────────────────
    # Model used to generate policy text embeddings for RAG retrieval.
    # Dimension must match the model output; change both together.
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # ── RAG ───────────────────────────────────────────────────────────────
    # Controls the retrieval-augmented generation pipeline for policy content.
    # When RAG_ENABLED=false, NCD evaluation falls back to decision field only.
    rag_enabled: bool = False
    vector_top_k: int = 5
    vector_min_score: float = 0.65


    @property
    def database_url_normalized(self) -> str:
        """Ensure standard postgresql:// scheme is converted to postgresql+psycopg://."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()
