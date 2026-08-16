"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Settings(BaseSettings):
    """All application settings.

    Values are read from environment variables or a ``.env`` file in the
    working directory.  See ``.env.example`` for the full list.
    """

    model_config = SettingsConfigDict(
        env_file=os.path.join(PROJECT_ROOT, ".env"),
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

    # ── LLM Configuration ─────────────────────────────────────────────────
    llm_enabled: bool = True
    llm_provider: str = "bedrock"
    llm_base_url: str = "http://127.0.0.1:1234/v1"
    llm_model: str = "qwen3-next-80b-a3b"
    llm_temperature: float = 0.0
    llm_api_key: str = ""

    # ── CMS Coverage API Configuration ─────────────────────────────────────
    cms_coverage_api_base_url: str = "https://api.coverage.cms.gov/v1"
    cms_coverage_api_timeout: float = 10.0
    cms_coverage_api_max_retries: int = 3
    cms_coverage_api_enabled: bool = True
    cms_coverage_api_key: str = ""

    # ── Agentic Semantic Evaluation Configuration ──────────────────────────────
    # Controls the 4-agent pipeline: PolicyAgent → ClinicalEvidenceAgent →
    # EvaluationAgent → Qwen → CriticAgent
    #
    # agent_read_timeout_secs: Per-agent LLM call timeout (seconds).
    #   Increase for slower hardware / larger models.
    #   Default 30s covers Qwen3-4B on CPU.
    agent_read_timeout_secs: float = 30.0

    # agent_hallucination_threshold: Minimum fraction of key words from a cited
    #   evidence string that must appear in the original clinical text.
    #   0.0 = disable hallucination guard, 1.0 = exact match required.
    agent_hallucination_threshold: float = 0.35

    # agent_source_text_max_chars: Max chars of source_text passed to PolicyAgent.
    #   Prevents very large policy chunks from blowing out LLM context.
    agent_source_text_max_chars: int = 2000



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
