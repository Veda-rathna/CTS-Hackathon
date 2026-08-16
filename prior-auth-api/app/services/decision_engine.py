"""Centralized mapping of internal evaluation states to the public Final Decision.

Priority ladder (highest authority first):
  1. Explicit policy exclusion (NCD / LCD / Article EXCLUDED) → PEND
  2. Ambiguous/unknown evidence                               → PEND
  3. Missing required information                             → REQUEST_MORE_INFORMATION
  4. No applicable policy found                               → PEND
  5. Confirmed coverage (COVERED at any level)                → APPROVE
  6. Fallback                                                 → PEND
"""
from typing import List, Tuple
from app.schemas.triage import TriageDecision


class DecisionEngine:
    @staticmethod
    def map_to_final(
        ncd_result: str,
        lcd_result: str,
        article_result: str,
        missing: List[str],
    ) -> Tuple[TriageDecision, List[str], List[str]]:
        """Map internal policy evaluation results to one of three final decisions:
        APPROVE, PEND, or REQUEST_MORE_INFORMATION.

        Args:
            ncd_result:     "COVERED", "EXCLUDED", or "NOT_ADDRESSED"
            lcd_result:     "COVERED", "EXCLUDED", "UNKNOWN", or "NOT_ADDRESSED"
            article_result: "COVERED", "EXCLUDED", "UNKNOWN", or "NOT_ADDRESSED"
            missing:        List of missing-information reasons.

        Returns:
            Tuple of (Final TriageDecision, List[reason codes], List[warnings])

        Authority ladder (deterministic evidence always wins):
          Explicit exclusion > ambiguous unknown > missing information > no policy > covered
        """
        reasons: List[str] = []
        warnings: List[str] = []

        # ── 1. Explicit policy exclusions always win ─────────────────────────
        # A deterministic exclusion (SQL / authoritative) can never be overridden
        # by missing documentation — the request must be pended for review.
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

        # ── 2. Missing required information ─────────────────────────────────
        # When clinical information or covered diagnosis codes are missing,
        # prompt the provider for additional information.
        if missing:
            reasons.append("MISSING_REQUIRED_INFORMATION")
            return TriageDecision.REQUEST_MORE_INFORMATION, reasons, warnings

        # ── 3. Ambiguous / unknown evidence ─────────────────────────────────
        # Article is the most specific layer — if it returned COVERED, LCD/NCD
        # UNKNOWN results are superseded and must not block an APPROVE.
        # Similarly, if LCD returned COVERED, NCD UNKNOWN is superseded.
        effective_unknown = False
        if article_result == "UNKNOWN":
            effective_unknown = True
        elif article_result not in ("COVERED", "EXCLUDED"):
            # Article did not resolve — check LCD
            if lcd_result == "UNKNOWN":
                effective_unknown = True
            elif lcd_result not in ("COVERED", "EXCLUDED"):
                # LCD did not resolve — check NCD
                if ncd_result == "UNKNOWN":
                    effective_unknown = True

        if effective_unknown:
            reasons.append("AMBIGUOUS_EVIDENCE_REQUIRES_REVIEW")
            warnings.append("Ambiguous evidence. Manual review required.")
            return TriageDecision.PEND, reasons, warnings

        # ── 4. No applicable policy found ───────────────────────────────────
        if (
            ncd_result == "NOT_ADDRESSED"
            and lcd_result == "NOT_ADDRESSED"
            and article_result == "NOT_ADDRESSED"
        ):
            reasons.append("NO_APPLICABLE_POLICY_FOUND")
            warnings.append("No policy found for procedure. Manual review required.")
            return TriageDecision.PEND, reasons, warnings

        # ── 5. Confirmed coverage ────────────────────────────────────────────
        # Most specific policy wins: Article > LCD > NCD.
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
        reasons.append("FALLBACK_PEND")
        warnings.append("Unable to determine safe coverage. Pended for review.")
        return TriageDecision.PEND, reasons, warnings
