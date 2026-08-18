"""Synthea Repository for dynamically fetching patient history."""

from __future__ import annotations

import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.synthea import SyntheaCondition, SyntheaProcedure, SyntheaObservation, SyntheaCrosswalk

logger = logging.getLogger(__name__)

class SyntheaRepository:
    """Repository for querying Synthea patient records to build clinical history."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_patient_history(self, patient_id: str) -> str:
        """Fetch and format a patient's medical history into a clinical text block.
        
        Fetches all conditions and procedures, and the 30 most recent observations 
        to provide comprehensive evidence for AI evaluation while preventing context overload.
        """
        logger.info("SyntheaRepository | Fetching history for patient_id=%s", patient_id)
        if not self._session:
            return f"[System: No prior Synthea medical history found for patient {patient_id}]"

        try:
            non_clinical_patterns = [
                "[prapare]", "survey", "social-history", "afraid", "transportation", "transport",
                "partner", "armed forces", "living or staying", "stress",
                "gender identity", "sexual orientation", "employment", "unemployed", "education",
                "food insecurity", "housing", "language", "race", "ethnicity",
                "unable to get", "felt safe", "physically and emotionally safe",
                "violence", "review due", "screening", "dental", "gingiv", "plaque", "teeth",
                "fluoride", "oral health", "assessment of", "medication review", "domestic abuse",
                "alcohol use", "substance use", "drug abuse",
            ]

            raw_conditions = (
                self._session.query(SyntheaCondition)
                .filter_by(patient_id=patient_id)
                .order_by(desc(SyntheaCondition.start_date))
                .all()
            )
            conditions = []
            for c in raw_conditions:
                desc_lower = (c.description or "").lower()
                if any(pat in desc_lower for pat in non_clinical_patterns):
                    continue
                conditions.append(c)
                if len(conditions) >= 10:
                    break

            raw_procedures = (
                self._session.query(SyntheaProcedure)
                .filter_by(patient_id=patient_id)
                .order_by(desc(SyntheaProcedure.start_date))
                .all()
            )
            procedures = []
            for p in raw_procedures:
                desc_lower = (p.description or "").lower()
                if any(pat in desc_lower for pat in non_clinical_patterns):
                    continue
                procedures.append(p)
                if len(procedures) >= 10:
                    break
            
            raw_observations = (
                self._session.query(SyntheaObservation)
                .filter_by(patient_id=patient_id)
                .order_by(desc(SyntheaObservation.date))
                .limit(50)
                .all()
            )

            observations = []
            for o in raw_observations:
                cat = (o.category or "").lower()
                desc_lower = (o.description or "").lower()
                
                # Exclude survey / social-history category
                if cat in ("survey", "social-history"):
                    continue
                
                # Exclude non-clinical observations by text
                if any(pat in desc_lower for pat in non_clinical_patterns):
                    continue
                
                observations.append(o)
                if len(observations) >= 10:
                    break

            lines = []
            if conditions:
                lines.append("HISTORICAL CONDITIONS:")
                for c in conditions:
                    date_str = c.start_date.isoformat() if c.start_date else "Unknown date"
                    lines.append(f"  - {date_str}: {c.description} (Code: {c.code})")
                lines.append("")

            if procedures:
                lines.append("PRIOR PROCEDURES:")
                for p in procedures:
                    date_str = p.start_date.strftime("%Y-%m-%d") if p.start_date else "Unknown date"
                    lines.append(f"  - {date_str}: {p.description} (Code: {p.code}) - Reason: {p.reasondescription or 'N/A'}")
                lines.append("")

            if observations:
                lines.append("RECENT CLINICAL OBSERVATIONS:")
                for o in observations:
                    date_str = o.date.strftime("%Y-%m-%d") if o.date else "Unknown date"
                    unit_str = f" {o.units}" if o.units else ""
                    lines.append(f"  - {date_str}: {o.description} = {o.value}{unit_str}")
                lines.append("")

            if not lines:
                return f"[System: No prior Synthea medical history found for patient {patient_id}]"

            history_text = "\n".join(lines).strip()
            return f"--- SYNTHEA DATABASE PATIENT HISTORY ---\n{history_text}\n----------------------------------------"

        except Exception as e:
            logger.error("SyntheaRepository | Error fetching history for %s: %s", patient_id, e)
            return f"[System: Error retrieving Synthea history for {patient_id}]"

    def crosswalk_code(self, source_code: str, target_system: str = None) -> str:
        """Translate a SNOMED code to CPT/ICD-10 if a mapping exists."""
        if not source_code or not self._session:
            return source_code
        
        query = self._session.query(SyntheaCrosswalk).filter_by(source_code=source_code.strip())
        if target_system:
            query = query.filter_by(target_system=target_system)
            
        mapping = query.first()
        if mapping:
            logger.info("SyntheaRepository | Crosswalked %s -> %s (%s)", source_code, mapping.target_code, mapping.target_system)
            return mapping.target_code
            
        return source_code

