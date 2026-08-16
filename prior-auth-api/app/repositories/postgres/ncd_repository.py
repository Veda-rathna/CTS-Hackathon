"""PostgreSQL NCD repository.

Supports composite version primary keys.
"""
from __future__ import annotations

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.ncd import NCD
from app.schemas.ncd import NCDResponse


class PostgresNCDRepository:
    """SQLAlchemy-backed NCD repository."""

    def _session(self):  # type: ignore[no-untyped-def]
        return SessionLocal()

    def _get_latest_version(self, db, ncd_id: str) -> int | None:
        stmt = (
            select(NCD.document_version)
            .where(NCD.document_id == ncd_id)
            .order_by(NCD.document_version.desc())
            .limit(1)
        )
        return db.scalars(stmt).first()

    def get_by_id(self, ncd_id: str) -> NCDResponse | None:
        """Return the latest version of the NCD."""
        with self._session() as db:
            latest_version = self._get_latest_version(db, ncd_id)
            if latest_version is None:
                return None
            row = db.get(NCD, (ncd_id, latest_version))
            if row is None:
                return None
            return NCDResponse(
                id=row.document_id,
                title=row.title or "",
                effective_date=row.effective_date,
                end_date=row.effective_end_date,
                description=row.item_service_description or row.indications_limitations,
                manual_section=row.document_display_id,
                decision=row.decision,
            )

    def get_hcpcs(self, ncd_id: str) -> list[CodeEntry]:
        """Return HCPCS codes associated with the specified NCD."""
        from app.models.ncd import NCDHCPCSCode
        from app.schemas.article import CodeEntry
        with self._session() as db:
            latest_version = self._get_latest_version(db, ncd_id)
            if latest_version is None:
                return []
            stmt = select(NCDHCPCSCode).where(
                NCDHCPCSCode.ncd_id == ncd_id,
                NCDHCPCSCode.ncd_version == latest_version,
            )
            rows = db.scalars(stmt).all()
            return [CodeEntry(code=r.hcpcs_code, description=r.description or "") for r in rows]

