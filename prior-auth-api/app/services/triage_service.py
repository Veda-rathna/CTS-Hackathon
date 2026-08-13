"""Triage service — deterministic policy-matching engine.

This module implements the core triage logic.  It is completely independent
of any database technology.  All data access goes through repository
interfaces so the engine can be tested in isolation using mock data.

IMPORTANT DISCLAIMER
--------------------
The triage engine produces a **policy-matching result** only.
It does NOT constitute clinical advice, medical diagnosis, insurance
coverage confirmation, or a guarantee of prior authorization approval.

Decision Logic (in order)
--------------------------
1. Normalize inputs.
2. Search for policies by procedure code → POLICY_NOT_FOUND if none.
3. Check NCD cascade:
   - If NCD COVERED → APPROVE (LIKELY_COVERED)
   - If NCD EXCLUDED → DENY (LIKELY_NOT_COVERED)
   - If NOT ADDRESSED → Proceed to LCD
4. Check LCD & jurisdiction:
   - If OUTSIDE_JURISDICTION → Return
5. Article coding validation:
   - Evaluate each diagnosis code against Article's covered/non-covered lists.
   - If COVERED → APPROVE (LIKELY_COVERED)
   - If NOT_COVERED → DENY (LIKELY_NOT_COVERED)
   - If UNKNOWN (with clinical flags) → NURSE_REVIEW
   - If UNKNOWN (no clinical flags) → MORE_INFORMATION_REQUIRED
"""
from __future__ import annotations

import logging
from datetime import date

from app.repositories.interfaces.article_repository import ArticleRepository
from app.repositories.interfaces.ncd_repository import NCDRepository
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


