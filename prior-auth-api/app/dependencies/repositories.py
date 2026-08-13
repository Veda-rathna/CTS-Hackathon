"""FastAPI dependency providers for repository and service instances.

Switching between mock and PostgreSQL is controlled entirely by the
``USE_MOCK_REPOSITORIES`` environment variable.  No router or service
code needs to change when switching modes.

Usage in a router
-----------------
    from fastapi import Depends
    from app.dependencies.repositories import get_article_service

    @router.get("/articles/{article_id}")
    def get_article(
        article_id: str,
        service: ArticleService = Depends(get_article_service),
    ):
        return service.get_article(article_id)
"""
from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.repositories.interfaces.article_repository import ArticleRepository
from app.repositories.interfaces.lcd_repository import LCDRepository
from app.repositories.interfaces.ncd_repository import NCDRepository
from app.repositories.interfaces.policy_repository import PolicyRepository
from app.services.article_service import ArticleService
from app.services.lcd_service import LCDService
from app.services.ncd_service import NCDService
from app.services.policy_service import PolicyService
from app.services.triage_service import TriageService
from app.services.policy_content_service import PolicyContentService
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.vector_policy_retriever import VectorPolicyRetriever
from app.services.evaluation.criterion_classifier import CriterionClassifier
from app.services.evaluation.criteria_extractor import CriteriaExtractor
from app.services.evaluation.structured_evaluator import StructuredEvaluator
from app.services.evaluation.rule_evaluator import RuleEvaluator
from app.services.evaluation.semantic_evaluator import SemanticEvaluator
from app.services.evaluation.evidence_fusion import EvidenceFusion
from app.services.evaluation.decision_engine import DecisionEngine
from app.services.evaluation.multi_evaluator import MultiEvaluator
from app.services.llm.llm_client import LLMClient
from app.db.session import SessionLocal


# ── Repository factories ──────────────────────────────────────────────────────


def get_article_repository(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ArticleRepository:
    """Return the correct ArticleRepository implementation."""
    if settings.use_mock_repositories:
        from app.repositories.mock.article_repository import MockArticleRepository
        return MockArticleRepository()
    from app.repositories.postgres.article_repository import PostgresArticleRepository
    return PostgresArticleRepository()


def get_lcd_repository(
    settings: Annotated[Settings, Depends(get_settings)],
) -> LCDRepository:
    """Return the correct LCDRepository implementation."""
    if settings.use_mock_repositories:
        from app.repositories.mock.lcd_repository import MockLCDRepository
        return MockLCDRepository()
    from app.repositories.postgres.lcd_repository import PostgresLCDRepository
    return PostgresLCDRepository()


def get_ncd_repository(
    settings: Annotated[Settings, Depends(get_settings)],
) -> NCDRepository:
    """Return the correct NCDRepository implementation."""
    if settings.use_mock_repositories:
        from app.repositories.mock.ncd_repository import MockNCDRepository
        return MockNCDRepository()
    from app.repositories.postgres.ncd_repository import PostgresNCDRepository
    return PostgresNCDRepository()


def get_policy_repository(
    settings: Annotated[Settings, Depends(get_settings)],
) -> PolicyRepository:
    """Return the correct PolicyRepository implementation."""
    if settings.use_mock_repositories:
        from app.repositories.mock.policy_repository import MockPolicyRepository
        return MockPolicyRepository()
    from app.repositories.postgres.policy_repository import PostgresPolicyRepository
    return PostgresPolicyRepository()


# ── Service factories (depend on repository factories) ────────────────────────


def get_article_service(
    repo: Annotated[ArticleRepository, Depends(get_article_repository)],
) -> ArticleService:
    return ArticleService(repository=repo)


def get_lcd_service(
    repo: Annotated[LCDRepository, Depends(get_lcd_repository)],
) -> LCDService:
    return LCDService(repository=repo)


def get_ncd_service(
    repo: Annotated[NCDRepository, Depends(get_ncd_repository)],
) -> NCDService:
    return NCDService(repository=repo)


def get_policy_service(
    repo: Annotated[PolicyRepository, Depends(get_policy_repository)],
) -> PolicyService:
    return PolicyService(repository=repo)


def get_db_session_factory():
    """Returns a factory function for DB sessions, used by pgvector retriever."""
    return SessionLocal


def get_policy_content_service(
    ncd_repo: Annotated[NCDRepository, Depends(get_ncd_repository)],
    lcd_repo: Annotated[LCDRepository, Depends(get_lcd_repository)],
    article_repo: Annotated[ArticleRepository, Depends(get_article_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PolicyContentService:
    return PolicyContentService(ncd_repo, lcd_repo, article_repo, settings)


def get_embedding_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> EmbeddingService:
    return EmbeddingService(settings)


def get_vector_retriever(
    embedding_service: Annotated[EmbeddingService, Depends(get_embedding_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> VectorPolicyRetriever:
    return VectorPolicyRetriever(SessionLocal, embedding_service, settings)


def get_criteria_extractor() -> CriteriaExtractor:
    return CriteriaExtractor(CriterionClassifier())


def get_multi_evaluator(
    settings: Annotated[Settings, Depends(get_settings)],
) -> MultiEvaluator:
    return MultiEvaluator(
        structured_evaluator=StructuredEvaluator(),
        rule_evaluator=RuleEvaluator(),
        semantic_evaluator=SemanticEvaluator(LLMClient(settings), settings),
    )


def get_triage_service(
    policy_repo: Annotated[PolicyRepository, Depends(get_policy_repository)],
    article_repo: Annotated[ArticleRepository, Depends(get_article_repository)],
    ncd_repo: Annotated[NCDRepository, Depends(get_ncd_repository)],
    lcd_repo: Annotated[LCDRepository, Depends(get_lcd_repository)],
    policy_content: Annotated[PolicyContentService, Depends(get_policy_content_service)],
    rag_retriever: Annotated[VectorPolicyRetriever, Depends(get_vector_retriever)],
    extractor: Annotated[CriteriaExtractor, Depends(get_criteria_extractor)],
    multi_evaluator: Annotated[MultiEvaluator, Depends(get_multi_evaluator)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TriageService:
    return TriageService(
        policy_repository=policy_repo,
        article_repository=article_repo,
        ncd_repository=ncd_repo,
        lcd_repository=lcd_repo,
        policy_content=policy_content,
        rag_retriever=rag_retriever,
        extractor=extractor,
        multi_evaluator=multi_evaluator,
        fusion=EvidenceFusion(),
        decision_engine=DecisionEngine(),
        settings=settings,
    )
