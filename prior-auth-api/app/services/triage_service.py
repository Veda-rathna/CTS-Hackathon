"""Triage service — Hybrid Deterministic/Semantic policy engine.

Implements the multi-evaluator pipeline with RAG and LLM integration,
while preserving deterministic exact-match authority.
"""
from __future__ import annotations

import logging
from datetime import date

from app.core.config import Settings
from app.repositories.interfaces.article_repository import ArticleRepository
from app.repositories.interfaces.lcd_repository import LCDRepository
from app.repositories.interfaces.ncd_repository import NCDRepository
from app.repositories.interfaces.policy_repository import PolicyRepository
from app.schemas.evaluation import PolicyEvaluationResult
from app.schemas.policy import PolicyMatch
from app.schemas.triage import (
    DiagnosisEvaluation,
    Evidence,
    TriageRequest,
    TriageResponse,
)
from app.services.evaluation.criteria_extractor import CriteriaExtractor
from app.services.evaluation.decision_engine import DecisionEngine
from app.services.evaluation.evidence_fusion import EvidenceFusion
from app.services.evaluation.multi_evaluator import MultiEvaluator
from app.services.policy_content_service import PolicyContentService

# Import Protocol for the retriever to avoid circular imports
from app.services.rag.vector_policy_retriever import PolicyRetriever

logger = logging.getLogger(__name__)


def _is_policy_effective(policy: PolicyMatch, as_of: date) -> bool:
    if policy.effective_date and policy.effective_date > as_of:
        return False
    if policy.end_date and policy.end_date < as_of:
        return False
    return True


def _filter_latest_effective_policies(
    policies: list[PolicyMatch], as_of: date
) -> list[PolicyMatch]:
    """Filter policies to keep only the most recent effective version per ID."""
    active = [p for p in policies if _is_policy_effective(p, as_of)]
    grouped = {}
    for p in active:
        if p.policy_id not in grouped:
            grouped[p.policy_id] = p
        else:
            existing = grouped[p.policy_id]
            if p.effective_date and existing.effective_date:
                if p.effective_date > existing.effective_date:
                    grouped[p.policy_id] = p
            elif p.effective_date:
                grouped[p.policy_id] = p
    return list(grouped.values())


