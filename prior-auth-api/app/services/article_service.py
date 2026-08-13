"""Article service — business logic for article-related operations."""
from __future__ import annotations

from app.exceptions.handlers import ResourceNotFoundError
from app.repositories.interfaces.article_repository import ArticleRepository
from app.schemas.article import ArticleResponse, CodeEntry, ICD10CodesResponse, HCPCSCodesResponse


class ArticleService:
    """Orchestrates article retrieval and delegates to the repository.

    This service contains no SQL and no framework-specific code.
    It depends only on the ``ArticleRepository`` protocol.
    """

    def __init__(self, repository: ArticleRepository) -> None:
        self._repo = repository

    def get_article(self, article_id: str) -> ArticleResponse:
        """Return the article or raise ``ResourceNotFoundError``."""
        article = self._repo.get_by_id(article_id.strip().upper())
        if article is None:
            raise ResourceNotFoundError(
                f"Article '{article_id}' was not found.",
                details={"article_id": article_id},
            )
        return article

    def get_icd10_covered(self, article_id: str) -> ICD10CodesResponse:
        """Return covered ICD-10 codes for an article.

        Raises ``ResourceNotFoundError`` if the article itself does not exist.
        """
        self.get_article(article_id)  # validates existence
        codes: list[CodeEntry] = self._repo.get_icd10_covered(article_id.strip().upper())
        return ICD10CodesResponse(article_id=article_id.upper(), codes=codes)

    def get_icd10_noncovered(self, article_id: str) -> ICD10CodesResponse:
        """Return non-covered ICD-10 codes for an article."""
        self.get_article(article_id)
        codes: list[CodeEntry] = self._repo.get_icd10_noncovered(article_id.strip().upper())
        return ICD10CodesResponse(article_id=article_id.upper(), codes=codes)

    def get_hcpcs(self, article_id: str) -> HCPCSCodesResponse:
        """Return HCPCS/CPT codes for an article."""
        self.get_article(article_id)
        codes: list[CodeEntry] = self._repo.get_hcpcs(article_id.strip().upper())
        return HCPCSCodesResponse(article_id=article_id.upper(), codes=codes)
