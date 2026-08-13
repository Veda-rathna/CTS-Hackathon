"""PostgreSQL LCD repository.

⚠️  INTEGRATION NOTE: Update column/table names when the data team delivers
    the final schema. Only this file and ``app/models/lcd.py`` need to change.
"""
from __future__ import annotations

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.lcd import LCD, LCDHCPCSCode, LCDIcd10Covered, LCDIcd10NonCovered
from app.schemas.article import CodeEntry
from app.schemas.lcd import ContractorSummary, JurisdictionSummary, LCDResponse


def _lcd_to_schema(row: LCD) -> LCDResponse:
    article_ids = [a.strip() for a in (row.associated_article_ids or "").split(",") if a.strip()]
    return LCDResponse(
        id=row.id,
        title=row.title,
        version=row.version,
        effective_date=row.effective_date,
        end_date=row.end_date,
        jurisdiction=(
            JurisdictionSummary(id=row.jurisdiction.id, name=row.jurisdiction.name)
            if row.jurisdiction
            else None
        ),
        contractor=(
            ContractorSummary(id=row.contractor.id, name=row.contractor.name)
            if row.contractor
            else None
        ),
        associated_article_ids=article_ids,
        hcpcs_codes=[CodeEntry(code=c.hcpcs_code, description=c.description) for c in row.hcpcs_codes],
        icd10_covered=[CodeEntry(code=c.icd10_code, description=c.description) for c in row.icd10_covered],
        icd10_noncovered=[CodeEntry(code=c.icd10_code, description=c.description) for c in row.icd10_noncovered],
    )


class PostgresLCDRepository:
    """SQLAlchemy-backed LCD repository."""

    def _session(self):  # type: ignore[no-untyped-def]
        return SessionLocal()

    def get_by_id(self, lcd_id: str) -> LCDResponse | None:
        with self._session() as db:
            row: LCD | None = db.get(LCD, lcd_id)
            return _lcd_to_schema(row) if row else None

    def find_by_hcpcs_code(self, hcpcs_code: str) -> list[LCDResponse]:
        with self._session() as db:
            stmt = (
                select(LCD)
                .join(LCDHCPCSCode, LCD.id == LCDHCPCSCode.lcd_id)
                .where(LCDHCPCSCode.hcpcs_code == hcpcs_code)
                .distinct()
            )
            rows = db.scalars(stmt).all()
            return [_lcd_to_schema(r) for r in rows]

    def find_by_jurisdiction(self, jurisdiction_id: str) -> list[LCDResponse]:
        with self._session() as db:
            stmt = select(LCD).where(LCD.jurisdiction_id == jurisdiction_id)
            rows = db.scalars(stmt).all()
            return [_lcd_to_schema(r) for r in rows]
