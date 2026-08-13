"""Mock Article repository.

Contains deterministic, in-memory demonstration data.

⚠️  THIS IS MOCK DATA — FOR DEVELOPMENT AND DEMO PURPOSES ONLY ⚠️
     It does not represent real CMS policy information.

When the data team delivers the PostgreSQL schema, replace this with
``app/repositories/postgres/article_repository.py`` and set
``USE_MOCK_REPOSITORIES=false`` in the environment.
"""
from __future__ import annotations

from datetime import date

from app.schemas.article import ArticleResponse, CodeEntry


# ── Static mock data ──────────────────────────────────────────────────────────

_ARTICLES: dict[str, ArticleResponse] = {
    "A12345": ArticleResponse(
        id="A12345",
        version="1",
        display_id="A12345",
        title="Injections — Epidural Steroid (Medicare)",
        publication_number="100-3",
        effective_date=date(2023, 1, 1),
        end_date=None,
        description=(
            "Coverage article for epidural steroid injections under Medicare. "
            "Covers medically necessary injections for specified diagnoses."
        ),
        status="ACTIVE",
    ),
    "A99999": ArticleResponse(
        id="A99999",
        version="2",
        display_id="A99999",
        title="Expired Demo Article",
        publication_number="999-1",
        effective_date=date(2010, 1, 1),
        end_date=date(2015, 12, 31),
        description="Demonstration expired article.",
        status="RETIRED",
    ),
}

_ICD10_COVERED: dict[str, list[CodeEntry]] = {
    "A12345": [
        CodeEntry(code="M54.16", description="Radiculopathy, lumbar region"),
        CodeEntry(code="M54.17", description="Radiculopathy, lumbosacral region"),
        CodeEntry(code="M54.4", description="Lumbago with sciatica"),
        CodeEntry(code="M47.816", description="Spondylosis with radiculopathy, lumbar region"),
    ],
    "A99999": [],
}

_ICD10_NONCOVERED: dict[str, list[CodeEntry]] = {
    "A12345": [
        CodeEntry(code="Z00.00", description="Encounter for general adult medical examination without abnormal findings"),
        CodeEntry(code="Z00.01", description="Encounter for general adult medical examination with abnormal findings"),
    ],
    "A99999": [],
}

_HCPCS: dict[str, list[CodeEntry]] = {
    "A12345": [
        CodeEntry(
            code="64483",
            description="Injection(s), anesthetic agent and/or steroid, transforaminal epidural; lumbar or sacral, single level",
        ),
        CodeEntry(
            code="64484",
            description="Injection(s), anesthetic agent and/or steroid, transforaminal epidural; lumbar or sacral, each additional level",
        ),
        CodeEntry(
            code="62321",
            description="Injection(s), of diagnostic or therapeutic substance(s) including anesthetic, antispasmodic, opioid, steroid, other solution; cervical or thoracic, interlaminar epidural or subarachnoid",
        ),
    ],
    "A99999": [],
}


# ── Repository class ──────────────────────────────────────────────────────────


class MockArticleRepository:
    """In-memory Article repository for development and testing."""

    def get_by_id(self, article_id: str) -> ArticleResponse | None:
        """Return the article or ``None`` if not found."""
        return _ARTICLES.get(article_id.upper())

    def get_icd10_covered(self, article_id: str) -> list[CodeEntry]:
        """Return covered ICD-10 codes for the given article."""
        return _ICD10_COVERED.get(article_id.upper(), [])

    def get_icd10_noncovered(self, article_id: str) -> list[CodeEntry]:
        """Return non-covered ICD-10 codes for the given article."""
        return _ICD10_NONCOVERED.get(article_id.upper(), [])

    def get_hcpcs(self, article_id: str) -> list[CodeEntry]:
        """Return HCPCS/CPT codes for the given article."""
        return _HCPCS.get(article_id.upper(), [])
