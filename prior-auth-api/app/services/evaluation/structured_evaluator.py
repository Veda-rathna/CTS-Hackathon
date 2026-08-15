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
        explanation = ""

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
                patient_evidence.append(f"Submitted HCPCS: {request.procedure_code}")
                policy_evidence.append(f"{ptype} {pid} → HCPCS {request.procedure_code}")
                explanation = (
                    f"The submitted procedure code {request.procedure_code} is present "
                    f"in the {ptype} {pid} applicable HCPCS data. "
                    f"The procedure requirement is satisfied."
                )
            elif covered_hcpcs:
                status = EvaluationStatus.NOT_SATISFIED
                patient_evidence.append(f"Submitted HCPCS: {request.procedure_code}")
                policy_evidence.append(
                    f"{ptype} {pid} HCPCS list does not include {request.procedure_code}."
                )
                explanation = (
                    f"The submitted procedure code {request.procedure_code} is not present "
                    f"in the {ptype} {pid} applicable HCPCS data. "
                    f"The procedure requirement is not satisfied."
                )
            else:
                # No specific HCPCS list found, fall back to text matching
                if request.procedure_code.lower() in text:
                    status = EvaluationStatus.SATISFIED
                    patient_evidence.append(f"Submitted HCPCS: {request.procedure_code}")
                    explanation = (
                        f"The submitted procedure code {request.procedure_code} was found "
                        f"referenced in the policy text. The procedure requirement is satisfied."
                    )
                else:
                    status = EvaluationStatus.NOT_SATISFIED
                    patient_evidence.append(f"Submitted HCPCS: {request.procedure_code}")
                    explanation = (
                        f"The submitted procedure code {request.procedure_code} was not found "
                        f"in the policy data for {ptype} {pid}. "
                        f"The procedure requirement is not satisfied."
                    )

        # 2. ICD-10 Evaluation
        elif re.search(r'\b(icd-?10|diagnosis|dx)\b', text):
            matched_any = False
            has_covered = False
            has_noncovered = False
            covered_dxs = []
            noncovered_dxs = []
            
            for dx in request.diagnosis_codes:
                if dx in covered_icd10:
                    has_covered = True
                    covered_dxs.append(dx)
                    matched_any = True
                elif dx in noncovered_icd10:
                    has_noncovered = True
                    noncovered_dxs.append(dx)
                    matched_any = True

            if has_covered:
                status = EvaluationStatus.SATISFIED
                patient_evidence.append(f"Submitted ICD-10: {', '.join(covered_dxs)}")
                policy_evidence.append(f"{ptype} {pid} → ICD-10 covered: {', '.join(covered_dxs)}")
                explanation = (
                    f"The submitted diagnosis code(s) {', '.join(covered_dxs)} are present in the "
                    f"{ptype} {pid} covered ICD-10 data. "
                    f"The diagnosis requirement is satisfied."
                )
            elif has_noncovered:
                status = EvaluationStatus.NOT_SATISFIED
                patient_evidence.append(f"Submitted ICD-10: {', '.join(noncovered_dxs)}")
                policy_evidence.append(f"{ptype} {pid} → ICD-10 non-covered: {', '.join(noncovered_dxs)}")
                explanation = (
                    f"The submitted diagnosis code(s) {', '.join(noncovered_dxs)} are explicitly listed in the "
                    f"{ptype} {pid} non-covered ICD-10 data. "
                    f"The diagnosis requirement is not satisfied."
                )

            if not matched_any:
                # Text fallback
                for dx in request.diagnosis_codes:
                    if dx.lower() in text:
                        status = EvaluationStatus.SATISFIED
                        patient_evidence.append(f"Submitted ICD-10: {dx}")
                        explanation = (
                            f"The submitted diagnosis code {dx} was found referenced "
                            f"in the policy text. The diagnosis requirement is satisfied."
                        )
                        matched_any = True
                        break

                if not matched_any:
                    status = EvaluationStatus.UNKNOWN
                    patient_evidence.append(
                        f"Submitted diagnosis codes: {', '.join(request.diagnosis_codes)}"
                    )
                    explanation = (
                        f"None of the submitted diagnosis codes "
                        f"({', '.join(request.diagnosis_codes)}) were found in the "
                        f"{ptype} {pid} structured code data. "
                        f"The diagnosis requirement cannot be deterministically evaluated."
                    )

        if status == EvaluationStatus.UNKNOWN:
            patient_evidence.append("Could not match any requested codes to this structured requirement.")
            explanation = (
                "The structured requirement could not be matched to any submitted codes. "
                "The requirement cannot be deterministically evaluated."
            )

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
            explanation=explanation,
            authoritative=True,
            mandatory=True
        )

