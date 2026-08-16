"""Classifier for evaluation criteria."""
from __future__ import annotations

import re
from app.schemas.evaluation import CriterionType, PolicyCriterion


class CriterionClassifier:
    """Classifies criteria into STRUCTURED, RULE_BASED, or SEMANTIC."""

    @staticmethod
    def classify(criterion_dict: dict) -> PolicyCriterion:
        """Classify a raw criterion dictionary."""
        text = criterion_dict["criterion"].lower()
        
        # 1. Check for Structured deterministic signals (Codes)
        if re.search(r'\b(hcpcs|cpt|icd-?10|code)\b', text):
            c_type = CriterionType.STRUCTURED
            
        # 2. Check for Rule-Based signals (Age, Dates, Numeric Thresholds)
        elif re.search(r'\b(age|years old|\>|\<|>=|<=|greater than|less than|date|days)\b', text):
            c_type = CriterionType.RULE_BASED
            
        # 3. Default to Semantic LLM Evaluation
        else:
            c_type = CriterionType.SEMANTIC
            
        return PolicyCriterion(
            criterion_id=criterion_dict["criterion_id"],
            criterion=criterion_dict["criterion"],
            type=c_type,
            policy_type=criterion_dict["policy_type"],
            policy_id=criterion_dict["policy_id"],
            mandatory=criterion_dict.get("mandatory", True),
        )
