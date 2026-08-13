"""PostgreSQL Article repository.

Uses SQLAlchemy 2.x to query the articles table and related code tables.

⚠️  INTEGRATION NOTE: When the data team delivers the final PostgreSQL schema,
    update the column/table names in this file and ``app/models/article.py``.
    The service layer and API routers will NOT need to change.

    Currently requires a database session.  For simplicity the session is
    created internally.  To pass a session in via DI, inject ``get_db``
    from ``app.db.session``.
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

    def get_by_id(self, article_id: str) -> ArticleResponse | None:
        """Return the article or ``None`` if not found."""
        with self._session() as db:
            row: Article | None = db.get(Article, article_id)
            if row is None:
                return None
            return ArticleResponse(
                id=row.id,
                version=row.version,
                display_id=row.display_id,
                title=row.title,
                publication_number=row.publication_number,
                effective_date=row.effective_date,
                end_date=row.end_date,
                description=row.description,
                status=row.status,
            )

    def get_icd10_covered(self, article_id: str) -> list[CodeEntry]:
        with self._session() as db:
            stmt = select(ArticleIcd10Covered).where(
                ArticleIcd10Covered.article_id == article_id
            )
            rows = db.scalars(stmt).all()
            return [CodeEntry(code=r.icd10_code, description=r.description) for r in rows]

    def get_icd10_noncovered(self, article_id: str) -> list[CodeEntry]:
        with self._session() as db:
            stmt = select(ArticleIcd10NonCovered).where(
                ArticleIcd10NonCovered.article_id == article_id
            )
            rows = db.scalars(stmt).all()
            return [CodeEntry(code=r.icd10_code, description=r.description) for r in rows]

    def get_hcpcs(self, article_id: str) -> list[CodeEntry]:
        with self._session() as db:
            stmt = select(ArticleHcpcsCode).where(
                ArticleHcpcsCode.article_id == article_id
            )
            rows = db.scalars(stmt).all()
            return [CodeEntry(code=r.hcpcs_code, description=r.description) for r in rows]
