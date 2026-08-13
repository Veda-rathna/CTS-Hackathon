"""Triage service — deterministic policy-matching engine.

This module implements the core triage logic.  It is completely independent
of any database technology.  All data access goes through repository
interfaces so the engine can be tested in isolation using mock data.

IMPORTANT DISCLAIMER
--------------------
The triage engine produces a **policy-matching result** only.
It does NOT constitute clinical advice, medical diagnosis, insurance
coverage confirmation, or a guarantee of prior authorization approval.

Confidence Score
----------------
The ``confidence`` field is a deterministic evidence-completeness score
(0.0 – 1.0).  It is NOT a machine-learning probability.  It indicates
how many of the expected evidence dimensions (procedure, diagnosis,
jurisdiction, policy date, article) were successfully matched.

    Procedure match:    +0.25
    Diagnosis match:    +0.30
    Jurisdiction match: +0.20
    Active policy:      +0.15
    Article match:      +0.10
    Maximum:             1.00

Decision Logic (in order)
--------------------------
1. Normalize inputs.
2. Search for policies by procedure code → POLICY_NOT_FOUND if none.
3. Check effective dates → POLICY_EXPIRED if all are expired.
4. Check jurisdiction → OUTSIDE_JURISDICTION if state supplied but no match.
5. Check HCPCS/CPT code in article codes.
6. Evaluate each diagnosis code (COVERED / NOT_COVERED / NOT_FOUND).
7. Determine final decision:
   - LIKELY_COVERED if ≥1 diagnosis is COVERED.
   - LIKELY_NOT_COVERED if all diagnosed codes are explicitly non-covered.
   - MORE_INFORMATION_REQUIRED otherwise.
"""
from __future__ import annotations

import logging
from datetime import date

from app.repositories.interfaces.article_repository import ArticleRepository
from app.repositories.interfaces.policy_repository import PolicyRepository
from app.schemas.policy import PolicyMatch
from app.schemas.triage import (
    DiagnosisEvaluation,
    Evidence,
    MatchedCodes,
    MatchedPolicy,
    TriageDecision,
    TriageRequest,
    TriageResponse,
)

logger = logging.getLogger(__name__)

# ── Confidence weights ────────────────────────────────────────────────────────

_W_PROCEDURE = 0.25
_W_DIAGNOSIS = 0.30
_W_JURISDICTION = 0.20
_W_ACTIVE_POLICY = 0.15
_W_ARTICLE = 0.10


def _calc_confidence(
    procedure_match: bool,
    diagnosis_match: bool,
    jurisdiction_match: bool,
    policy_active: bool,
    article_match: bool,
) -> float:
    """Return a deterministic evidence-completeness score (0.0–1.0)."""
    score = 0.0
    if procedure_match:
        score += _W_PROCEDURE
    if diagnosis_match:
        score += _W_DIAGNOSIS
    if jurisdiction_match:
        score += _W_JURISDICTION
    if policy_active:
        score += _W_ACTIVE_POLICY
    if article_match:
        score += _W_ARTICLE
    return min(round(score, 2), 1.0)


def _is_policy_effective(policy: PolicyMatch, as_of: date | None = None) -> bool:
    check = as_of or date.today()
    if policy.effective_date and policy.effective_date > check:
        return False
    if policy.end_date and policy.end_date < check:
        return False
    return True


