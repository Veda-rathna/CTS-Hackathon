"""Mock Policy repository.

Aggregates cross-entity search across Articles and LCDs for the triage engine.

⚠️  THIS IS MOCK DATA — FOR DEVELOPMENT AND DEMO PURPOSES ONLY ⚠️
"""
from __future__ import annotations

from datetime import date

from app.schemas.policy import PolicyMatch


# ── Jurisdiction → state mapping ──────────────────────────────────────────────
# The data team will provide the authoritative mapping via PostgreSQL.
# This is a best-effort demo mapping only.

_JURISDICTION_STATES: dict[str, list[str]] = {
    "J5": ["TX", "NM", "OK", "LA", "AR", "MS", "CO"],
    "J8": ["IA", "KS", "MO", "NE"],
    "JF": ["CA", "HI", "NV"],
    "JL": ["IL", "MN", "WI"],
    "JK": ["WA", "OR", "AK", "ID"],
}

# ── Policy catalogue ──────────────────────────────────────────────────────────

_POLICIES: list[PolicyMatch] = [
    PolicyMatch(
        policy_type="LCD",
        policy_id="L39054",
        title="Epidural Injections for Pain Management",
        article_id="A12345",
        jurisdiction_id="J5",
        effective_date=date(2023, 1, 1),
        end_date=None,
        procedure_match=False,
        diagnosis_match=False,
        jurisdiction_match=False,
        effective=True,
    ),
    PolicyMatch(
        policy_type="LCD",
        policy_id="L99001",
        title="Expired Demo LCD",
        article_id=None,
        jurisdiction_id="J8",
        effective_date=date(2010, 1, 1),
        end_date=date(2015, 12, 31),
        procedure_match=False,
        diagnosis_match=False,
        jurisdiction_match=False,
        effective=False,
    ),
]

# HCPCS → policy IDs
_HCPCS_TO_POLICY_IDX: dict[str, list[int]] = {
    "64483": [0, 1],
    "64484": [0],
    "62321": [0],
}


def _is_effective(policy: PolicyMatch, as_of: date | None = None) -> bool:
    check_date = as_of or date.today()
    if policy.effective_date and policy.effective_date > check_date:
        return False
    if policy.end_date and policy.end_date < check_date:
        return False
    return True


def _jurisdiction_matches(jurisdiction_id: str | None, state: str | None) -> bool:
    if jurisdiction_id is None or state is None:
        return False
    states = _JURISDICTION_STATES.get(jurisdiction_id, [])
    return state.upper() in states


class MockPolicyRepository:
    """In-memory Policy repository for development and testing."""

    def find_policies_for_procedure(self, procedure_code: str) -> list[PolicyMatch]:
        """Return all policies (active or not) referencing the procedure code."""
        indices = _HCPCS_TO_POLICY_IDX.get(procedure_code.upper(), [])
        return [_POLICIES[i].model_copy() for i in indices]

    def search(
        self,
        procedure_code: str,
        diagnosis_code: str | None = None,
        state: str | None = None,
        payer: str | None = None,
        policy_type: str | None = None,
        effective_date: date | None = None,
    ) -> list[PolicyMatch]:
        """Search policies by procedure code with optional filters.

        Each returned ``PolicyMatch`` has its match flags populated.
        """
        candidates = self.find_policies_for_procedure(procedure_code)
        results: list[PolicyMatch] = []

        for base in candidates:
            p = base.model_copy()

            # Apply policy_type filter
            if policy_type and p.policy_type.upper() != policy_type.upper():
                continue

            # Procedure always matches because we searched by it
            p.procedure_match = True

            # Effective date check
            p.effective = _is_effective(p, effective_date)

            # Jurisdiction / state check
            if state:
                p.jurisdiction_match = _jurisdiction_matches(p.jurisdiction_id, state)
            else:
                p.jurisdiction_match = True  # no filter → assume applicable

            # Diagnosis check (basic: does the policy have covered codes and does one match?)
            if diagnosis_code:
                from app.repositories.mock.article_repository import (
                    _ICD10_COVERED as COVERED,
                )
                article_id = p.article_id
                if article_id:
                    covered = {c.code for c in COVERED.get(article_id, [])}
                    p.diagnosis_match = diagnosis_code.upper() in covered
                else:
                    p.diagnosis_match = False
            else:
                p.diagnosis_match = False

            results.append(p)

        return results
