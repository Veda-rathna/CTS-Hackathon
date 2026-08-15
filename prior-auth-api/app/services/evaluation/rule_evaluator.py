"""Rule-Based Evaluator."""
from __future__ import annotations

import re
from datetime import date
from app.schemas.evaluation import EvaluatedCriterion, EvaluationStatus, EvaluatorType, PolicyCriterion
from app.schemas.triage import TriageRequest

class RuleEvaluator:
    """Evaluates RULE_BASED criteria using deterministic Python rules."""
    
    def evaluate(self, criterion: PolicyCriterion, request: TriageRequest) -> EvaluatedCriterion:
        status = EvaluationStatus.UNKNOWN
        patient_evidence = []
        policy_evidence = [criterion.criterion]
        explanation = ""

        text = criterion.criterion.lower()
        
        # 1. Age Rules
        if re.search(r'\b(age|years old)\b', text):
            if request.patient_age is None:
                status = EvaluationStatus.UNKNOWN
                patient_evidence.append("Patient age is unknown.")
                explanation = (
                    "The policy requires an age check, but no patient age was provided. "
                    "The requirement cannot be evaluated."
                )
            else:
                # Basic operator extraction
                if re.search(r'(?:>=|greater than or equal)\s*(\d+)', text):
                    val = int(re.search(r'(?:>=|greater than or equal)\s*(\d+)', text).group(1))
                    status = EvaluationStatus.SATISFIED if request.patient_age >= val else EvaluationStatus.NOT_SATISFIED
                    patient_evidence.append(f"Patient age: {request.patient_age}")
                    explanation = (f"The policy requires the patient to be at least {val} years old. "
                                   f"The patient is {request.patient_age} years old. "
                                   f"The age requirement is {'satisfied' if status == EvaluationStatus.SATISFIED else 'not satisfied'}.")
                elif re.search(r'(?:<=|less than or equal)\s*(\d+)', text):
                    val = int(re.search(r'(?:<=|less than or equal)\s*(\d+)', text).group(1))
                    status = EvaluationStatus.SATISFIED if request.patient_age <= val else EvaluationStatus.NOT_SATISFIED
                    patient_evidence.append(f"Patient age: {request.patient_age}")
                    explanation = (f"The policy requires the patient to be at most {val} years old. "
                                   f"The patient is {request.patient_age} years old. "
                                   f"The age requirement is {'satisfied' if status == EvaluationStatus.SATISFIED else 'not satisfied'}.")
                elif re.search(r'(?:>|greater than)\s*(\d+)', text):
                    val = int(re.search(r'(?:>|greater than)\s*(\d+)', text).group(1))
                    status = EvaluationStatus.SATISFIED if request.patient_age > val else EvaluationStatus.NOT_SATISFIED
                    patient_evidence.append(f"Patient age: {request.patient_age}")
                    explanation = (f"The policy requires the patient to be older than {val} years. "
                                   f"The patient is {request.patient_age} years old. "
                                   f"The age requirement is {'satisfied' if status == EvaluationStatus.SATISFIED else 'not satisfied'}.")
                elif re.search(r'(?:<|less than)\s*(\d+)', text):
                    val = int(re.search(r'(?:<|less than)\s*(\d+)', text).group(1))
                    status = EvaluationStatus.SATISFIED if request.patient_age < val else EvaluationStatus.NOT_SATISFIED
                    patient_evidence.append(f"Patient age: {request.patient_age}")
                    explanation = (f"The policy requires the patient to be younger than {val} years. "
                                   f"The patient is {request.patient_age} years old. "
                                   f"The age requirement is {'satisfied' if status == EvaluationStatus.SATISFIED else 'not satisfied'}.")
                elif re.search(r'(?:==|equals|is)\s*(\d+)', text):
                    val = int(re.search(r'(?:==|equals|is)\s*(\d+)', text).group(1))
                    status = EvaluationStatus.SATISFIED if request.patient_age == val else EvaluationStatus.NOT_SATISFIED
                    patient_evidence.append(f"Patient age: {request.patient_age}")
                    explanation = (f"The policy requires the patient to be exactly {val} years old. "
                                   f"The patient is {request.patient_age} years old. "
                                   f"The age requirement is {'satisfied' if status == EvaluationStatus.SATISFIED else 'not satisfied'}.")
                else:
                    status = EvaluationStatus.UNKNOWN
                    patient_evidence.append("Unrecognized operator for age rule.")
                    explanation = ("An age requirement was identified but the comparison operator "
                                   "could not be parsed. The requirement cannot be evaluated.")
                    
        # 2. Date Rules (e.g. "service date must be before 2024-01-01")
        elif re.search(r'\b(date|service date)\b', text):
            if not getattr(request, "service_date", None):
                status = EvaluationStatus.UNKNOWN
                patient_evidence.append("Service date is unknown.")
                explanation = ("The policy requires a service date check, but no service date was provided. "
                               "The requirement cannot be evaluated.")
            else:
                try:
                    s_date = date.fromisoformat(request.service_date)
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
                    if date_match:
                        val_date = date.fromisoformat(date_match.group(1))
                        if re.search(r'\b(before|<|<=)\b', text):
                            status = EvaluationStatus.SATISFIED if s_date < val_date else EvaluationStatus.NOT_SATISFIED
                            patient_evidence.append(f"Service date: {s_date}")
                            explanation = (f"The policy requires the service date to be before {val_date}. "
                                           f"The submitted service date is {s_date}. "
                                           f"The date requirement is {'satisfied' if status == EvaluationStatus.SATISFIED else 'not satisfied'}.")
                        elif re.search(r'\b(after|>|>=)\b', text):
                            status = EvaluationStatus.SATISFIED if s_date > val_date else EvaluationStatus.NOT_SATISFIED
                            patient_evidence.append(f"Service date: {s_date}")
                            explanation = (f"The policy requires the service date to be after {val_date}. "
                                           f"The submitted service date is {s_date}. "
                                           f"The date requirement is {'satisfied' if status == EvaluationStatus.SATISFIED else 'not satisfied'}.")
                        elif re.search(r'\b(on|equals|==)\b', text):
                            status = EvaluationStatus.SATISFIED if s_date == val_date else EvaluationStatus.NOT_SATISFIED
                            patient_evidence.append(f"Service date: {s_date}")
                            explanation = (f"The policy requires the service date to be exactly {val_date}. "
                                           f"The submitted service date is {s_date}. "
                                           f"The date requirement is {'satisfied' if status == EvaluationStatus.SATISFIED else 'not satisfied'}.")
                        else:
                            status = EvaluationStatus.UNKNOWN
                            patient_evidence.append("Unrecognized date operator.")
                            explanation = ("A date requirement was identified but the comparison operator "
                                           "could not be parsed. The requirement cannot be evaluated.")
                    else:
                        status = EvaluationStatus.UNKNOWN
                        patient_evidence.append("No valid YYYY-MM-DD date found in text.")
                        explanation = ("A date requirement was identified but no reference date "
                                       "(YYYY-MM-DD) could be extracted from the policy text.")
                except ValueError:
                    status = EvaluationStatus.UNKNOWN
                    patient_evidence.append("Invalid service date format (must be YYYY-MM-DD).")
                    explanation = ("The submitted service date could not be parsed. "
                                   "Dates must be in YYYY-MM-DD format.")
        
        else:
            # Fallback for unknown rule logic
            status = EvaluationStatus.UNKNOWN
            patient_evidence.append("No explicit deterministic rule logic implemented for this text.")
            explanation = ("A rule-based requirement was identified but no matching evaluation logic "
                           "exists for this criterion text. The requirement cannot be evaluated.")

        return EvaluatedCriterion(
            criterion_id=criterion.criterion_id,
            policy_type=criterion.policy_type,
            policy_id=criterion.policy_id,
            criterion=criterion.criterion,
            criterion_type=criterion.type,
            evaluator=EvaluatorType.RULES,
            status=status,
            patient_evidence=patient_evidence,
            policy_evidence=policy_evidence,
            explanation=explanation,
            authoritative=True,
            mandatory=True
        )
