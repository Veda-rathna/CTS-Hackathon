"""Rule Evaluator.

Evaluates RULE_BASED criteria using deterministic Python rules.
This includes calculations for age, dates, frequencies, and durations.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from app.schemas.evaluation import CriterionEvaluation
from app.schemas.triage import TriageRequest

logger = logging.getLogger(__name__)


class RuleEvaluator:
    """Evaluates RULE_BASED criteria deterministically."""

    def evaluate(
        self,
        criterion: CriterionEvaluation,
        request: TriageRequest,
    ) -> CriterionEvaluation:
        """Evaluate a single rule-based criterion."""
        if criterion.criterion_type != "RULE_BASED":
            return criterion

        c_text = criterion.criterion.lower()

        # Age Evaluation
        if "age" in c_text or "years old" in c_text:
            if request.patient_age is None:
                criterion.status = "UNKNOWN"
                criterion.explanation = "Patient age not provided in request."
                return criterion
                
            # Extract age requirement
            match = re.search(r"(>=|>|<=|<|=)?\s*(\d+)", c_text)
            if match:
                op = match.group(1) or ">="
                req_age = int(match.group(2))
                
                patient_age = request.patient_age
                satisfied = False
                
                if op == ">=": satisfied = patient_age >= req_age
                elif op == ">": satisfied = patient_age > req_age
                elif op == "<=": satisfied = patient_age <= req_age
                elif op == "<": satisfied = patient_age < req_age
                elif op == "=": satisfied = patient_age == req_age
                
                criterion.status = "SATISFIED" if satisfied else "NOT_SATISFIED"
                criterion.patient_evidence.append(f"Patient age: {patient_age}")
                criterion.explanation = f"Age {patient_age} {op} {req_age} is {satisfied}."
                return criterion

        # Duration Evaluation
        # E.g., "failed conservative treatment for 6 months"
        # If we have a duration rule, we actually need facts about the patient's duration.
        # Since TriageRequest only has clinical_notes, a pure rule engine can't easily parse
        # unstructured clinical notes to get the exact duration. 
        # So we either rely on the LLM to extract the duration as a fact, or if the LLM
        # is enabled, we pass it to the Semantic Evaluator instead.
        # For now, if we don't have explicit structured duration facts in the request,
        # it evaluates to UNKNOWN, and Evidence Fusion might let LLM override if needed.
        if "month" in c_text or "week" in c_text or "day" in c_text:
            # We don't have structured clinical facts for duration in TriageRequest.
            criterion.status = "UNKNOWN"
            criterion.explanation = "Structured clinical duration facts not available. Requires semantic evaluation."
            return criterion

        criterion.status = "UNKNOWN"
        return criterion
