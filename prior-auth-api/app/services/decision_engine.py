"""Centralized mapping of internal evaluation states to the public Final Decision."""
from typing import List, Dict, Any, Tuple, Optional
from app.schemas.triage import TriageDecision
from app.schemas.evaluation import EvaluatedCriterion, EvaluationStatus


class DecisionEngine:
    @staticmethod
    def map_to_final(
        ncd_result: str,
        lcd_result: str,
        article_result: str,
        missing: List[str],
        criteria: Optional[List[EvaluatedCriterion]] = None,
    ) -> Tuple[TriageDecision, List[str], List[str]]:
        """
        Maps internal policy evaluation results to one of three final decisions:
        APPROVE, DENY, or NEED_MORE_INFORMATION.

        Decision Rules:
        - Mandatory NOT_SATISFIED or explicit policy exclusion -> DENY
        - Mandatory UNKNOWN or missing clinical documentation -> NEED_MORE_INFORMATION
        - All mandatory requirements SATISFIED -> APPROVE

        Returns:
            Tuple of (Final TriageDecision, List of Reason Codes, List of Warnings)
        """
        reasons = []
        warnings = []

        # 1. Check criterion-level evaluations if provided
        if criteria:
            mandatory_failed = [c for c in criteria if c.status == EvaluationStatus.NOT_SATISFIED and c.mandatory]
            mandatory_unknown = [c for c in criteria if c.status == EvaluationStatus.UNKNOWN and c.mandatory]

            if mandatory_failed:
                reasons.append("MANDATORY_CRITERIA_NOT_SATISFIED")
                for mf in mandatory_failed:
                    warnings.append(f"Failed Requirement: {mf.criterion}")
                return TriageDecision.DENY, reasons, warnings

            if mandatory_unknown or missing:
                if missing:
                    reasons.append("MISSING_REQUIRED_INFORMATION")
                else:
                    reasons.append("AMBIGUOUS_EVIDENCE_REQUIRES_DOCUMENTATION")
                for mu in mandatory_unknown:
                    warnings.append(f"Documentation Required: {mu.criterion}")
                return TriageDecision.NEED_MORE_INFORMATION, reasons, warnings

        # 2. Missing information always forces NEED_MORE_INFORMATION
        if missing:
            reasons.append("MISSING_REQUIRED_INFORMATION")
            return TriageDecision.NEED_MORE_INFORMATION, reasons, warnings

        # 3. Check for explicit policy exclusions -> DENY
        if ncd_result == "EXCLUDED":
            reasons.append("NCD_EXCLUDES_PROCEDURE")
            warnings.append("The requested procedure is explicitly excluded by the applicable National Coverage Determination.")
            return TriageDecision.DENY, reasons, warnings

        if lcd_result == "EXCLUDED":
            reasons.append("LCD_EXCLUDES_PROCEDURE")
            warnings.append("The requested procedure is explicitly excluded by the applicable Local Coverage Determination.")
            return TriageDecision.DENY, reasons, warnings

        if article_result == "EXCLUDED":
            reasons.append("ARTICLE_EXCLUDES_PROCEDURE")
            warnings.append("The submitted diagnosis or procedure is explicitly non-covered under the applicable Billing and Coding Article.")
            return TriageDecision.DENY, reasons, warnings

        # 4. Check for unknowns / ambiguity -> NEED_MORE_INFORMATION
        if ncd_result == "UNKNOWN" or lcd_result == "UNKNOWN" or article_result == "UNKNOWN":
            reasons.append("AMBIGUOUS_EVIDENCE_REQUIRES_DOCUMENTATION")
            warnings.append("Additional clinical documentation is required to verify ambiguous criteria.")
            return TriageDecision.NEED_MORE_INFORMATION, reasons, warnings

        # 5. Check for lack of policy addressing the procedure
        if ncd_result == "NOT_ADDRESSED" and lcd_result == "NOT_ADDRESSED" and article_result == "NOT_ADDRESSED":
            reasons.append("NO_APPLICABLE_POLICY_FOUND")
            warnings.append("No active Medicare policy references the submitted procedure code in this jurisdiction.")
            return TriageDecision.NEED_MORE_INFORMATION, reasons, warnings

        # 6. Check if we have valid coverage
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

        # 7. Fallback
        reasons.append("FALLBACK_REVIEW")
        warnings.append("Unable to determine coverage from available evidence. Additional documentation required.")
        return TriageDecision.NEED_MORE_INFORMATION, reasons, warnings

