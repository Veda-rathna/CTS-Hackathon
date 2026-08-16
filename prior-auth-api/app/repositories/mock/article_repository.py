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
    "A56157": ArticleResponse(
        id="A56157",
        version="1",
        display_id="A56157",
        title="Billing and Coding: Intraarticular Knee Injections of Hyaluronan",
        publication_number="100-3",
        effective_date=date(2023, 1, 1),
        end_date=None,
        description="Coverage article for hyaluronan knee injections.",
        status="ACTIVE",
    ),
    "A59487": ArticleResponse(
        id="A59487",
        version="1",
        display_id="A59487",
        title="Billing and Coding: Trigger Point Injections (TPI)",
        publication_number="100-3",
        effective_date=date(2023, 1, 1),
        end_date=None,
        description="Coverage article for trigger point injections.",
        status="ACTIVE",
    ),
}

_ICD10_COVERED: dict[str, list[CodeEntry]] = {
    "A12345": [
        CodeEntry(code="M54.16", description="Radiculopathy, lumbar region"),
        CodeEntry(code="M54.17", description="Radiculopathy, lumbosacral region"),
        CodeEntry(code="M54.4", description="Lumbago with sciatica"),
        CodeEntry(code="M47.816", description="Spondylosis with radiculopathy, lumbar region"),
    ],
    "A56157": [
        CodeEntry(code="M17.0", description="Bilateral primary osteoarthritis of knee"),
        CodeEntry(code="M17.11", description="Unilateral primary osteoarthritis, right knee"),
        CodeEntry(code="M17.12", description="Unilateral primary osteoarthritis, left knee"),
        CodeEntry(code="M17.2", description="Bilateral post-traumatic osteoarthritis of knee"),
    ],
    "A59487": [
        CodeEntry(code="M79.10", description="Myalgia, unspecified site"),
        CodeEntry(code="M79.11", description="Myalgia of mastication muscle"),
        CodeEntry(code="M79.12", description="Myalgia of auxiliary muscles of head and neck"),
        CodeEntry(code="M79.18", description="Myalgia, other site"),
    ],
    "A99999": [],
}

_ICD10_NONCOVERED: dict[str, list[CodeEntry]] = {
    "A12345": [
        CodeEntry(code="Z00.00", description="Encounter for general adult medical examination without abnormal findings"),
        CodeEntry(code="Z00.01", description="Encounter for general adult medical examination with abnormal findings"),
    ],
    "A56157": [],

    "A59487": [
        CodeEntry(code="M25.50", description="Pain in unspecified joint"),
        CodeEntry(code="M25.511", description="Pain in right shoulder"),
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
    "A56157": [
        CodeEntry(
            code="20610",
            description="Arthrocentesis, aspiration and/or injection, major joint or bursa",
        ),
    ],
    "A59487": [
        CodeEntry(
            code="20552",
            description="Injection(s), single or multiple trigger point(s), 1 or 2 muscle(s)",
        ),
        CodeEntry(
            code="20553",
            description="Injection(s), single or multiple trigger point(s), 3 or more muscle(s)",
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
