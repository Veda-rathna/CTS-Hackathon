"""Criterion Classifier.

Determines the type of a criterion (STRUCTURED, RULE_BASED, SEMANTIC, DOCUMENT)
based on its metadata, source, and text content.
"""
from __future__ import annotations

import re

from app.schemas.evaluation import CriterionSource


class CriterionClassifier:
    """Classifies criteria to determine which evaluator should process them."""

    def classify(self, criterion: str, source: CriterionSource) -> str:
        """Classify a criterion into its corresponding type.

        Priority:
        1. Explicit structured metadata (e.g., from DB schema)
        2. Known deterministic patterns (duration, age)
        3. Document checks (if explicitly tagged)
        4. Semantic (fallback for unstructured text)

        Returns:
            "STRUCTURED", "RULE_BASED", "SEMANTIC", or "DOCUMENT"
        """
        # 1. Structured metadata / Database source
        if source.extraction_method in ("STRUCTURED_FIELD", "CODE_RELATIONSHIP"):
            if "doc_reqs" in source.section.lower() or "documentation" in source.section.lower():
                return "DOCUMENT"
            return "STRUCTURED"
            
        if "decision" in source.section.lower() and source.extraction_method == "STRUCTURED_FIELD":
            return "STRUCTURED"

        # 2. Known deterministic patterns (Regex)
        criterion_lower = criterion.lower()
        
        # Age
        if re.search(r"\b(age|years? old|>=|>|<=|<|=)\s*\d+\b", criterion_lower):
            # Might be rule-based if simple age
            if "age" in criterion_lower or "years old" in criterion_lower:
                return "RULE_BASED"
                
        # Duration / Timeframes
        if re.search(r"\b\d+\s+(weeks?|months?|days?|years?)\b", criterion_lower):
            # Check if it's about duration of treatment etc.
            if any(w in criterion_lower for w in ["conservative", "failed", "tried", "trial", "duration"]):
                return "RULE_BASED"
                
        # Frequency
        if re.search(r"\b(per year|per month|annually|lifetime)\b", criterion_lower):
            return "RULE_BASED"
            
        # 3. Document checks (if from text but clearly about documentation)
        if any(w in criterion_lower for w in ["documentation must", "must be documented", "medical record must", "notes must show"]):
            return "DOCUMENT"

        # 4. Semantic fallback for unstructured clinical criteria
        return "SEMANTIC"
