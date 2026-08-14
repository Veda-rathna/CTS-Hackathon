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
        
        text = criterion.criterion.lower()
        
        # 1. Age Rules
        if re.search(r'\b(age|years old)\b', text):
            if request.patient_age is None:
                status = EvaluationStatus.UNKNOWN
                patient_evidence.append("Patient age is unknown.")
            else:
                # Basic operator extraction
                if re.search(r'(?:>=|greater than or equal)\s*(\d+)', text):
                    val = int(re.search(r'(?:>=|greater than or equal)\s*(\d+)', text).group(1))
                    status = EvaluationStatus.SATISFIED if request.patient_age >= val else EvaluationStatus.NOT_SATISFIED
                    patient_evidence.append(f"Patient age {request.patient_age} {'is >=' if status == EvaluationStatus.SATISFIED else 'is not >='} {val}.")
                elif re.search(r'(?:<=|less than or equal)\s*(\d+)', text):
                    val = int(re.search(r'(?:<=|less than or equal)\s*(\d+)', text).group(1))
                    status = EvaluationStatus.SATISFIED if request.patient_age <= val else EvaluationStatus.NOT_SATISFIED
                    patient_evidence.append(f"Patient age {request.patient_age} {'is <=' if status == EvaluationStatus.SATISFIED else 'is not <='} {val}.")
                elif re.search(r'(?:>|greater than)\s*(\d+)', text):
                    val = int(re.search(r'(?:>|greater than)\s*(\d+)', text).group(1))
                    status = EvaluationStatus.SATISFIED if request.patient_age > val else EvaluationStatus.NOT_SATISFIED
                    patient_evidence.append(f"Patient age {request.patient_age} {'is >' if status == EvaluationStatus.SATISFIED else 'is not >'} {val}.")
                elif re.search(r'(?:<|less than)\s*(\d+)', text):
                    val = int(re.search(r'(?:<|less than)\s*(\d+)', text).group(1))
                    status = EvaluationStatus.SATISFIED if request.patient_age < val else EvaluationStatus.NOT_SATISFIED
                    patient_evidence.append(f"Patient age {request.patient_age} {'is <' if status == EvaluationStatus.SATISFIED else 'is not <'} {val}.")
                elif re.search(r'(?:==|equals|is)\s*(\d+)', text):
                    val = int(re.search(r'(?:==|equals|is)\s*(\d+)', text).group(1))
                    status = EvaluationStatus.SATISFIED if request.patient_age == val else EvaluationStatus.NOT_SATISFIED
                    patient_evidence.append(f"Patient age {request.patient_age} {'==' if status == EvaluationStatus.SATISFIED else '!='} {val}.")
                else:
                    status = EvaluationStatus.UNKNOWN
                    patient_evidence.append("Unrecognized operator for age rule.")
                    
        # 2. Date Rules (e.g. "service date must be before 2024-01-01")
        elif re.search(r'\b(date|service date)\b', text):
            if not getattr(request, "service_date", None):
                status = EvaluationStatus.UNKNOWN
                patient_evidence.append("Service date is unknown.")
            else:
                try:
                    s_date = date.fromisoformat(request.service_date)
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
                    if date_match:
                        val_date = date.fromisoformat(date_match.group(1))
                        if re.search(r'\b(before|<|<=)\b', text):
                            status = EvaluationStatus.SATISFIED if s_date < val_date else EvaluationStatus.NOT_SATISFIED
                            patient_evidence.append(f"Service date {s_date} {'is' if status == EvaluationStatus.SATISFIED else 'is not'} before {val_date}.")
                        elif re.search(r'\b(after|>|>=)\b', text):
                            status = EvaluationStatus.SATISFIED if s_date > val_date else EvaluationStatus.NOT_SATISFIED
                            patient_evidence.append(f"Service date {s_date} {'is' if status == EvaluationStatus.SATISFIED else 'is not'} after {val_date}.")
                        elif re.search(r'\b(on|equals|==)\b', text):
                            status = EvaluationStatus.SATISFIED if s_date == val_date else EvaluationStatus.NOT_SATISFIED
                            patient_evidence.append(f"Service date {s_date} {'==' if status == EvaluationStatus.SATISFIED else '!='} {val_date}.")
                        else:
                            status = EvaluationStatus.UNKNOWN
                            patient_evidence.append("Unrecognized date operator.")
                    else:
                        status = EvaluationStatus.UNKNOWN
                        patient_evidence.append("No valid YYYY-MM-DD date found in text.")
                except ValueError:
                    status = EvaluationStatus.UNKNOWN
                    patient_evidence.append("Invalid service date format (must be YYYY-MM-DD).")
        
        else:
            # Fallback for unknown rule logic
            status = EvaluationStatus.UNKNOWN
            patient_evidence.append("No explicit deterministic rule logic implemented for this text.")

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
            authoritative=True,
            mandatory=True
        )
