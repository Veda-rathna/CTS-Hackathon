"""PostgreSQL Article repository.

Supports composite version primary keys.
"""
from __future__ import annotations

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.article import Article, ArticleHcpcsCode, ArticleIcd10Covered, ArticleIcd10NonCovered
from app.schemas.article import ArticleResponse, CodeEntry


class PostgresArticleRepository:
    """SQLAlchemy-backed Article repository."""

    def _session(self):  # type: ignore[no-untyped-def]
        return SessionLocal()

    def _get_latest_version(self, db, article_id: str) -> int | None:
        stmt = (
            select(Article.article_version)
            .where(Article.article_id == article_id)
            .order_by(Article.article_version.desc())
            .limit(1)
        )
        return db.scalars(stmt).first()

    def get_by_id(self, article_id: str) -> ArticleResponse | None:
        """Return the latest version of the article or ``None`` if not found."""
        with self._session() as db:
            latest_version = self._get_latest_version(db, article_id)
            if latest_version is None:
                return None
            row = db.get(Article, (article_id, latest_version))
            if row is None:
                return None
            return ArticleResponse(
                id=row.article_id,
                version=str(row.article_version),
                display_id=row.display_id,
                title=row.title or "",
                effective_date=row.article_eff_date,
                end_date=row.article_end_date,
                description=row.description,
                status=row.status or "ACTIVE",
            )

    def get_icd10_covered(self, article_id: str) -> list[CodeEntry]:
        with self._session() as db:
            latest_version = self._get_latest_version(db, article_id)
            if latest_version is None:
                return []
            stmt = select(ArticleIcd10Covered).where(
                ArticleIcd10Covered.article_id == article_id,
                ArticleIcd10Covered.article_version == latest_version
            )
            rows = db.scalars(stmt).all()
            return [CodeEntry(code=r.icd10_code_id, description=r.description) for r in rows]

    def get_icd10_noncovered(self, article_id: str) -> list[CodeEntry]:
        with self._session() as db:
            latest_version = self._get_latest_version(db, article_id)
            if latest_version is None:
                return []
            stmt = select(ArticleIcd10NonCovered).where(
                ArticleIcd10NonCovered.article_id == article_id,
                ArticleIcd10NonCovered.article_version == latest_version
            )
            rows = db.scalars(stmt).all()
            return [CodeEntry(code=r.icd10_code_id, description=r.description) for r in rows]

    def get_hcpcs(self, article_id: str) -> list[CodeEntry]:
        with self._session() as db:
            latest_version = self._get_latest_version(db, article_id)
            if latest_version is None:
                return []
            stmt = select(ArticleHcpcsCode).where(
                ArticleHcpcsCode.article_id == article_id,
                ArticleHcpcsCode.article_version == latest_version
            )
            rows = db.scalars(stmt).all()
            return [CodeEntry(code=r.hcpcs_code_id, description=r.long_description or r.short_description) for r in rows]
