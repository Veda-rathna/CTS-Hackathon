"""PostgreSQL Policy repository.

Implements cross-entity policy search by querying LCD (and later NCD) tables.

⚠️  INTEGRATION NOTE: This implementation queries LCDs joined with their HCPCS
    codes and jurisdictions.  When the data team delivers the final schema,
    update the joins here.  The service layer will NOT change.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.lcd import LCD, LCDHCPCSCode, LCDIcd10Covered
from app.models.jurisdiction import Jurisdiction
from app.schemas.policy import PolicyMatch


def _is_effective(effective_date: date | None, end_date: date | None, as_of: date | None) -> bool:
    check = as_of or date.today()
    if effective_date and effective_date > check:
        return False
    if end_date and end_date < check:
        return False
    return True


class PostgresPolicyRepository:
    """SQLAlchemy-backed cross-entity policy search."""

    def _session(self):  # type: ignore[no-untyped-def]
        return SessionLocal()

    def find_policies_for_procedure(self, procedure_code: str) -> list[PolicyMatch]:
        with self._session() as db:
            stmt = (
                select(LCD)
                .join(LCDHCPCSCode, LCD.id == LCDHCPCSCode.lcd_id)
                .where(LCDHCPCSCode.hcpcs_code == procedure_code)
                .distinct()
            )
            rows = db.scalars(stmt).all()
            result: list[PolicyMatch] = []
            for row in rows:
                article_ids = [
                    a.strip()
                    for a in (row.associated_article_ids or "").split(",")
                    if a.strip()
                ]
                result.append(
                    PolicyMatch(
                        policy_type="LCD",
                        policy_id=row.id,
                        title=row.title,
                        article_id=article_ids[0] if article_ids else None,
                        jurisdiction_id=row.jurisdiction_id,
                        effective_date=row.effective_date,
                        end_date=row.end_date,
                        effective=_is_effective(row.effective_date, row.end_date, None),
                    )
                )
            return result

    def search(
        self,
        procedure_code: str,
        diagnosis_code: str | None = None,
        state: str | None = None,
        payer: str | None = None,
        policy_type: str | None = None,
        effective_date: date | None = None,
    ) -> list[PolicyMatch]:
        candidates = self.find_policies_for_procedure(procedure_code)
        results: list[PolicyMatch] = []

        with self._session() as db:
            for p in candidates:
                if policy_type and p.policy_type.upper() != policy_type.upper():
                    continue

                p.procedure_match = True
                p.effective = _is_effective(p.effective_date, p.end_date, effective_date)

                # Jurisdiction/state check
                if state and p.jurisdiction_id:
                    jur: Jurisdiction | None = db.get(Jurisdiction, p.jurisdiction_id)
                    if jur and jur.states:
                        state_list = [s.strip().upper() for s in jur.states.split(",")]
                        p.jurisdiction_match = state.upper() in state_list
                    else:
                        p.jurisdiction_match = False
                else:
                    p.jurisdiction_match = state is None  # no filter = applicable

                # Diagnosis check
                if diagnosis_code and p.article_id:
                    covered_stmt = select(LCDIcd10Covered).where(
                        LCDIcd10Covered.lcd_id == p.policy_id,
                        LCDIcd10Covered.icd10_code == diagnosis_code,
                    )
                    p.diagnosis_match = db.scalars(covered_stmt).first() is not None

                results.append(p)

        return results
