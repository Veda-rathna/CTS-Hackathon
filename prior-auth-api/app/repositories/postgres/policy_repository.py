"""PostgreSQL Policy repository.

Supports composite version primary keys.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.lcd import LCD, LCDHCPCSCode, LCDIcd10Covered
from app.models.jurisdiction import Jurisdiction
from app.models.ncd import NCD, LCDNCDAssociation, NCDHCPCSCode
from app.models.state import State
from app.schemas.policy import PolicyMatch
from typing import Any


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

    def is_state_in_jurisdiction(self, state: str, policy: PolicyMatch) -> bool:
        """Check if a state falls within the policy's jurisdiction via DB lookup."""
        if policy.policy_type.upper() != "LCD":
            # NCDs are national — always in jurisdiction
            return True
        with self._session() as db:
            # Get the latest version for this LCD
            stmt_ver = (
                select(LCD.lcd_version)
                .where(LCD.lcd_id == policy.policy_id)
                .order_by(LCD.lcd_version.desc())
                .limit(1)
            )
            latest_ver = db.scalars(stmt_ver).first()
            if latest_ver is None:
                return False
            state_stmt = (
                select(State.state_code)
                .join(Jurisdiction, State.state_id == Jurisdiction.state_id)
                .where(
                    Jurisdiction.lcd_id == policy.policy_id,
                    Jurisdiction.lcd_version == latest_ver,
                )
            )
            state_list = [s.strip().upper() for s in db.scalars(state_stmt).all()]
            return state.upper() in state_list

    def find_policies_for_procedure(self, procedure_code: str) -> list[PolicyMatch]:
        with self._session() as db:
            # Query matching LCDs (joining on both id and version for safety)
            stmt = (
                select(LCD)
                .join(LCDHCPCSCode, (LCD.lcd_id == LCDHCPCSCode.lcd_id) & (LCD.lcd_version == LCDHCPCSCode.lcd_version))
                .where(LCDHCPCSCode.hcpcs_code == procedure_code)
                .distinct()
            )
            rows = db.scalars(stmt).all()
            result: list[PolicyMatch] = []
            
            # Group and take latest versions of LCDs to return
            seen = set()
            for row in rows:
                if row.lcd_id not in seen:
                    seen.add(row.lcd_id)
                    article_ids = [
                        a.strip()
                        for a in (row.associated_article_ids or "").split(",")
                        if a.strip()
                    ]
                    result.append(
                        PolicyMatch(
                            policy_type="LCD",
                            policy_id=row.lcd_id,
                            title=row.title,
                            article_id=article_ids[0] if article_ids else None,
                            jurisdiction_id=None,  # Populated dynamically via states lookup
                            effective_date=row.orig_det_eff_date,
                            end_date=row.date_retired,
                            effective=_is_effective(row.orig_det_eff_date, row.date_retired, None),
                        )
                    )
            
            # Find and append linked NCD policies
            matched_lcd_ids = list(seen)
            seen_ncd = set()
            
            # 1. NCDs found via LCD bridge
            if matched_lcd_ids:
                ncd_stmt = (
                    select(NCD)
                    .join(LCDNCDAssociation, (NCD.document_id == LCDNCDAssociation.ncd_id) & (NCD.document_version == LCDNCDAssociation.ncd_version))
                    .where(LCDNCDAssociation.lcd_id.in_(matched_lcd_ids))
                    .distinct()
                )
                ncd_rows = db.scalars(ncd_stmt).all()
                for ncd in ncd_rows:
                    if ncd.document_id not in seen_ncd:
                        seen_ncd.add(ncd.document_id)
                        result.append(
                            PolicyMatch(
                                policy_type="NCD",
                                policy_id=ncd.document_id,
                                title=ncd.title,
                                effective_date=ncd.effective_date,
                                end_date=ncd.effective_end_date,
                                effective=_is_effective(ncd.effective_date, ncd.effective_end_date, None),
                            )
                        )

            # 2. Standalone NCDs found via direct HCPCS crosswalk
            direct_ncd_stmt = (
                select(NCD)
                .join(NCDHCPCSCode, (NCD.document_id == NCDHCPCSCode.ncd_id) & (NCD.document_version == NCDHCPCSCode.ncd_version))
                .where(NCDHCPCSCode.hcpcs_code == procedure_code)
                .distinct()
            )
            direct_ncd_rows = db.scalars(direct_ncd_stmt).all()
            for ncd in direct_ncd_rows:
                if ncd.document_id not in seen_ncd:
                    seen_ncd.add(ncd.document_id)
                    result.append(
                        PolicyMatch(
                            policy_type="NCD",
                            policy_id=ncd.document_id,
                            title=ncd.title,
                            effective_date=ncd.effective_date,
                            end_date=ncd.effective_end_date,
                            effective=_is_effective(ncd.effective_date, ncd.effective_end_date, None),
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
                
                # Fetch latest version number to verify children
                if p.policy_type == "LCD":
                    stmt_ver = select(LCD.lcd_version).where(LCD.lcd_id == p.policy_id).order_by(LCD.lcd_version.desc()).limit(1)
                else:
                    stmt_ver = select(NCD.document_version).where(NCD.document_id == p.policy_id).order_by(NCD.document_version.desc()).limit(1)
                latest_ver = db.scalars(stmt_ver).first()
                if latest_ver is None:
                    continue

                p.effective = _is_effective(p.effective_date, p.end_date, effective_date)

                # Jurisdiction/state check via jurisdictions join states table
                if state and p.policy_type == "LCD":
                    state_stmt = (
                        select(State.state_code)
                        .join(Jurisdiction, State.state_id == Jurisdiction.state_id)
                        .where(
                            Jurisdiction.lcd_id == p.policy_id,
                            Jurisdiction.lcd_version == latest_ver
                        )
                    )
                    state_list = [s.strip().upper() for s in db.scalars(state_stmt).all()]
                    p.jurisdiction_match = state.upper() in state_list
                else:
                    p.jurisdiction_match = True  # NCDs are national, and state=None maps to True

                # Diagnosis check
                if diagnosis_code and p.policy_type == "LCD":
                    covered_stmt = select(LCDIcd10Covered).where(
                        LCDIcd10Covered.lcd_id == p.policy_id,
                        LCDIcd10Covered.lcd_version == latest_ver,
                        LCDIcd10Covered.icd10_code == diagnosis_code,
                    )
                    p.diagnosis_match = db.scalars(covered_stmt).first() is not None

                results.append(p)

        return results

    def upsert_policy(self, normalized_data: dict[str, Any]) -> None:
        """Upsert a normalized policy (LCD or Article) into the database transactionally."""
        with self._session() as db:
            try:
                # 1. Merge the main policy entity
                policy_obj = normalized_data["policy"]
                db.merge(policy_obj)
                
                # 2. Merge related HCPCS codes
                for h in normalized_data.get("hcpcs", []):
                    db.merge(h)
                    
                # 3. Merge related ICD-10 covered codes
                for icd in normalized_data.get("icd10_covered", []):
                    db.merge(icd)
                    
                # 4. Merge related ICD-10 non-covered codes
                for icd in normalized_data.get("icd10_noncovered", []):
                    db.merge(icd)
                    
                db.commit()
            except Exception as e:
                db.rollback()
                raise e
