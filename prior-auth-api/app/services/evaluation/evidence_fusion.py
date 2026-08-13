"""Evidence Fusion.

Applies criterion-type authority precedence to fuse results from multiple evaluators.
Determines the overall policy status (COVERED, EXCLUDED, UNKNOWN, NOT_ADDRESSED).
"""
from __future__ import annotations

import logging
from typing import Literal

from app.schemas.evaluation import CriterionEvaluation, EvidenceMatrix, PolicyEvaluationResult

logger = logging.getLogger(__name__)


class EvidenceFusion:
    """Enforces authority precedence for evidence fusion."""

    def _apply_precedence(self, criteria: list[CriterionEvaluation]) -> list[CriterionEvaluation]:
        """Apply criterion-type authority precedence.
        
        If an LLM attempts to evaluate a structured criterion and disagrees
        with the SQL evaluator, the SQL evaluator is authoritative.
        """
        # Group by criterion_id
        grouped: dict[str, list[CriterionEvaluation]] = {}
        for c in criteria:
            grouped.setdefault(c.criterion_id, []).append(c)
            
        fused_criteria: list[CriterionEvaluation] = []
        
        for c_id, evals in grouped.items():
            if len(evals) == 1:
                fused_criteria.append(evals[0])
                continue
                
            # Multiple evaluators for the same criterion.
            # Enforce precedence based on criterion type.
            c_type = evals[0].criterion_type
            
            if c_type == "STRUCTURED":
                # Deterministic (SQL) wins over Semantic (LLM)
                sql_eval = next((e for e in evals if e.evaluator == "SQL"), None)
                if sql_eval:
                    for e in evals:
                        if e.evaluator == "LLM":
                            e.status = sql_eval.status
                            e.authoritative = False
                            e.overridden_by = "SQL"
                            e.explanation += f" [Overridden by SQL deterministic rule]"
                    fused_criteria.append(sql_eval)
                else:
                    # Just take the first if no SQL
                    fused_criteria.append(evals[0])
                    
            elif c_type == "RULE_BASED":
                # Rule Engine wins
                rule_eval = next((e for e in evals if e.evaluator == "RULE_ENGINE"), None)
                if rule_eval:
                    fused_criteria.append(rule_eval)
                else:
                    fused_criteria.append(evals[0])
                    
            else:
                # For SEMANTIC or DOCUMENT, assume LLM or Document Rule is authoritative
                # Just take the first available
                fused_criteria.append(evals[0])
                
        return fused_criteria

    def determine_ncd_status(
        self, 
        matrix: EvidenceMatrix, 
        ncd_hint: str | None = None
    ) -> PolicyEvaluationResult:
        """Determine NCD overall status based on fused evidence."""
        matrix.criteria = self._apply_precedence(matrix.criteria)
        
        if matrix.has_exclusion:
            status = "EXCLUDED"
            explanation = "One or more mandatory NCD criteria explicitly excluded coverage."
        elif matrix.all_satisfied:
            status = "COVERED"
            explanation = "All mandatory NCD criteria were satisfied."
        elif matrix.has_unknown:
            # Check hint if criteria are unknown
            if ncd_hint and "NOT_ADDRESSED" in ncd_hint.upper():
                status = "NOT_ADDRESSED"
                explanation = "NCD does not address this procedure nationally."
            else:
                # If we don't have enough info, but the hint says covered, 
                # we still can't guarantee coverage without the facts.
                # However, for NCDs if there are no explicit exclusions and we just don't have facts,
                # it's usually NOT_ADDRESSED so it falls to LCD.
                # Let's say if we have unknown criteria, we can't definitively cover.
                status = "NOT_ADDRESSED" 
                explanation = "Insufficient evidence to determine NCD coverage; deferring to LCD."
        else:
            status = "NOT_ADDRESSED"
            explanation = "NCD does not address this procedure nationally."
            
        return PolicyEvaluationResult(
            policy_id="", # Filled by caller
            policy_type="NCD",
            criteria=matrix.criteria,
            evidence_matrix=matrix,
            overall_status=status,
            explanation=explanation
        )

    def determine_lcd_status(
        self, 
        matrix: EvidenceMatrix,
    ) -> PolicyEvaluationResult:
        """Determine LCD overall status based on fused evidence."""
        matrix.criteria = self._apply_precedence(matrix.criteria)
        
        if matrix.has_exclusion:
            status = "EXCLUDED"
            explanation = "One or more mandatory LCD criteria explicitly excluded coverage."
        elif matrix.all_satisfied:
            status = "COVERED"
            explanation = "All mandatory LCD criteria were satisfied."
        elif matrix.has_unknown:
            status = "UNKNOWN"
            explanation = "Insufficient evidence to determine LCD coverage (more information required)."
        else:
            status = "UNKNOWN"
            explanation = "Insufficient evidence to determine LCD coverage."
            
        return PolicyEvaluationResult(
            policy_id="", # Filled by caller
            policy_type="LCD",
            criteria=matrix.criteria,
            evidence_matrix=matrix,
            overall_status=status,
            explanation=explanation
        )
