"""Mock NCD repository.

Contains deterministic, in-memory demonstration data modelled after real
CMS NCD data (document_id, document_display_id, indications_limitations, etc.).

⚠️  THIS IS MOCK DATA — FOR DEVELOPMENT AND DEMO PURPOSES ONLY ⚠️
"""
from __future__ import annotations

from datetime import date

from app.schemas.article import CodeEntry
from app.schemas.ncd import NCDResponse


# ── Static mock NCD data ──────────────────────────────────────────────────────
# Modelled after actual CMS NCD JSON fields provided in requirements.

_NCDS: dict[str, NCDResponse] = {
    # NCD 160.7.1 — TENS for Acute Pain (general demo NCD)
    "N123": NCDResponse(
        id="N123",
        title="Transcutaneous Electrical Nerve Stimulation (TENS) for Acute Pain",
        effective_date=date(2012, 3, 1),
        end_date=None,
        description="Medicare covers TENS for acute pain when conservative therapy fails.",
        manual_section="160.7.1",
        decision="COVERED_WITH_CONDITIONS",
    ),
    # NCD 110.23 — Stem Cell Transplantation (matches LCD 39513 sample data)
    "NCD-110.23": NCDResponse(
        id="NCD-110.23",
        title="Stem Cell Transplantation",
        effective_date=date(2010, 4, 7),
        end_date=None,
        description=(
            "Allogeneic hematopoietic stem cell transplantation (allo-HSCT) is covered "
            "for Leukemia, Aplastic Anemia, SCID, and Wiskott-Aldrich Syndrome when "
            "reasonable and necessary. Other indications remain at local MAC discretion."
        ),
        manual_section="110.23",
        decision="COVERED_WITH_CONDITIONS",
    ),
    # NCD 190.25 — Alpha-fetoprotein (matches document_id 121 in requirements)
    "NCD-190.25": NCDResponse(
        id="NCD-190.25",
        title="Alpha-fetoprotein",
        effective_date=date(2002, 11, 25),
        end_date=None,
        description=(
            "AFP is a polysaccharide found in some carcinomas. Effective as a biochemical "
            "marker for monitoring the response of certain malignancies to therapy. Covered "
            "for hepatocellular carcinoma in high-risk patients, and germ cell neoplasms."
        ),
        manual_section="190.25",
        decision="COVERED_WITH_CONDITIONS",
    ),
    # Demo: explicitly covered procedure NCD
    "N111": NCDResponse(
        id="N111",
        title="NCD for Covered Demo Procedure",
        effective_date=date(2010, 1, 1),
        end_date=None,
        description="Demo NCD that explicitly covers a procedure.",
        manual_section="100.1",
        decision="COVERED",
    ),
    # Demo: explicitly excluded procedure NCD
    "N222": NCDResponse(
        id="N222",
        title="NCD for Excluded Demo Procedure",
        effective_date=date(2010, 1, 1),
        end_date=None,
        description="Demo NCD that explicitly excludes a procedure.",
        manual_section="100.2",
        decision="EXCLUDED",
    ),
}


# ── NCD HCPCS mappings ────────────────────────────────────────────────────────
# Which HCPCS codes are referenced by each NCD.
# In production this comes from the CMS NCD covered-code lists (quarterly PDFs).

_NCD_HCPCS: dict[str, list[CodeEntry]] = {
    "N123": [
        CodeEntry(code="64550", description="Application of surface (transcutaneous) neurostimulator"),
    ],
    "NCD-110.23": [
        CodeEntry(code="38240", description="Hematopoietic progenitor cell (HPC); allogeneic transplantation"),
        CodeEntry(code="38241", description="Hematopoietic progenitor cell; autologous transplantation"),
        CodeEntry(code="38242", description="Allogeneic lymphocyte infusions"),
    ],
    "NCD-190.25": [
        CodeEntry(code="82105", description="Alpha-fetoprotein (AFP); serum"),
        CodeEntry(code="82106", description="Alpha-fetoprotein (AFP); amniotic fluid"),
    ],
    "N111": [
        CodeEntry(code="11111", description="Demo covered procedure"),
    ],
    "N222": [
        CodeEntry(code="22222", description="Demo excluded procedure"),
    ],
}


# ── Repository class ──────────────────────────────────────────────────────────


class MockNCDRepository:
    """In-memory NCD repository for development and testing.

    Implements the NCDRepository protocol including get_hcpcs() which is
    required by StructuredEvaluator.
    """

    def get_by_id(self, ncd_id: str) -> NCDResponse | None:
        """Return the NCD matching *ncd_id*, or None if not found."""
        return _NCDS.get(ncd_id.upper())

    def get_hcpcs(self, ncd_id: str) -> list[CodeEntry]:
        """Return HCPCS/CPT codes covered under this NCD.

        In production, these are sourced from the CMS quarterly covered-code
        lists linked from each NCD's 'other_text' field.
        """
        return _NCD_HCPCS.get(ncd_id.upper(), [])
