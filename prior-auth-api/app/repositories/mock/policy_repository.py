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
#
# Source: CMS MAC Jurisdiction boundaries.
# J5  = Novitas Solutions (TX, NM, OK, LA, AR, MS, CO)
# J8  = Wisconsin Physicians Service (IA, KS, MO, NE)
# JF  = Noridian Healthcare Solutions (CA, HI, NV)
# JL  = Wisconsin Physicians Service (IL, MN, WI)
# JK  = Noridian Healthcare Solutions (WA, OR, AK, ID)

_JURISDICTION_STATES: dict[str, list[str]] = {
    "J5": ["TX", "NM", "OK", "LA", "AR", "MS", "CO"],
    "J8": ["IA", "KS", "MO", "NE"],
    "JF": ["CA", "HI", "NV"],
    "JL": ["IL", "MN", "WI"],
    "JK": ["WA", "OR", "AK", "ID"],
}

# ── Policy catalogue ──────────────────────────────────────────────────────────
# Index  0: LCD L39054 — Epidural Injections (Jurisdiction J5 / TX)
# Index  1: LCD L99001 — Expired Demo LCD
# Index  2: NCD N111   — Demo covered NCD
# Index  3: NCD N222   — Demo excluded NCD
# Index  4: NCD NCD-110.23 — Stem Cell Transplantation (national, no jurisdiction)
# Index  5: NCD NCD-190.25 — Alpha-fetoprotein (national)

_POLICIES: list[PolicyMatch] = [
    # 0
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
    # 1
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
    # 2
    PolicyMatch(
        policy_type="NCD",
        policy_id="N111",
        title="NCD for Covered Demo Procedure",
        effective_date=date(2010, 1, 1),
        procedure_match=False,
        diagnosis_match=False,
        jurisdiction_match=False,
        effective=True,
    ),
    # 3
    PolicyMatch(
        policy_type="NCD",
        policy_id="N222",
        title="NCD for Excluded Demo Procedure",
        effective_date=date(2010, 1, 1),
        procedure_match=False,
        diagnosis_match=False,
        jurisdiction_match=False,
        effective=True,
    ),
    # 4 — NCD 110.23 Stem Cell Transplantation
    # NCDs are national: no jurisdiction_id restriction.
    PolicyMatch(
        policy_type="NCD",
        policy_id="NCD-110.23",
        title="Stem Cell Transplantation",
        article_id=None,
        jurisdiction_id=None,
        effective_date=date(2010, 4, 7),
        end_date=None,
        procedure_match=False,
        diagnosis_match=False,
        jurisdiction_match=False,
        effective=True,
    ),
    # 5 — NCD 190.25 Alpha-fetoprotein
    PolicyMatch(
        policy_type="NCD",
        policy_id="NCD-190.25",
        title="Alpha-fetoprotein",
        article_id=None,
        jurisdiction_id=None,
        effective_date=date(2002, 11, 25),
        end_date=None,
        procedure_match=False,
        diagnosis_match=False,
        jurisdiction_match=False,
        effective=True,
    ),
    # 6 — NCD N123 (160.7.1) TENS for Acute Pain
    PolicyMatch(
        policy_type="NCD",
        policy_id="N123",
        title="Transcutaneous Electrical Nerve Stimulation (TENS) for Acute Pain",
        article_id=None,
        jurisdiction_id=None,
        effective_date=date(2012, 3, 1),
        end_date=None,
        procedure_match=False,
        diagnosis_match=False,
        jurisdiction_match=False,
        effective=True,
    ),
]

# ── HCPCS → policy index mapping ──────────────────────────────────────────────
# Maps a procedure code to a list of indices into _POLICIES.
#
# Key insight:
#   • 64483/64484/62321 → governed by LCD L39054 + Article A12345.
#     NCDs do NOT explicitly address epidural injections nationally, so they
#     are correctly NOT_ADDRESSED at the NCD level — this is the real CMS
#     behavior. We include only the LCD entries.
#   • 38240/38241/38242 → governed by NCD 110.23 (Stem Cell Transplantation).
#     Included so the NCD evaluation path can be demonstrated.
#   • 82105/82106 → governed by NCD 190.25 (Alpha-fetoprotein).
#   • 11111/22222 → demo procedures for explicit covered/excluded NCD paths.

_HCPCS_TO_POLICY_IDX: dict[str, list[int]] = {
    # Epidural injections — LCD path only (NCD NOT_ADDRESSED is correct)
    "64483": [0, 1],
    "64484": [0],
    "62321": [0],
    # TENS neurostimulator — NCD N123 (160.7.1) path (index 6)
    "64550": [6],
    # Stem Cell Transplantation — NCD path (index 4 = NCD-110.23)
    "38240": [4],
    "38241": [4],
    "38242": [4],
    # AFP Lab test — NCD path (index 5 = NCD-190.25)
    "82105": [5],
    "82106": [5],
    # Demo: explicit covered NCD (index 2 = N111)
    "11111": [2],
    # Demo: explicit excluded NCD (index 3 = N222)
    "22222": [3],
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

    def is_state_in_jurisdiction(self, state: str, policy: PolicyMatch) -> bool:
        """Check if a state falls within the policy's jurisdiction.

        NCDs are national (no jurisdiction_id) — they always match any state.
        """
        if policy.policy_type.upper() == "NCD" and not policy.jurisdiction_id:
            return True  # NCDs are national — no geographic restriction
        if not policy.jurisdiction_id:
            return False
        states = _JURISDICTION_STATES.get(policy.jurisdiction_id, [])
        return state.upper() in states

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

    def upsert_policy(self, policy: PolicyMatch, source: str = "CMS_MCD") -> None:
        """Upsert a normalized policy match into the mock repository."""
        # Find if it exists
        for i, existing in enumerate(_POLICIES):
            if existing.policy_id == policy.policy_id and existing.policy_type == policy.policy_type:
                _POLICIES[i] = policy
                return
        # If not found, append
        _POLICIES.append(policy)