def _calc_evidence_score(
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


def _filter_latest_effective_policies(
    policies: list[PolicyMatch], as_of: date | None = None
) -> list[PolicyMatch]:
    """Filter policies to keep only the most recent effective version per ID."""
    active = [p for p in policies if _is_policy_effective(p, as_of)]
    grouped = {}
    for p in active:
        if p.policy_id not in grouped:
            grouped[p.policy_id] = p
        else:
            existing = grouped[p.policy_id]
            if p.effective_date and existing.effective_date:
                if p.effective_date > existing.effective_date:
                    grouped[p.policy_id] = p
            elif p.effective_date:
                grouped[p.policy_id] = p
    return list(grouped.values())


class TriageService:
    """Deterministic triage engine that matches a clinical request to policies."""

    def __init__(
        self,
        policy_repository: PolicyRepository,
        article_repository: ArticleRepository,
        ncd_repository: NCDRepository,
    ) -> None:
        self._policy_repo = policy_repository
        self._article_repo = article_repository
        self._ncd_repo = ncd_repository

    # ── Public entry point ────────────────────────────────────────────────────

    def evaluate(self, request: TriageRequest) -> TriageResponse:
        """Run the full triage pipeline and return a structured, explained result."""
        procedure = request.procedure_code
        diagnoses = request.diagnosis_codes
        state = request.state

        logger.info(
            "Triage started | procedure=%s diagnoses=%s state=%s",
            procedure,
            ",".join(diagnoses),
            state or "N/A",
        )

        evidence: list[Evidence] = []
        warnings: list[str] = []
        missing: list[str] = []

        # ── Step 2: Find all policies ─────────────────────────────────────────
        all_policies = self._policy_repo.find_policies_for_procedure(procedure)
        if not all_policies:
            logger.info("Triage result: POLICY_NOT_FOUND | procedure=%s", procedure)
            return TriageResponse(
                decision=TriageDecision.POLICY_NOT_FOUND,
                evidence_score=0.0,
                reason=f"No policy was found for procedure code '{procedure}'.",
                reason_codes=["POLICY_NOT_FOUND"],
                missing_information=[f"No coverage policy references procedure code '{procedure}'."],
            )

        active_policies = _filter_latest_effective_policies(all_policies)
        if not active_policies:
            logger.info("Triage result: POLICY_EXPIRED | procedure=%s", procedure)
            return TriageResponse(
                decision=TriageDecision.POLICY_EXPIRED,
                evidence_score=0.0,
                reason=f"All policies referencing procedure code '{procedure}' are expired.",
                reason_codes=["POLICY_EXPIRED"],
                warnings=["All matching policies have expired."],
            )

        ncd_policies = [p for p in active_policies if p.policy_type.upper() == "NCD"]
        lcd_policies = [p for p in active_policies if p.policy_type.upper() == "LCD"]

        # ── Step 3: NCD cascade ───────────────────────────────────────────────
        if ncd_policies:
            for ncd_policy in ncd_policies:
                ncd_details = self._ncd_repo.get_by_id(ncd_policy.policy_id)
                if ncd_details and ncd_details.decision:
                    ncd_decision = ncd_details.decision.upper()
                    
                    # Log evidence of NCD evaluation
                    evidence.append(
                        Evidence(
                            type="HCPCS",
                            identifier=ncd_policy.policy_id,
                            code=procedure,
                            result="MATCHED",
                            explanation=f"Procedure {procedure} is addressed by NCD {ncd_policy.policy_id}.",
                        )
                    )
                    
                    mp = MatchedPolicy(
                        policy_type="NCD",
                        policy_id=ncd_policy.policy_id,
                        title=ncd_policy.title,
                    )
                    
                    if "COVERED" in ncd_decision:
                        logger.info("Triage result: LIKELY_COVERED (NCD) | procedure=%s", procedure)
                        return TriageResponse(
                            decision=TriageDecision.LIKELY_COVERED,
                            evidence_score=_calc_evidence_score(True, False, False, True, False),
                            reason=f"National Coverage Determination ({ncd_policy.policy_id}) explicitly covers procedure {procedure}.",
                            reason_codes=["NCD_COVERS_PROCEDURE"],
                            policies=[mp],
                            matched_codes=MatchedCodes(procedure=procedure),
                            evidence=evidence,
                        )
                    elif "EXCLUDED" in ncd_decision or "NON_COVERED" in ncd_decision:
                        logger.info("Triage result: LIKELY_NOT_COVERED (NCD) | procedure=%s", procedure)
                        return TriageResponse(
                            decision=TriageDecision.LIKELY_NOT_COVERED,
                            evidence_score=_calc_evidence_score(True, False, False, True, False),
                            reason=f"National Coverage Determination ({ncd_policy.policy_id}) explicitly excludes procedure {procedure}.",
                            reason_codes=["NCD_EXCLUDES_PROCEDURE"],
                            policies=[mp],
                            matched_codes=MatchedCodes(procedure=procedure),
                            evidence=evidence,
                        )
                    # If NOT_ADDRESSED or UNKNOWN, continue to LCD

        # ── Step 4: LCD and Jurisdiction ──────────────────────────────────────
        if not lcd_policies:
            # We had NCDs but they were not addressed, and no LCDs exist
            logger.info("Triage result: POLICY_NOT_FOUND (No LCD) | procedure=%s", procedure)
            return TriageResponse(
                decision=TriageDecision.POLICY_NOT_FOUND,
                evidence_score=0.0,
                reason=f"NCDs do not address coverage and no LCDs exist for procedure '{procedure}'.",
                reason_codes=["NO_APPLICABLE_LCD"],
                missing_information=["Missing specific LCD or Article for evaluation."],
            )

        candidate_policies = lcd_policies
        if state:
            jurisdiction_matching = [
                p for p in lcd_policies if self._policy_repo.is_state_in_jurisdiction(state, p)
            ]
            if not jurisdiction_matching:
                evidence.append(
                    Evidence(
                        type="JURISDICTION",
                        identifier="",
                        state=state,
                        result="NOT_MATCHED",
                        explanation=f"State '{state}' is outside the jurisdiction(s) of the matching LCDs.",
                    )
                )
                logger.info("Triage result: OUTSIDE_JURISDICTION | state=%s procedure=%s", state, procedure)
                return TriageResponse(
                    decision=TriageDecision.OUTSIDE_JURISDICTION,
                    evidence_score=_calc_evidence_score(True, False, False, True, False),
                    reason=f"State '{state}' is not covered by the jurisdiction of the matching LCD. Contact your MAC.",
                    reason_codes=["OUTSIDE_JURISDICTION"],
                    policies=[MatchedPolicy(policy_type=p.policy_type, policy_id=p.policy_id, title=p.title, article_id=p.article_id) for p in lcd_policies],
                    evidence=evidence,
                    warnings=[f"State '{state}' is outside policy jurisdiction."],
                )

            candidate_policies = jurisdiction_matching
            evidence.append(
                Evidence(
                    type="JURISDICTION",
                    identifier=candidate_policies[0].jurisdiction_id or candidate_policies[0].policy_id,
                    state=state,
                    result="MATCHED",
                    explanation=f"State '{state}' falls within the jurisdiction of LCD {candidate_policies[0].policy_id}.",
                )
            )
        else:
            missing.append("State not provided — jurisdiction could not be verified.")

        # ── Step 5: Article validation (HCPCS & ICD-10) ───────────────────────
        best_policy = candidate_policies[0]
        article_id = best_policy.article_id

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
                    explanation=f"Procedure code '{procedure}' {'is' if procedure_matched else 'was not'} listed in article {article_id}.",
                )
            )
        else:
            missing.append("No associated article found for detailed code validation.")

        covered_set: set[str] = set()
        noncovered_set: set[str] = set()
        if article_id:
            covered_set = {c.code for c in self._article_repo.get_icd10_covered(article_id)}
            noncovered_set = {c.code for c in self._article_repo.get_icd10_noncovered(article_id)}

        diagnosis_evals: list[DiagnosisEvaluation] = []
        covered_matches: list[str] = []
        noncovered_matches: list[str] = []
        unknown_matches: list[str] = []

        for dx in diagnoses:
            if dx in covered_set:
                status = "COVERED"
                covered_matches.append(dx)
                evidence.append(
                    Evidence(type="ICD10", identifier=article_id, code=dx, result="COVERED", explanation=f"Diagnosis '{dx}' is covered.")
                )
            elif dx in noncovered_set:
                status = "NOT_COVERED"
                noncovered_matches.append(dx)
                evidence.append(
                    Evidence(type="ICD10", identifier=article_id, code=dx, result="NOT_COVERED", explanation=f"Diagnosis '{dx}' is explicitly non-covered.")
                )
            else:
                status = "NOT_FOUND"
                unknown_matches.append(dx)
                missing.append(f"Diagnosis code '{dx}' not found in policy code lists.")
                evidence.append(
                    Evidence(type="ICD10", identifier=article_id, code=dx, result="NOT_FOUND", explanation=f"Diagnosis '{dx}' not found in article {article_id}.")
                )
            diagnosis_evals.append(DiagnosisEvaluation(code=dx, status=status))

        # ── Step 6: Final Decision Logic ──────────────────────────────────────
        has_article = article_id is not None
        jurisdiction_match = state is not None and bool(candidate_policies[0].jurisdiction_id)

        evidence_score = _calc_evidence_score(
            procedure_match=procedure_matched,
            diagnosis_match=len(covered_matches) > 0,
            jurisdiction_match=jurisdiction_match,
            policy_active=True,
            article_match=has_article,
        )

        all_explicitly_noncovered = (
            len(diagnoses) > 0
            and len(noncovered_matches) == len(diagnoses)
            and len(covered_matches) == 0
        )

        reason_codes = ["PROCEDURE_FOUND"]
        if jurisdiction_match:
            reason_codes.append("JURISDICTION_MATCH")

        if covered_matches:
            decision = TriageDecision.LIKELY_COVERED
            reason = f"Procedure '{procedure}' and diagnosis ({', '.join(covered_matches)}) match an active LCD/Article."
            reason_codes.append("DIAGNOSIS_COVERED")
        elif all_explicitly_noncovered:
            decision = TriageDecision.LIKELY_NOT_COVERED
            reason = f"All diagnosis codes ({', '.join(noncovered_matches)}) are explicitly non-covered under the applicable policy."
            reason_codes.append("DIAGNOSIS_EXPLICITLY_NON_COVERED")
        else:
            if request.patient_age is not None and unknown_matches:
                decision = TriageDecision.NURSE_REVIEW
                reason = "Diagnosis codes are not explicitly covered or non-covered, but clinical context (age) requires manual nurse review."
                reason_codes.append("CLINICAL_CONTEXT_REVIEW")
            else:
                decision = TriageDecision.MORE_INFORMATION_REQUIRED
                reason = "Diagnosis codes could not be confirmed as covered or non-covered. Additional clinical documentation may be required."
                reason_codes.append("DIAGNOSIS_NOT_EXPLICITLY_DEFINED")

        if noncovered_matches:
            warnings.append(f"Explicitly non-covered diagnosis codes: {', '.join(noncovered_matches)}")

        matched_policies = [
            MatchedPolicy(policy_type=p.policy_type, policy_id=p.policy_id, title=p.title, article_id=p.article_id)
            for p in candidate_policies
        ]

        logger.info("Triage result: %s | evidence_score=%.2f | procedure=%s", decision.value, evidence_score, procedure)

        return TriageResponse(
            decision=decision,
            evidence_score=evidence_score,
            requires_prior_authorization=None,
            reason=reason,
            reason_codes=reason_codes,
            policies=matched_policies,
            matched_codes=MatchedCodes(procedure=procedure, diagnosis=covered_matches),
            diagnosis_evaluation=diagnosis_evals,
            evidence=evidence,
            missing_information=missing,
            warnings=warnings,
        )

