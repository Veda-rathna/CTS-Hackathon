"""Classifier for evaluation criteria."""
from __future__ import annotations

import re
from app.schemas.evaluation import CriterionType, PolicyCriterion


class CriterionClassifier:
    """Classifies criteria into STRUCTURED or SEMANTIC.

    STRUCTURED: contains deterministic code references (HCPCS, CPT, ICD-10).
                Routed to StructuredEvaluator (SQL / deterministic).
    SEMANTIC:   free-text clinical requirements.
                Routed to SemanticEvaluator (4-agent Qwen pipeline).
    """

    @staticmethod
    def classify(criterion_dict: dict) -> PolicyCriterion:
        """Classify a raw criterion dictionary."""
        text = criterion_dict["criterion"].lower()
        
        # 1. Check for Structured deterministic signals (Codes)
        if re.search(r'\b(hcpcs|cpt|icd-?10|code)\b', text):
            c_type = CriterionType.STRUCTURED
        # 2. Default to Semantic LLM Evaluation
        else:
            c_type = CriterionType.SEMANTIC
            
        return PolicyCriterion(
            criterion_id=criterion_dict["criterion_id"],
            criterion=criterion_dict["criterion"],
            type=c_type,
            policy_type=criterion_dict["policy_type"],
            policy_id=criterion_dict["policy_id"],
            source_text=criterion_dict.get("source_text"),
            mandatory=criterion_dict.get("mandatory", True),
        )
