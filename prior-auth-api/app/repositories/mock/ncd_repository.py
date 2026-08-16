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
        title="Covered Demo NCD",
        effective_date=date(2010, 1, 1),
        end_date=None,
        description="Explicitly covered demo procedure under NCD.",
        decision="COVERED",
    ),
    # Demo: explicitly excluded procedure NCD
    "N222": NCDResponse(
        id="N222",
        title="Excluded Demo NCD",
        effective_date=date(2010, 1, 1),
        end_date=None,
        description="Explicitly excluded demo procedure under NCD.",
        decision="EXCLUDED",
    ),
    # NCD 373 — Acupuncture / Trigger Point Exclusion
    "373": NCDResponse(
        id="373",
        title="Acupuncture for Chronic Lower Back Pain (cLBP)",
        effective_date=date(2020, 1, 21),
        end_date=None,
        description="Acupuncture is explicitly non-covered for non-indicated procedures.",
        decision="EXCLUDED",
    ),
    "NCD-373": NCDResponse(
        id="NCD-373",
        title="Acupuncture for Chronic Lower Back Pain (cLBP)",
        effective_date=date(2020, 1, 21),
        end_date=None,
        description="Acupuncture is explicitly non-covered for non-indicated procedures.",
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
        CodeEntry(code="38240", description="Allogeneic hematopoietic stem cell transplantation"),
        CodeEntry(code="38241", description="Autologous hematopoietic stem cell transplantation"),
        CodeEntry(code="38242", description="Allogeneic donor lymphocyte infusions"),
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
    "373": [
        CodeEntry(code="20552", description="Injection(s), single or multiple trigger point(s), 1 or 2 muscle(s)"),
        CodeEntry(code="20553", description="Injection(s), single or multiple trigger point(s), 3 or more muscle(s)"),
    ],
    "NCD-373": [
        CodeEntry(code="20552", description="Injection(s), single or multiple trigger point(s), 1 or 2 muscle(s)"),
        CodeEntry(code="20553", description="Injection(s), single or multiple trigger point(s), 3 or more muscle(s)"),
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
