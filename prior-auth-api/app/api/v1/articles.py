"""Article endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.repositories import get_article_service
from app.schemas.article import ArticleResponse, HCPCSCodesResponse, ICD10CodesResponse
from app.schemas.common import ErrorResponse
from app.services.article_service import ArticleService

router = APIRouter(prefix="/articles", tags=["Articles"])

_404_responses = {
    404: {"model": ErrorResponse, "description": "Article not found"},
}


@router.get(
    "/{article_id}",
    response_model=ArticleResponse,
    responses=_404_responses,
    summary="Get article by ID",
    description=(
        "Returns the full article record for the given CMS article identifier. "
        "Returns **404** if the article does not exist."
    ),
)
def get_article(
    article_id: str,
    service: Annotated[ArticleService, Depends(get_article_service)],
) -> ArticleResponse:
    return service.get_article(article_id)


@router.get(
    "/{article_id}/icd10-covered",
    response_model=ICD10CodesResponse,
    responses=_404_responses,
    summary="Get covered ICD-10 codes for an article",
    description=(
        "Returns the list of ICD-10 diagnosis codes that are **covered** "
        "under this article.  Returns **404** if the article does not exist."
    ),
)
def get_icd10_covered(
    article_id: str,
    service: Annotated[ArticleService, Depends(get_article_service)],
) -> ICD10CodesResponse:
    return service.get_icd10_covered(article_id)


@router.get(
    "/{article_id}/icd10-noncovered",
    response_model=ICD10CodesResponse,
    responses=_404_responses,
    summary="Get non-covered ICD-10 codes for an article",
    description=(
        "Returns the list of ICD-10 diagnosis codes that are **explicitly not covered** "
        "under this article.  Returns **404** if the article does not exist."
    ),
)
def get_icd10_noncovered(
    article_id: str,
    service: Annotated[ArticleService, Depends(get_article_service)],
) -> ICD10CodesResponse:
    return service.get_icd10_noncovered(article_id)


@router.get(
    "/{article_id}/hcpcs",
    response_model=HCPCSCodesResponse,
    responses=_404_responses,
    summary="Get HCPCS/CPT codes for an article",
    description=(
        "Returns the HCPCS and CPT procedure codes referenced in this article. "
        "Returns **404** if the article does not exist."
    ),
)
def get_hcpcs(
    article_id: str,
    service: Annotated[ArticleService, Depends(get_article_service)],
) -> HCPCSCodesResponse:
    return service.get_hcpcs(article_id)
