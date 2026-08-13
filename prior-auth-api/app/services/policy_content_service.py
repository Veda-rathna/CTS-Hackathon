"""PolicyContentService — normalizes policy content across NCD/LCD/Article.

This service provides a consistent interface for the RAG and evaluation
pipelines to access policy text.  It wraps existing repository methods
and extracts text from ORM models WITHOUT modifying repository interfaces.

The existing ``get_by_id()`` methods already return the policy objects;
this service normalises their text fields into ``PolicySection`` objects
with consistent section_type labels.
"""
from __future__ import annotations

import logging
from datetime import date

from app.core.config import Settings
from app.repositories.interfaces.article_repository import ArticleRepository
from app.repositories.interfaces.lcd_repository import LCDRepository
from app.repositories.interfaces.ncd_repository import NCDRepository
from app.schemas.evaluation import PolicySection

logger = logging.getLogger(__name__)


class PolicyContentService:
    """Normalizes policy content from NCD/LCD/Article into standardized
    sections for the RAG chunking, embedding, and evaluation pipelines.

    Does NOT modify any repository interface — it uses existing
    ``get_by_id()`` and the underlying data models.
    """

    def __init__(
        self,
        ncd_repo: NCDRepository,
        lcd_repo: LCDRepository,
        article_repo: ArticleRepository,
        settings: Settings,
    ) -> None:
        self._ncd_repo = ncd_repo
        self._lcd_repo = lcd_repo
        self._article_repo = article_repo
        self._settings = settings

    # ── NCD sections ──────────────────────────────────────────────────────

    def get_ncd_sections(self, ncd_id: str) -> list[PolicySection]:
        """Extract normalized sections from an NCD.

        Uses the existing NCDResponse returned by ``get_by_id()`` plus
        direct ORM access for rich text fields when running against
        PostgreSQL.  In mock mode, falls back to description field.
        """
        ncd = self._ncd_repo.get_by_id(ncd_id)
        if ncd is None:
            return []

        sections: list[PolicySection] = []
        base = dict(
            policy_type="NCD",
            policy_id=ncd.id,
            effective_date=ncd.effective_date,
            end_date=ncd.end_date,
        )

        # The NCDResponse schema has: description, decision
        # For mock mode, description is the primary content
        if ncd.description:
            sections.append(PolicySection(
                **base,
                section_type="description",
                content=ncd.description,
            ))

        # Try to access rich text fields if using postgres repositories
        # The postgres NCD repo returns NCDResponse but the ORM NCD model
        # has additional text fields.  We access them via a separate query
        # when the policy content service is configured for postgres mode.
        if not self._settings.use_mock_repositories:
            sections.extend(self._get_ncd_rich_sections(ncd_id, base))

        return sections

    def _get_ncd_rich_sections(
        self, ncd_id: str, base: dict,
    ) -> list[PolicySection]:
        """Extract rich text sections from NCD ORM model (postgres only)."""
        try:
            from app.db.session import SessionLocal
            from app.models.ncd import NCD
            from sqlalchemy import select

            with SessionLocal() as db:
                # Get latest version
                stmt = (
                    select(NCD)
                    .where(NCD.document_id == ncd_id)
                    .order_by(NCD.document_version.desc())
                    .limit(1)
                )
                row = db.scalars(stmt).first()
                if row is None:
                    return []

                sections: list[PolicySection] = []
                version = str(row.document_version)

                field_map = {
                    "item_service_description": "coverage",
                    "indications_limitations": "indications",
                    "reasons_for_denial": "denial_reasons",
                    "cross_reference": "cross_reference",
                    "other_text": "other",
                }

                for attr, section_type in field_map.items():
                    value = getattr(row, attr, None)
                    if value and value.strip():
                        sections.append(PolicySection(
                            **base,
                            policy_version=version,
                            section_type=section_type,
                            content=value.strip(),
                        ))

                return sections

        except Exception:
            logger.warning("Failed to load rich NCD sections for %s", ncd_id, exc_info=True)
            return []

    # ── LCD sections ──────────────────────────────────────────────────────

    def get_lcd_sections(self, lcd_id: str) -> list[PolicySection]:
        """Extract normalized sections from an LCD.

        The LCD has the richest text: indication, doc_reqs,
        coding_guidelines, diagnoses_support, etc.
        """
        lcd = self._lcd_repo.get_by_id(lcd_id)
        if lcd is None:
            return []

        sections: list[PolicySection] = []
        base = dict(
            policy_type="LCD",
            policy_id=lcd.id,
            policy_version=lcd.version,
            effective_date=lcd.effective_date,
            end_date=lcd.end_date,
            jurisdiction_id=lcd.jurisdiction.id if lcd.jurisdiction else None,
            contractor_id=lcd.contractor.id if lcd.contractor else None,
        )

        # In postgres mode, access the ORM model for rich text fields
        if not self._settings.use_mock_repositories:
            sections.extend(self._get_lcd_rich_sections(lcd_id, base))
        else:
            # Mock mode: minimal content
            if lcd.title:
                sections.append(PolicySection(
                    **base,
                    section_type="title",
                    content=lcd.title,
                ))

        return sections

    def _get_lcd_rich_sections(
        self, lcd_id: str, base: dict,
    ) -> list[PolicySection]:
        """Extract rich text sections from LCD ORM model (postgres only)."""
        try:
            from app.db.session import SessionLocal
            from app.models.lcd import LCD
            from sqlalchemy import select

            with SessionLocal() as db:
                stmt = (
                    select(LCD)
                    .where(LCD.lcd_id == lcd_id)
                    .order_by(LCD.lcd_version.desc())
                    .limit(1)
                )
                row = db.scalars(stmt).first()
                if row is None:
                    return []

                sections: list[PolicySection] = []
                version = str(row.lcd_version)

                field_map = {
                    "cms_cov_policy": "coverage_policy",
                    "indication": "indications",
                    "diagnoses_support": "diagnoses_support",
                    "diagnoses_dont_support": "diagnoses_dont_support",
                    "coding_guidelines": "coding_guidelines",
                    "doc_reqs": "documentation_requirements",
                    "summary_of_evidence": "evidence_summary",
                    "analysis_of_evidence": "evidence_analysis",
                    "associated_info": "associated_info",
                    "appendices": "appendices",
                    "util_guide": "utilization_guidelines",
                }

                for attr, section_type in field_map.items():
                    value = getattr(row, attr, None)
                    if value and value.strip():
                        sections.append(PolicySection(
                            **base,
                            policy_version=version,
                            section_type=section_type,
                            content=value.strip(),
                        ))

                return sections

        except Exception:
            logger.warning("Failed to load rich LCD sections for %s", lcd_id, exc_info=True)
            return []

    # ── Article sections ──────────────────────────────────────────────────

    def get_article_sections(self, article_id: str) -> list[PolicySection]:
        """Extract normalized sections from an Article.

        Articles have limited text (description, cms_cov_policy) —
        most Article evaluation is deterministic code matching.
        """
        article = self._article_repo.get_by_id(article_id)
        if article is None:
            return []

        sections: list[PolicySection] = []
        base = dict(
            policy_type="ARTICLE",
            policy_id=article.id,
            policy_version=article.version,
            effective_date=article.effective_date,
            end_date=article.end_date,
        )

        if article.description:
            sections.append(PolicySection(
                **base,
                section_type="description",
                content=article.description,
            ))

        # In postgres mode, try to get cms_cov_policy text
        if not self._settings.use_mock_repositories:
            try:
                from app.db.session import SessionLocal
                from app.models.article import Article as ArticleModel
                from sqlalchemy import select

                with SessionLocal() as db:
                    stmt = (
                        select(ArticleModel)
                        .where(ArticleModel.article_id == article_id)
                        .order_by(ArticleModel.article_version.desc())
                        .limit(1)
                    )
                    row = db.scalars(stmt).first()
                    if row and getattr(row, "cms_cov_policy", None):
                        sections.append(PolicySection(
                            **base,
                            section_type="coverage_policy",
                            content=row.cms_cov_policy.strip(),
                        ))
            except Exception:
                logger.warning(
                    "Failed to load rich Article sections for %s",
                    article_id, exc_info=True,
                )

        return sections