class TriageService:
    """Deterministic triage engine that matches a clinical request to policies."""

    def __init__(
        self,
        policy_repository: PolicyRepository,
        article_repository: ArticleRepository,
    ) -> None:
        self._policy_repo = policy_repository
        self._article_repo = article_repository

    # ── Public entry point ────────────────────────────────────────────────────

    def evaluate(self, request: TriageRequest) -> TriageResponse:
        """Run the full triage pipeline and return a structured, explained result.

        This method is the single integration point called by the API router.
        """
        procedure = request.procedure_code   # already normalized by Pydantic
        diagnoses = request.diagnosis_codes  # already normalized
        state = request.state               # already normalized

        logger.info(
            "Triage started | procedure=%s diagnoses=%s state=%s",
            procedure,
            ",".join(diagnoses),
            state or "N/A",
        )

        evidence: list[Evidence] = []
        warnings: list[str] = []
        missing: list[str] = []

        # ── Step 2: Find policies for procedure ───────────────────────────────
        all_policies = self._policy_repo.find_policies_for_procedure(procedure)
        if not all_policies:
            logger.info("Triage result: POLICY_NOT_FOUND | procedure=%s", procedure)
            return TriageResponse(
                decision=TriageDecision.POLICY_NOT_FOUND,
                confidence=0.0,
                requires_prior_authorization=None,
                reason=f"No policy was found for procedure code '{procedure}'.",
                policies=[],
                missing_information=[
                    f"No coverage policy references procedure code '{procedure}'."
                ],
                warnings=[],
            )

        # ── Step 3: Effective date check ──────────────────────────────────────
        active_policies = [p for p in all_policies if _is_policy_effective(p)]
        if not active_policies:
            expired = all_policies[0]
            evidence.append(
                Evidence(
                    type="POLICY_DATE",
                    identifier=expired.policy_id,
                    result="EXPIRED",
                    explanation=(
                        f"Policy {expired.policy_id} ended on {expired.end_date}. "
                        "No active policies reference this procedure code."
                    ),
                )
            )
            logger.info("Triage result: POLICY_EXPIRED | procedure=%s", procedure)
            return TriageResponse(
                decision=TriageDecision.POLICY_EXPIRED,
                confidence=0.0,
                requires_prior_authorization=None,
                reason=(
                    f"All policies referencing procedure code '{procedure}' are expired. "
                    "Verify that the procedure code is current."
                ),
                policies=[
                    MatchedPolicy(
                        policy_type=p.policy_type,
                        policy_id=p.policy_id,
                        title=p.title,
                        article_id=p.article_id,
                    )
                    for p in all_policies
                ],
                evidence=evidence,
                missing_information=[],
                warnings=["All matching policies have expired."],
            )

        evidence.append(
            Evidence(
                type="POLICY_DATE",
                identifier=active_policies[0].policy_id,
                result="ACTIVE",
                explanation=(
                    f"Policy {active_policies[0].policy_id} is currently active "
                    f"(effective {active_policies[0].effective_date})."
                ),
            )
        )

        # ── Step 4: Jurisdiction check ────────────────────────────────────────
        if state:
            jurisdiction_matching = [
                p for p in active_policies if p.jurisdiction_id and self._state_in_jurisdiction(state, p)
            ]
            if not jurisdiction_matching and active_policies:
                jurisdictions = [p.jurisdiction_id for p in active_policies if p.jurisdiction_id]
                evidence.append(
                    Evidence(
                        type="JURISDICTION",
                        identifier=", ".join(j for j in jurisdictions if j),
                        state=state,
                        result="NOT_MATCHED",
                        explanation=(
                            f"State '{state}' does not fall within the jurisdiction(s) "
                            f"({', '.join(j for j in jurisdictions if j)}) of the matching policies."
                        ),
                    )
                )
                logger.info(
                    "Triage result: OUTSIDE_JURISDICTION | state=%s procedure=%s",
                    state,
                    procedure,
                )
                return TriageResponse(
                    decision=TriageDecision.OUTSIDE_JURISDICTION,
                    confidence=_calc_confidence(True, False, False, True, False),
                    requires_prior_authorization=None,
                    reason=(
                        f"State '{state}' is not covered by the jurisdiction of the "
                        "matching policy. Contact the appropriate MAC for your region."
                    ),
                    policies=[
                        MatchedPolicy(
                            policy_type=p.policy_type,
                            policy_id=p.policy_id,
                            title=p.title,
                            article_id=p.article_id,
                        )
                        for p in active_policies
                    ],
                    evidence=evidence,
                    missing_information=[],
                    warnings=[f"The submitted state '{state}' is outside the policy jurisdiction."],
                )

            candidate_policies = jurisdiction_matching if state else active_policies
            jurisdiction_id = candidate_policies[0].jurisdiction_id if candidate_policies else None
            evidence.append(
                Evidence(
                    type="JURISDICTION",
                    identifier=jurisdiction_id,
                    state=state,
                    result="MATCHED",
                    explanation=(
                        f"State '{state}' falls within jurisdiction '{jurisdiction_id}' "
                        f"which governs the matching policy."
                    ),
                )
            )
        else:
            candidate_policies = active_policies
            missing.append("State not provided — jurisdiction could not be verified.")

        # ── Step 5 & 6: Code and diagnosis matching ───────────────────────────
        best_policy = candidate_policies[0]
        article_id = best_policy.article_id

        # Procedure match evidence
        procedure_matched = False
        if article_id:
            hcpcs_codes = {c.code for c in self._article_repo.get_hcpcs(article_id)}
            procedure_matched = procedure in hcpcs_codes
            evidence.append(
                Evidence(
                    type="HCPCS",
                    identifier=article_id,
                    code=procedure,
                    result="MATCHED" if procedure_matched else "NOT_FOUND",
                    explanation=(
                        f"Procedure code '{procedure}' {'is' if procedure_matched else 'was not'} "
                        f"listed in article {article_id}'s HCPCS/CPT code set."
                    ),
                )
            )
        else:
            missing.append("No associated article found for detailed code validation.")

        # Diagnosis matching
        covered_set: set[str] = set()
        noncovered_set: set[str] = set()
        if article_id:
            covered_set = {c.code for c in self._article_repo.get_icd10_covered(article_id)}
            noncovered_set = {c.code for c in self._article_repo.get_icd10_noncovered(article_id)}

        diagnosis_evals: list[DiagnosisEvaluation] = []
        covered_matches: list[str] = []
        noncovered_matches: list[str] = []

        for dx in diagnoses:
            if dx in covered_set:
                status = "COVERED"
                covered_matches.append(dx)
                evidence.append(
                    Evidence(
                        type="ICD10",
                        identifier=article_id,
                        code=dx,
                        result="COVERED",
                        explanation=(
                            f"Diagnosis code '{dx}' is present in article "
                            f"{article_id}'s covered ICD-10 list."
                        ),
                    )
                )
            elif dx in noncovered_set:
                status = "NOT_COVERED"
                noncovered_matches.append(dx)
                evidence.append(
                    Evidence(
                        type="ICD10",
                        identifier=article_id,
                        code=dx,
                        result="NOT_COVERED",
                        explanation=(
                            f"Diagnosis code '{dx}' is explicitly listed in article "
                            f"{article_id}'s non-covered ICD-10 list."
                        ),
                    )
                )
            else:
                status = "NOT_FOUND"
                missing.append(f"Diagnosis code '{dx}' was not found in policy code lists.")
                evidence.append(
                    Evidence(
                        type="ICD10",
                        identifier=article_id,
                        code=dx,
                        result="NOT_FOUND",
                        explanation=(
                            f"Diagnosis code '{dx}' was not found in either the covered "
                            f"or non-covered ICD-10 lists for article {article_id}."
                        ),
                    )
                )
            diagnosis_evals.append(DiagnosisEvaluation(code=dx, status=status))

        # ── Step 7: Final decision ────────────────────────────────────────────
        has_article = article_id is not None
        diagnosis_match = len(covered_matches) > 0
        jurisdiction_match = state is not None and bool(
            [p for p in candidate_policies if p.jurisdiction_id]
        )

        confidence = _calc_confidence(
            procedure_match=procedure_matched,
            diagnosis_match=diagnosis_match,
            jurisdiction_match=jurisdiction_match,
            policy_active=True,
            article_match=has_article,
        )

        all_explicitly_noncovered = (
            len(diagnoses) > 0
            and len(noncovered_matches) == len(diagnoses)
            and len(covered_matches) == 0
        )

        if covered_matches:
            decision = TriageDecision.LIKELY_COVERED
            reason = (
                f"The procedure code '{procedure}' and at least one submitted diagnosis code "
                f"({', '.join(covered_matches)}) match an active, applicable policy."
            )
        elif all_explicitly_noncovered:
            decision = TriageDecision.LIKELY_NOT_COVERED
            reason = (
                f"All submitted diagnosis codes ({', '.join(noncovered_matches)}) are "
                "explicitly listed as non-covered under the applicable policy."
            )
        else:
            decision = TriageDecision.MORE_INFORMATION_REQUIRED
            reason = (
                "A matching policy was found for the procedure code, but the submitted "
                "diagnosis codes could not be confirmed as covered or non-covered. "
                "Additional clinical documentation may be required."
            )

        if noncovered_matches:
            warnings.append(
                f"The following diagnosis codes are explicitly non-covered: "
                f"{', '.join(noncovered_matches)}."
            )

        matched_policies = [
            MatchedPolicy(
                policy_type=p.policy_type,
                policy_id=p.policy_id,
                title=p.title,
                article_id=p.article_id,
            )
            for p in candidate_policies
        ]

        logger.info(
            "Triage result: %s | confidence=%.2f | procedure=%s",
            decision.value,
            confidence,
            procedure,
        )

        return TriageResponse(
            decision=decision,
            confidence=confidence,
            requires_prior_authorization=None,
            reason=reason,
            policies=matched_policies,
            matched_codes=MatchedCodes(procedure=procedure, diagnosis=covered_matches),
            diagnosis_evaluation=diagnosis_evals,
            evidence=evidence,
            missing_information=missing,
            warnings=warnings,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _state_in_jurisdiction(self, state: str, policy: PolicyMatch) -> bool:
        """Check whether *state* is served by the policy's jurisdiction.

        The mapping lives in the policy repository (mock or PostgreSQL).
        This helper queries the mock's internal mapping via the repository.
        A PostgreSQL implementation would query the jurisdiction table.
        """
        from app.repositories.mock.policy_repository import _JURISDICTION_STATES

        if not policy.jurisdiction_id:
            return False
        states = _JURISDICTION_STATES.get(policy.jurisdiction_id, [])
        return state.upper() in states
