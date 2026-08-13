"""Mock LCD repository.

⚠️  THIS IS MOCK DATA — FOR DEVELOPMENT AND DEMO PURPOSES ONLY ⚠️
"""
from __future__ import annotations

from datetime import date

from app.schemas.article import CodeEntry
from app.schemas.lcd import LCDResponse, JurisdictionSummary, ContractorSummary


# ── Static mock data ──────────────────────────────────────────────────────────

_LCDS: dict[str, LCDResponse] = {
    "L39054": LCDResponse(
        id="L39054",
        title="Epidural Injections for Pain Management",
        version="1",
        effective_date=date(2023, 1, 1),
        end_date=None,
        jurisdiction=JurisdictionSummary(id="J5", name="Jurisdiction 5"),
        contractor=ContractorSummary(id="12301", name="Novitas Solutions"),
        associated_article_ids=["A12345"],
        hcpcs_codes=[
            CodeEntry(
                code="64483",
                description="Transforaminal epidural injection, lumbar/sacral, single level",
            ),
            CodeEntry(
                code="64484",
                description="Transforaminal epidural injection, lumbar/sacral, each additional level",
            ),
        ],
        icd10_covered=[
            CodeEntry(code="M54.16", description="Radiculopathy, lumbar region"),
            CodeEntry(code="M54.17", description="Radiculopathy, lumbosacral region"),
            CodeEntry(code="M54.4", description="Lumbago with sciatica"),
        ],
        icd10_noncovered=[
            CodeEntry(code="Z00.00", description="General adult examination without abnormal findings"),
        ],
    ),
    "L99001": LCDResponse(
        id="L99001",
        title="Expired Demo LCD",
        version="1",
        effective_date=date(2010, 1, 1),
        end_date=date(2015, 12, 31),
        jurisdiction=JurisdictionSummary(id="J8", name="Jurisdiction 8"),
        contractor=ContractorSummary(id="99001", name="Demo MAC"),
        associated_article_ids=[],
        hcpcs_codes=[CodeEntry(code="64483", description="Demo")],
        icd10_covered=[],
        icd10_noncovered=[],
    ),
}

# HCPCS → LCD mapping for quick lookup
_HCPCS_TO_LCDS: dict[str, list[str]] = {
    "64483": ["L39054", "L99001"],
    "64484": ["L39054"],
    "62321": ["L39054"],
}

# Jurisdiction → LCD mapping
_JURISDICTION_TO_LCDS: dict[str, list[str]] = {
    "J5": ["L39054"],
    "J8": ["L99001"],
}


# ── Repository class ──────────────────────────────────────────────────────────


class MockLCDRepository:
    """In-memory LCD repository for development and testing."""

    def get_by_id(self, lcd_id: str) -> LCDResponse | None:
        return _LCDS.get(lcd_id.upper())

    def find_by_hcpcs_code(self, hcpcs_code: str) -> list[LCDResponse]:
        """Return all LCDs referencing the given HCPCS/CPT code."""
        lcd_ids = _HCPCS_TO_LCDS.get(hcpcs_code.upper(), [])
        return [_LCDS[lid] for lid in lcd_ids if lid in _LCDS]

    def find_by_jurisdiction(self, jurisdiction_id: str) -> list[LCDResponse]:
        """Return all LCDs within the given jurisdiction."""
        lcd_ids = _JURISDICTION_TO_LCDS.get(jurisdiction_id.upper(), [])
        return [_LCDS[lid] for lid in lcd_ids if lid in _LCDS]
