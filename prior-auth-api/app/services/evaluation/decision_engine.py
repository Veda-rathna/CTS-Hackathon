"""Decision Engine.

Determines the final TriageDecision based on NCD, LCD, and Article results.
Enforces explicit precedence rules (e.g. any explicit exclusion → DENY).
"""
from __future__ import annotations

import logging
from typing import Any

from app.schemas.evaluation import CriterionEvaluation, PolicyEvaluationResult
from app.schemas.triage import (
    DiagnosisEvaluation,
    Evidence,
    MatchedCodes,
    MatchedPolicy,
    TriageDecision,
    TriageResponse,
)

logger = logging.getLogger(__name__)


class DecisionEngine:
    """Deterministic final decision engine."""

    def decide(
        self,
        ncd_result: PolicyEvaluationResult | None,
        lcd_result: PolicyEvaluationResult | None,
        article_result: PolicyEvaluationResult | None,
        policy_path: list[PolicyEvaluationResult],
        evidence: list[Evidence],
        warnings: list[str],
        procedure: str,
    ) -> TriageResponse:
        """Make a final triage decision."""
        
        # 1. Explicit deterministic exclusion at any level -> DENY
        for result in [ncd_result, lcd_result]:
            if result and result.overall_status == "EXCLUDED":
                return self._deny(result, policy_path, evidence, warnings, procedure)

        # Collect all criteria
        all_criteria: list[CriterionEvaluation] = []
        if ncd_result: all_criteria.extend(ncd_result.criteria)
        if lcd_result: all_criteria.extend(lcd_result.criteria)
        if article_result: all_criteria.extend(article_result.criteria)

        # 2. Mandatory criterion NOT_SATISFIED -> DENY
        mandatory_failed = [c for c in all_criteria if c.mandatory and c.status == "NOT_SATISFIED"]
        if mandatory_failed:
            return self._deny_criteria(mandatory_failed, policy_path, evidence, warnings, procedure)

        # 3. Mandatory criterion UNKNOWN -> PEND
        mandatory_unknown = [c for c in all_criteria if c.mandatory and c.status == "UNKNOWN"]
        if mandatory_unknown:
            return self._pend(mandatory_unknown, policy_path, evidence, warnings, procedure)

        # 4. Article issues -> PEND or REVIEW
        if article_result:
            if article_result.has_missing_documentation:
                return self._pend_documentation(article_result, policy_path, evidence, warnings, procedure)
            if article_result.has_coding_conflict:
                return self._nurse_review(article_result, policy_path, evidence, warnings, procedure)
                
        # 5. All clear -> APPROVE
        return self._approve(policy_path, evidence, warnings, procedure)

    def _deny(self, result, policy_path, evidence, warnings, procedure) -> TriageResponse:
        return self._build_response(
            TriageDecision.LIKELY_NOT_COVERED,
            f"{result.policy_type} {result.policy_id} explicitly excludes coverage.",
            ["POLICY_EXCLUSION"],
            policy_path, evidence, warnings, procedure
        )

    def _deny_criteria(self, failed_criteria, policy_path, evidence, warnings, procedure) -> TriageResponse:
        reasons = [c.criterion for c in failed_criteria]
        return self._build_response(
            TriageDecision.LIKELY_NOT_COVERED,
            "One or more mandatory criteria were not satisfied.",
            ["CRITERIA_NOT_SATISFIED"],
            policy_path, evidence, warnings, procedure
        )

    def _pend(self, unknown_criteria, policy_path, evidence, warnings, procedure) -> TriageResponse:
        return self._build_response(
            TriageDecision.MORE_INFORMATION_REQUIRED,
            "Insufficient evidence to determine coverage. More information required.",
            ["CRITERIA_UNKNOWN"],
            policy_path, evidence, warnings, procedure
        )

    def _pend_documentation(self, article_result, policy_path, evidence, warnings, procedure) -> TriageResponse:
        return self._build_response(
            TriageDecision.MORE_INFORMATION_REQUIRED,
            "Coverage established, but required documentation is missing.",
            ["MISSING_DOCUMENTATION"],
            policy_path, evidence, warnings, procedure
        )

    def _nurse_review(self, article_result, policy_path, evidence, warnings, procedure) -> TriageResponse:
        return self._build_response(
            TriageDecision.NURSE_REVIEW,
            "Coverage established, but an article coding conflict requires manual review.",
            ["CODING_CONFLICT"],
            policy_path, evidence, warnings, procedure
        )

    def _approve(self, policy_path, evidence, warnings, procedure) -> TriageResponse:
        return self._build_response(
            TriageDecision.LIKELY_COVERED,
            "All mandatory criteria satisfied. Procedure is covered.",
            ["ALL_CRITERIA_SATISFIED"],
            policy_path, evidence, warnings, procedure
        )

    def _build_response(
        self, decision, reason, reason_codes, policy_path, evidence, warnings, procedure
    ) -> TriageResponse:
        matched_policies = [
            MatchedPolicy(policy_type=p.policy_type, policy_id=p.policy_id)
            for p in policy_path
        ]
        
        # Convert Pydantic objects to dicts for TriageResponse criteria_evaluation
        # Ensure we can serialize it correctly
        ce_dicts = []
        for p in policy_path:
            for c in p.criteria:
                ce_dicts.append(c.model_dump())
                
        pp_dicts = [p.model_dump() for p in policy_path]
        
        return TriageResponse(
            decision=decision,
            evidence_score=1.0, # Dummy for now
            requires_prior_authorization=None,
            reason=reason,
            reason_codes=reason_codes,
            policies=matched_policies,
            matched_codes=MatchedCodes(procedure=procedure, diagnosis=[]),
            evidence=evidence,
            warnings=warnings,
            criteria_evaluation=ce_dicts,
            policy_path=pp_dicts,
        )
