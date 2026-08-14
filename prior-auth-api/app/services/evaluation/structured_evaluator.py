"""Structured Evaluator."""
from __future__ import annotations

import re
from typing import List

from app.schemas.evaluation import EvaluatedCriterion, EvaluationStatus, EvaluatorType, PolicyCriterion
from app.schemas.triage import TriageRequest
from app.repositories.interfaces.article_repository import ArticleRepository
from app.repositories.interfaces.lcd_repository import LCDRepository
from app.repositories.interfaces.ncd_repository import NCDRepository

class StructuredEvaluator:
    """Evaluates STRUCTURED criteria using deterministic logic (SQL equivalent)."""

    def __init__(
        self,
        article_repository: ArticleRepository,
        lcd_repository: LCDRepository,
        ncd_repository: NCDRepository,
    ):
        self._article_repo = article_repository
        self._lcd_repo = lcd_repository
        self._ncd_repo = ncd_repository
    
    def evaluate(self, criterion: PolicyCriterion, request: TriageRequest) -> EvaluatedCriterion:
        """
        Evaluate structured criteria (e.g., HCPCS, ICD-10) using actual repositories.
        """
        status = EvaluationStatus.UNKNOWN
        patient_evidence = []
        policy_evidence = [criterion.criterion]
        
        text = criterion.criterion.lower()
        
        # Determine which repository to use based on policy type
        ptype = criterion.policy_type.upper()
        pid = criterion.policy_id
        
        covered_hcpcs = []
        covered_icd10 = []
        noncovered_icd10 = []
        
        if ptype == "ARTICLE":
            covered_hcpcs = [c.code for c in self._article_repo.get_hcpcs(pid)]
            covered_icd10 = [c.code for c in self._article_repo.get_icd10_covered(pid)]
            noncovered_icd10 = [c.code for c in self._article_repo.get_icd10_noncovered(pid)]
        elif ptype == "LCD":
            covered_hcpcs = [c.code for c in self._lcd_repo.get_hcpcs(pid)]
            covered_icd10 = [c.code for c in self._lcd_repo.get_icd10_covered(pid)]
            noncovered_icd10 = [c.code for c in self._lcd_repo.get_icd10_noncovered(pid)]
        elif ptype == "NCD":
            covered_hcpcs = [c.code for c in self._ncd_repo.get_hcpcs(pid)]
            # NCD usually doesn't have standard ICD-10 tables in this schema but we can add safely
            
        # 1. HCPCS Evaluation
        if re.search(r'\b(hcpcs|cpt|procedure)\b', text):
            if request.procedure_code in covered_hcpcs:
                status = EvaluationStatus.SATISFIED
                patient_evidence.append(f"Procedure code {request.procedure_code} is explicitly covered in {ptype} {pid}.")
            elif covered_hcpcs:
                status = EvaluationStatus.NOT_SATISFIED
                patient_evidence.append(f"Procedure code {request.procedure_code} is not in the covered list for {ptype} {pid}.")
            else:
                # No specific HCPCS list found, fall back to text matching
                if request.procedure_code.lower() in text:
                    status = EvaluationStatus.SATISFIED
                    patient_evidence.append(f"Procedure code {request.procedure_code} found in text.")
                else:
                    status = EvaluationStatus.NOT_SATISFIED
                    patient_evidence.append(f"Procedure code {request.procedure_code} not found in text.")

        # 2. ICD-10 Evaluation
        elif re.search(r'\b(icd-?10|diagnosis|dx)\b', text):
            matched_any = False
            for dx in request.diagnosis_codes:
                if dx in covered_icd10:
                    status = EvaluationStatus.SATISFIED
                    patient_evidence.append(f"Diagnosis code {dx} is explicitly covered in {ptype} {pid}.")
                    matched_any = True
                elif dx in noncovered_icd10:
                    status = EvaluationStatus.NOT_SATISFIED
                    patient_evidence.append(f"Diagnosis code {dx} is explicitly non-covered in {ptype} {pid}.")
                    matched_any = True
            
            if not matched_any:
                # Text fallback
                for dx in request.diagnosis_codes:
                    if dx.lower() in text:
                        status = EvaluationStatus.SATISFIED
                        patient_evidence.append(f"Diagnosis code {dx} found in text.")
                        matched_any = True
                        break
                        
                if not matched_any:
                    status = EvaluationStatus.NOT_SATISFIED
                    patient_evidence.append("Requested diagnosis codes not found in structured requirements.")

        if status == EvaluationStatus.UNKNOWN:
            status = EvaluationStatus.NOT_SATISFIED
            patient_evidence.append("Could not match any requested codes to this structured requirement.")

        return EvaluatedCriterion(
            criterion_id=criterion.criterion_id,
            policy_type=criterion.policy_type,
            policy_id=criterion.policy_id,
            criterion=criterion.criterion,
            criterion_type=criterion.type,
            evaluator=EvaluatorType.SQL,
            status=status,
            patient_evidence=patient_evidence,
            policy_evidence=policy_evidence,
            authoritative=True,
            mandatory=True
        )
