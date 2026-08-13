"""Mock NCD repository.

⚠️  THIS IS MOCK DATA — FOR DEVELOPMENT AND DEMO PURPOSES ONLY ⚠️
"""
from __future__ import annotations

from datetime import date

from app.schemas.ncd import NCDResponse


_NCDS: dict[str, NCDResponse] = {
    "N123": NCDResponse(
        id="N123",
        title="Transcutaneous Electrical Nerve Stimulation (TENS) for Acute Pain",
        effective_date=date(2012, 3, 1),
        end_date=None,
        description=(
            "Medicare covers TENS for acute pain as a complement to other "
            "therapeutic modalities for the relief of acute post-operative pain."
        ),
        manual_section="160.7.1",
        decision="COVERED_WITH_CONDITIONS",
    ),
}


class MockNCDRepository:
    """In-memory NCD repository for development and testing."""

    def get_by_id(self, ncd_id: str) -> NCDResponse | None:
        return _NCDS.get(ncd_id.upper())
