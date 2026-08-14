"""Centralized mapping of internal evaluation states to the public Final Decision."""
from typing import List, Dict, Any, Tuple
from app.schemas.triage import TriageDecision

class DecisionEngine:
    @staticmethod
    def map_to_final(
        ncd_result: str,
        lcd_result: str,
        article_result: str,
        missing: List[str]
    ) -> Tuple[TriageDecision, List[str], List[str]]:
        """
        Maps internal policy evaluation results to one of three final decisions:
        APPROVE, PEND, or REQUEST_MORE_INFORMATION.
        
        Args:
            ncd_result: "COVERED", "EXCLUDED", or "NOT_ADDRESSED"
            lcd_result: "COVERED", "EXCLUDED", "UNKNOWN", or "NOT_ADDRESSED"
            article_result: "COVERED", "EXCLUDED", "UNKNOWN", "NOT_ADDRESSED"
            missing: List of missing information fields.
            
        Returns:
            Tuple of (Final TriageDecision, List of Reason Codes, List of Warnings)
        """
        reasons = []
        warnings = []
        
        # 1. Missing information always forces REQUEST_MORE_INFORMATION
        if missing:
            reasons.append("MISSING_REQUIRED_INFORMATION")
            return TriageDecision.REQUEST_MORE_INFORMATION, reasons, warnings
            
        # 2. Check for explicit exclusions
        if ncd_result == "EXCLUDED":
            reasons.append("NCD_EXCLUDES_PROCEDURE")
            warnings.append("Explicit NCD exclusion mapped to PEND for review.")
            return TriageDecision.PEND, reasons, warnings
            
        if lcd_result == "EXCLUDED":
            reasons.append("LCD_EXCLUDES_PROCEDURE")
            warnings.append("Explicit LCD exclusion mapped to PEND for review.")
            return TriageDecision.PEND, reasons, warnings
            
        if article_result == "EXCLUDED":
            reasons.append("ARTICLE_EXCLUDES_PROCEDURE")
            warnings.append("Explicit Article exclusion mapped to PEND for review.")
            return TriageDecision.PEND, reasons, warnings
            
        # 3. Check for unknowns / ambiguity
        if ncd_result == "UNKNOWN" or lcd_result == "UNKNOWN" or article_result == "UNKNOWN":
            reasons.append("AMBIGUOUS_EVIDENCE_REQUIRES_REVIEW")
            warnings.append("Ambiguous evidence. Manual review required.")
            return TriageDecision.PEND, reasons, warnings
            
        # 4. Check for lack of policy addressing the procedure
        if ncd_result == "NOT_ADDRESSED" and lcd_result == "NOT_ADDRESSED" and article_result == "NOT_ADDRESSED":
            reasons.append("NO_APPLICABLE_POLICY_FOUND")
            warnings.append("No policy found for procedure. Manual review required.")
            return TriageDecision.PEND, reasons, warnings
            
        # 5. Check if we have valid coverage
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
            
        # 6. Fallback
        reasons.append("FALLBACK_PEND")
        warnings.append("Unable to determine safe coverage. Pended for review.")
        return TriageDecision.PEND, reasons, warnings
