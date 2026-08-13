"""PostgreSQL LCD repository.

Supports composite version primary keys.

Cleaned up and decluttered by Vedarathna.
"""
from __future__ import annotations

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.lcd import LCD, LCDHCPCSCode, LCDIcd10Covered, LCDIcd10NonCovered
from app.schemas.article import CodeEntry
from app.schemas.lcd import LCDResponse


def _lcd_to_schema(row: LCD) -> LCDResponse:
    article_ids = [a.strip() for a in (row.associated_article_ids or "").split(",") if a.strip()]
    return LCDResponse(
        id=row.lcd_id,
        title=row.title or "",
        version=str(row.lcd_version),
        effective_date=row.orig_det_eff_date,
        end_date=row.date_retired,
        jurisdiction=None,  # Handled dynamically or via seed mapping
        contractor=None,    # Handled dynamically
        associated_article_ids=article_ids,
        hcpcs_codes=[CodeEntry(code=c.hcpcs_code, description=c.description) for c in row.hcpcs_codes],
        icd10_covered=[CodeEntry(code=c.icd10_code, description=c.description) for c in row.icd10_covered],
        icd10_noncovered=[CodeEntry(code=c.icd10_code, description=c.description) for c in row.icd10_noncovered],
    )


class PostgresLCDRepository:
    """SQLAlchemy-backed LCD repository."""

    def _session(self):  # type: ignore[no-untyped-def]
        return SessionLocal()

    def _get_latest_version(self, db, lcd_id: str) -> int | None:
        stmt = (
            select(LCD.lcd_version)
            .where(LCD.lcd_id == lcd_id)
            .order_by(LCD.lcd_version.desc())
            .limit(1)
        )
        return db.scalars(stmt).first()

    def get_by_id(self, lcd_id: str) -> LCDResponse | None:
        """Return the latest version of the LCD."""
        with self._session() as db:
            latest_version = self._get_latest_version(db, lcd_id)
            if latest_version is None:
                return None
            row = db.get(LCD, (lcd_id, latest_version))
            return _lcd_to_schema(row) if row else None

