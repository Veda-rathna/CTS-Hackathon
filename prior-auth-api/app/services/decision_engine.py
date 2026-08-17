"""Centralized mapping of internal evaluation states to the public Final Decision.

Priority ladder (highest authority first):
  1. Explicit policy exclusion or mandatory criterion NOT_SATISFIED → DENY
  2. Missing required information or mandatory criterion UNKNOWN    → NEED_MORE_INFORMATION
  3. No applicable policy found / Ambiguous evidence                → NEED_MORE_INFORMATION
  4. Confirmed coverage (all mandatory criteria SATISFIED)           → APPROVE
  5. Fallback                                                       → NEED_MORE_INFORMATION
"""
from typing import List, Tuple
from app.schemas.triage import TriageDecision
from app.schemas.evaluation import EvaluatedCriterion, EvaluationStatus



class DecisionEngine:
    @staticmethod
    def map_to_final(
        ncd_result: str,
        lcd_result: str,
        article_result: str,
        missing: List[str],
        criteria: List[EvaluatedCriterion] | None = None,
    ) -> Tuple[TriageDecision, List[str], List[str]]:
        """Map internal policy evaluation results to one of three final decisions:
        APPROVE, DENY, or NEED_MORE_INFORMATION.

        Args:
            ncd_result:     "COVERED", "EXCLUDED", "UNKNOWN", or "NOT_ADDRESSED"
            lcd_result:     "COVERED", "EXCLUDED", "UNKNOWN", or "NOT_ADDRESSED"
            article_result: "COVERED", "EXCLUDED", "UNKNOWN", or "NOT_ADDRESSED"
            missing:        List of missing-information reasons.
            criteria:       Optional list of evaluated criteria.

        Returns:
            Tuple of (Final TriageDecision, List[reason codes], List[warnings])

        Authority ladder (deterministic evidence always wins):
          Explicit exclusion / NOT_SATISFIED > Missing info / UNKNOWN > Covered
        """
        reasons: List[str] = []
        warnings: List[str] = []
        criteria = criteria or []

        # ── 1. Explicit policy exclusions always win ─────────────────────────
        # A deterministic exclusion (SQL / authoritative) or an explicitly failed
        # mandatory requirement always maps to DENY.
        if ncd_result == "EXCLUDED":
            reasons.append("NCD_EXCLUDES_PROCEDURE")
            warnings.append("Explicit NCD exclusion resulted in denial.")
            return TriageDecision.DENY, reasons, warnings

        if lcd_result == "EXCLUDED":
            reasons.append("LCD_EXCLUDES_PROCEDURE")
            warnings.append("Explicit LCD exclusion resulted in denial.")
            return TriageDecision.DENY, reasons, warnings

        if article_result == "EXCLUDED":
            reasons.append("ARTICLE_EXCLUDES_PROCEDURE")
            warnings.append("Explicit Article exclusion resulted in denial.")
            return TriageDecision.DENY, reasons, warnings

        # Check if any mandatory criterion is NOT_SATISFIED
        for c in criteria:
            if c.mandatory and c.status == EvaluationStatus.NOT_SATISFIED:
                reasons.append("MANDATORY_CRITERIA_NOT_SATISFIED")
                warnings.append(f"Mandatory requirement '{c.criterion}' was not satisfied.")
                return TriageDecision.DENY, reasons, warnings

        # ── 2. Missing required information or mandatory UNKNOWN criteria ─────
        # When clinical information is missing or any mandatory criterion is UNKNOWN,
        # prompt the provider for additional information.
        if missing:
            reasons.append("MISSING_REQUIRED_INFORMATION")
            return TriageDecision.NEED_MORE_INFORMATION, reasons, warnings

        for c in criteria:
            if c.mandatory and c.status == EvaluationStatus.UNKNOWN:
                reasons.append("AMBIGUOUS_EVIDENCE_REQUIRES_DOCUMENTATION")
                warnings.append(f"Mandatory requirement '{c.criterion}' requires additional clinical documentation.")
                return TriageDecision.NEED_MORE_INFORMATION, reasons, warnings

        # ── 3. Ambiguous / unknown policy evidence ───────────────────────────
        effective_unknown = False
        if article_result == "UNKNOWN":
            effective_unknown = True
        elif article_result not in ("COVERED", "EXCLUDED"):
            if lcd_result == "UNKNOWN":
                effective_unknown = True
            elif lcd_result not in ("COVERED", "EXCLUDED"):
                if ncd_result == "UNKNOWN":
                    effective_unknown = True

        if effective_unknown:
            reasons.append("AMBIGUOUS_EVIDENCE_REQUIRES_DOCUMENTATION")
            warnings.append("Ambiguous evidence or missing clinical documentation. Additional information required.")
            return TriageDecision.NEED_MORE_INFORMATION, reasons, warnings

        # ── 4. No applicable policy found ───────────────────────────────────
        if (
            ncd_result == "NOT_ADDRESSED"
            and lcd_result == "NOT_ADDRESSED"
            and article_result == "NOT_ADDRESSED"
        ):
            reasons.append("POLICY_NOT_FOUND")
            warnings.append("No active policy found for procedure in this jurisdiction.")
            return TriageDecision.NEED_MORE_INFORMATION, reasons, warnings

        # ── 5. Confirmed coverage (All mandatory criteria SATISFIED) ─────────
        is_covered = False
        if article_result == "COVERED":
            is_covered = True
            reasons.append("ARTICLE_CRITERIA_SATISFIED")
        elif lcd_result == "COVERED" and article_result != "EXCLUDED":
            is_covered = True
            reasons.append("LCD_CRITERIA_SATISFIED")
        elif ncd_result == "COVERED" and lcd_result != "EXCLUDED" and article_result != "EXCLUDED":
            is_covered = True
            reasons.append("NCD_CRITERIA_SATISFIED")

        if is_covered:
            return TriageDecision.APPROVE, reasons, warnings

        # ── 6. Fallback ──────────────────────────────────────────────────────
        reasons.append("FALLBACK_NEED_MORE_INFO")
        warnings.append("Unable to determine safe coverage with available evidence.")
        return TriageDecision.NEED_MORE_INFORMATION, reasons, warnings
