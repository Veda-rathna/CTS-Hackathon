"""PostgreSQL NCD repository."""
from __future__ import annotations

from app.db.session import SessionLocal
from app.models.ncd import NCD
from app.schemas.ncd import NCDResponse


class PostgresNCDRepository:
    """SQLAlchemy-backed NCD repository."""

    def _session(self):  # type: ignore[no-untyped-def]
        return SessionLocal()

    def get_by_id(self, ncd_id: str) -> NCDResponse | None:
        with self._session() as db:
            row: NCD | None = db.get(NCD, ncd_id)
            if row is None:
                return None
            return NCDResponse(
                id=row.id,
                title=row.title,
                effective_date=row.effective_date,
                end_date=row.end_date,
                description=row.description,
                manual_section=row.manual_section,
                decision=row.decision,
            )