class TriageService:
    """Triage engine that matches a clinical request to policies using RAG/LLM and rules."""

    def __init__(
        self,
        policy_repository: PolicyRepository,
        article_repository: ArticleRepository,
        ncd_repository: NCDRepository,
        lcd_repository: LCDRepository,
        policy_content: PolicyContentService,
        rag_retriever: PolicyRetriever,
        extractor: CriteriaExtractor,
        multi_evaluator: MultiEvaluator,
        fusion: EvidenceFusion,
        decision_engine: DecisionEngine,
        settings: Settings,
    ) -> None:
        self._policy_repo = policy_repository
        self._article_repo = article_repository
        self._ncd_repo = ncd_repository
        self._lcd_repo = lcd_repository
        
        self._policy_content = policy_content
        self._rag_retriever = rag_retriever
        self._extractor = extractor
        self._multi_evaluator = multi_evaluator
        self._fusion = fusion
        self._decision_engine = decision_engine
        self._settings = settings

    def _build_query(self, request: TriageRequest) -> str:
        """Build search query for RAG from facts."""
        q = f"Procedure {request.procedure_code}. "
        if request.diagnosis_codes:
            q += f"Diagnoses: {', '.join(request.diagnosis_codes)}. "
        if request.clinical_notes:
            q += request.clinical_notes
        return q

    # ── Public entry point ────────────────────────────────────────────────────

    def evaluate(self, request: TriageRequest) -> TriageResponse:
        """Run the full triage pipeline."""
        procedure = request.procedure_code
        state = request.state

        evidence: list[Evidence] = []
        warnings: list[str] = []
        policy_path: list[PolicyEvaluationResult] = []

        # ── Service date handling ──────────────────────────────────
        if request.service_date:
            effective_as_of = request.service_date
        else:
            effective_as_of = date.today()
            warnings.append(
                "Service date not provided. Policy version applicability is UNVERIFIED. "
                "The system used today's date for filtering, which may not reflect the actual service date."
            )

        # ── Policy resolution (existing) ──────────────────────────
        all_policies = self._policy_repo.find_policies_for_procedure(procedure)
        if not all_policies:
            return self._decision_engine._build_response(
                decision="POLICY_NOT_FOUND",
                reason=f"No policy was found for procedure code '{procedure}'.",
                reason_codes=["POLICY_NOT_FOUND"],
                policy_path=policy_path,
                evidence=evidence,
                warnings=warnings,
                procedure=procedure
            )

        active_policies = _filter_latest_effective_policies(all_policies, effective_as_of)
        if not active_policies:
            warnings.append("All matching policies have expired based on service date.")
            return self._decision_engine._build_response(
                decision="POLICY_EXPIRED",
                reason=f"All policies referencing procedure code '{procedure}' are expired.",
                reason_codes=["POLICY_EXPIRED"],
                policy_path=policy_path,
                evidence=evidence,
                warnings=warnings,
                procedure=procedure
            )

        ncd_policies = [p for p in active_policies if p.policy_type.upper() == "NCD"]
        lcd_policies = [p for p in active_policies if p.policy_type.upper() == "LCD"]

        # ── NCD Evaluation ─────────────────────────────
        ncd_result = None
        for ncd_policy in ncd_policies:
            ncd_details = self._ncd_repo.get_by_id(ncd_policy.policy_id)
            if not ncd_details:
                continue

            ncd_sections = self._policy_content.get_ncd_sections(ncd_policy.policy_id)
            
            if self._settings.rag_enabled:
                retrieval = self._rag_retriever.retrieve(
                    query=self._build_query(request),
                    candidate_sections=ncd_sections,
                    min_score=self._settings.vector_min_score
                )

                if retrieval.status == "RETRIEVAL_UNAVAILABLE":
                    warnings.append("RAG unavailable. Using structured evaluation only.")
                    retrieved_sections = []
                elif retrieval.status == "RETRIEVAL_NO_MATCH":
                    retrieved_sections = []
                else:
                    retrieved_sections = retrieval.sections
            else:
                retrieval = None
                retrieved_sections = []

            criteria = self._extractor.extract(
                structured_data=ncd_details,
                policy_sections=retrieved_sections,
                request_facts=request
            )
            
            matrix = self._multi_evaluator.evaluate_all(
                criteria=criteria,
                request=request,
                policy_data=ncd_details,
                policy_sections=retrieved_sections
            )
            
            ncd_eval = self._fusion.determine_ncd_status(
                matrix=matrix, 
                ncd_hint=getattr(ncd_details, "decision", None)
            )
            ncd_eval.policy_id = ncd_policy.policy_id
            ncd_eval.title = ncd_policy.title
            if retrieval:
                ncd_eval.retrieval_status = retrieval.status
                
            policy_path.append(ncd_eval)

            if ncd_eval.overall_status == "EXCLUDED":
                return self._decision_engine.decide(
                    ncd_eval, None, None, policy_path, evidence, warnings, procedure
                )

            if ncd_eval.overall_status == "COVERED":
                ncd_result = ncd_eval
                break  # NCD coverage is authoritative

        # ── Jurisdiction + LCD ───────────
        lcd_result = None
        if ncd_result is None or ncd_result.overall_status == "NOT_ADDRESSED":
            if not lcd_policies:
                return self._decision_engine._build_response(
                    decision="POLICY_NOT_FOUND",
                    reason=f"NCDs do not address coverage and no LCDs exist for procedure '{procedure}'.",
                    reason_codes=["NO_APPLICABLE_LCD"],
                    policy_path=policy_path,
                    evidence=evidence,
                    warnings=warnings,
                    procedure=procedure
                )

            # Jurisdiction resolution
            if state:
                jurisdiction_matching = [
                    p for p in lcd_policies if self._policy_repo.is_state_in_jurisdiction(state, p)
                ]
                if not jurisdiction_matching:
                    warnings.append(f"State '{state}' is outside policy jurisdiction.")
                    return self._decision_engine._build_response(
                        decision="OUTSIDE_JURISDICTION",
                        reason=f"State '{state}' is not covered by the jurisdiction of the matching LCD. Contact your MAC.",
                        reason_codes=["OUTSIDE_JURISDICTION"],
                        policy_path=policy_path,
                        evidence=evidence,
                        warnings=warnings,
                        procedure=procedure
                    )
                candidate_policies = jurisdiction_matching
            else:
                # No state provided, just take the first LCD
                candidate_policies = lcd_policies

            lcd_policy = candidate_policies[0]
            lcd_details = self._lcd_repo.get_by_id(lcd_policy.policy_id)

            if lcd_details:
                lcd_sections = self._policy_content.get_lcd_sections(lcd_policy.policy_id)

                lcd_criteria = self._extractor.extract(
                    structured_data=lcd_details,
                    policy_sections=lcd_sections,
                    request_facts=request
                )
                
                lcd_matrix = self._multi_evaluator.evaluate_all(
                    criteria=lcd_criteria,
                    request=request,
                    policy_data=lcd_details,
                    policy_sections=lcd_sections
                )
                
                lcd_eval = self._fusion.determine_lcd_status(lcd_matrix)
                lcd_eval.policy_id = lcd_policy.policy_id
                lcd_eval.title = lcd_policy.title
                
                policy_path.append(lcd_eval)
                lcd_result = lcd_eval

                if lcd_eval.overall_status == "EXCLUDED":
                    return self._decision_engine.decide(
                        ncd_result, lcd_eval, None, policy_path, evidence, warnings, procedure
                    )

                if lcd_eval.overall_status == "UNKNOWN":
                    return self._decision_engine.decide(
                        ncd_result, lcd_eval, None, policy_path, evidence, warnings, procedure
                    )
                    # Article is NOT executed if LCD is UNKNOWN

        # ── Article Validation ──────────────────
        # Reached only when NCD COVERED or LCD COVERED
        article_result = None
        best_policy = None
        if lcd_result:
            best_policy = next((p for p in lcd_policies if p.policy_id == lcd_result.policy_id), None)
        elif ncd_result:
            best_policy = next((p for p in ncd_policies if p.policy_id == ncd_result.policy_id), None)

        if best_policy and best_policy.article_id:
            article_id = best_policy.article_id
            article_details = self._article_repo.get_by_id(article_id)
            
            if article_details:
                article_sections = self._policy_content.get_article_sections(article_id)
                
                art_criteria = self._extractor.extract(
                    structured_data=article_details,
                    policy_sections=article_sections,
                    request_facts=request
                )
                
                # Use MultiEvaluator and EvidenceFusion exactly like NCD and LCD
                art_matrix = self._multi_evaluator.evaluate_all(
                    criteria=art_criteria,
                    request=request,
                    policy_data=article_details,
                    policy_sections=article_sections
                )
                
                art_eval = self._fusion.determine_article_status(art_matrix)
                art_eval.policy_id = article_id
                art_eval.title = getattr(article_details, "title", None)
                
                policy_path.append(art_eval)
                article_result = art_eval

        # ── Final Decision ────────────────────────────────────────
        return self._decision_engine.decide(
            ncd_result=ncd_result,
            lcd_result=lcd_result,
            article_result=article_result,
            policy_path=policy_path,
            evidence=evidence,
            warnings=warnings,
            procedure=procedure
        )
