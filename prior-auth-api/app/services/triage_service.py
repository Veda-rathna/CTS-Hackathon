"""Triage service — deterministic policy-matching engine integrated with RAG and LLM.

This module implements the core triage logic:
1. Normalize inputs.
2. Search for active NCD candidate policies.
3. RAG Retrieval -> NCD Criteria -> Strategy Evaluation -> Evidence Fusion.
4. Jurisdiction check if NCD NOT_ADDRESSED.
5. LCD structured/rule/semantic extraction -> Strategy Evaluation -> Evidence Fusion.
6. Article evaluation via related documents -> deterministic SQL checks.
7. Final Decision Engine.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import List

from app.repositories.interfaces.article_repository import ArticleRepository
from app.repositories.interfaces.ncd_repository import NCDRepository
from app.repositories.interfaces.policy_repository import PolicyRepository
from app.repositories.policy_chunk_repository import PolicyChunkRepository

from app.services.rag.embedding_service import EmbeddingService
from app.services.evaluation.multi_evaluator import MultiEvaluator
from app.services.evaluation.criterion_extractor import CriterionExtractor
from app.services.evaluation.criterion_classifier import CriterionClassifier
from app.services.evaluation.evidence_fusion import EvidenceFusion
from app.services.decision_engine import DecisionEngine

from app.schemas.policy import PolicyMatch
from app.schemas.evaluation import EvaluatedCriterion, EvaluationStatus, EvaluatorType, CriterionType
from app.schemas.triage import (
    DiagnosisEvaluation,
    Evidence,
    MatchedCodes,
    MatchedPolicy,
    RagEvidence,
    TriageDecision,
    TriageRequest,
    TriageResponse,
)

logger = logging.getLogger(__name__)


def _is_policy_effective(policy: PolicyMatch, as_of: date | None = None) -> bool:
    check = as_of or date.today()
    if policy.effective_date and policy.effective_date > check:
        return False
    if policy.end_date and policy.end_date < check:
        return False
    return True

def _filter_latest_effective_policies(
    policies: list[PolicyMatch], as_of: date | None = None
) -> list[PolicyMatch]:
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
    """Triage engine that matches a clinical request to policies using Deterministic+LLM pipeline."""

    def __init__(
        self,
        policy_repository: PolicyRepository,
        article_repository: ArticleRepository,
        ncd_repository: NCDRepository,
        chunk_repository: PolicyChunkRepository,
        evaluator: MultiEvaluator,
        embedding_service: EmbeddingService,
    ) -> None:
        self._policy_repo = policy_repository
        self._article_repo = article_repository
        self._ncd_repo = ncd_repository
        self._chunk_repo = chunk_repository
        self._evaluator = evaluator
        self._embedding_service = embedding_service

    def evaluate(self, request: TriageRequest) -> TriageResponse:
        procedure = request.procedure_code
        diagnoses = request.diagnosis_codes
        state = request.state

        logger.info(
            "Triage started | procedure=%s diagnoses=%s state=%s",
            procedure,
            ",".join(diagnoses),
            state or "N/A",
        )

        all_evidence: List[Evidence] = []
        warnings: List[str] = []
        missing: List[str] = []
        all_criteria: List[EvaluatedCriterion] = []
        all_rag_evidence: List[RagEvidence] = []
        matched_policies: List[MatchedPolicy] = []
        matched_diagnoses = set()
        
        # Determine RAG Query text
        notes = getattr(request, "clinical_notes", "")
        query_text = f"Procedure {procedure}. Diagnoses {', '.join(diagnoses)}. {notes}".strip()
        query_embedding = self._embedding_service.embed_text(query_text) if query_text else []
        # ── Find Candidate Policies (via Evidence Resolver) ───────────────
        from app.services.policy_evidence_resolver import PolicyEvidenceResolver
        
        # Instantiate resolver (could be injected via DI in a larger refactor)
        resolver = PolicyEvidenceResolver(
            self._policy_repo, 
            self._article_repo, 
            self._ncd_repo
        )
        
        evidence_result = resolver.resolve_evidence(procedure, diagnoses, state)
        
        if evidence_result["status"] in ("NOT_FOUND", "UNAVAILABLE") or not evidence_result.get("policies"):
            reason_msg = f"No coverage policy references procedure '{procedure}'."
            if evidence_result["status"] == "UNAVAILABLE":
                reason_msg = f"Policy evidence is currently unavailable (CMS API error). Manual review required."
                decision = TriageDecision.PEND
            else:
                decision = TriageDecision.REQUEST_MORE_INFORMATION
                
            return TriageResponse(
                decision=decision,
                evidence_score=0.0,
                reason=reason_msg,
                reason_codes=["POLICY_NOT_FOUND" if evidence_result["status"] == "NOT_FOUND" else "EVIDENCE_UNAVAILABLE"],
                missing_information=[reason_msg],
                policies=[],
                policy_path=None,
                matched_codes=MatchedCodes(procedure=procedure, diagnosis=[]),
                diagnosis_evaluation=[],
                evidence=[],
                criteria=[],
                warnings=["CMS Coverage API Fallback was attempted but returned no valid evidence." if evidence_result["status"] == "NOT_FOUND" else "CMS Coverage API Fallback failed."],
                evidence_fusion_result="NOT_ADDRESSED",
                decision_basis=(
                    f"{reason_msg} "
                    f"Evidence Fusion: NOT_ADDRESSED. "
                    f"DecisionEngine: NOT_ADDRESSED → {decision.value}."
                )
            )

        all_policies = evidence_result["policies"]

        active_policies = _filter_latest_effective_policies(all_policies)
        if not active_policies:
            return TriageResponse(
                decision=TriageDecision.POLICY_EXPIRED,
                evidence_score=0.0,
                reason=f"All policies referencing procedure code '{procedure}' are expired.",
                reason_codes=["POLICY_EXPIRED"],
                warnings=["All matching policies have expired."],
            )

        ncd_candidates = [p for p in active_policies if p.policy_type.upper() == "NCD"]
        lcd_candidates = [p for p in active_policies if p.policy_type.upper() == "LCD"]

        ncd_result = "NOT_ADDRESSED"
        active_lcd = None
        lcd_result = "NOT_ADDRESSED"
        article_result = "NOT_ADDRESSED"
        
        policy_path = {
            "ncd": {"policy_id": None, "result": "NOT_ADDRESSED"},
            "jurisdiction": {"state": state, "result": "NOT_ADDRESSED"},
            "lcd": {"policy_id": None, "result": "NOT_ADDRESSED"},
            "article": {"policy_id": None, "result": "NOT_ADDRESSED"},
        }

        # ── NCD Evaluation (Phases 3-8) ─────────────────────────────────────
        if ncd_candidates:
            # We have candidate NCDs, let's do RAG retrieval restricted to them
            ncd_ids = [p.policy_id for p in ncd_candidates]
            
            # Phase 4: Constrained Vector Search
            # NOTE: query_embedding may be [] in mock/no-LLM mode.
            # MockPolicyChunkRepository handles this gracefully by ignoring
            # the embedding and matching by policy_id alone.
            ncd_chunks = self._chunk_repo.search_similar(
                query_embedding=query_embedding,
                policy_type="NCD",
                candidate_policy_ids=ncd_ids,
                top_k=5,
                threshold=0.6
            )
            
            ncd_criteria = []
            
            # Phase 4b: Deterministic HCPCS check for each candidate NCD
            # This runs ALWAYS (regardless of RAG) as the authoritative structured layer.
            # Even if RAG returns semantic/unknown criteria, a positive HCPCS match
            # provides a SATISFIED structured criterion so EvidenceFusion → COVERED.
            for p in ncd_candidates:
                ncd_hcpcs_codes = {c.code for c in self._ncd_repo.get_hcpcs(p.policy_id)}
                if ncd_hcpcs_codes:
                    hcpcs_matched = procedure in ncd_hcpcs_codes
                    ncd_criteria.append(EvaluatedCriterion(
                        criterion_id=f"NCD-{p.policy_id}-HCPCS",
                        policy_type="NCD",
                        policy_id=p.policy_id,
                        criterion=f"The requested procedure must be an applicable service under NCD {p.policy_id}.",
                        criterion_type=CriterionType.STRUCTURED,
                        evaluator=EvaluatorType.SQL,
                        status=EvaluationStatus.SATISFIED if hcpcs_matched else EvaluationStatus.NOT_SATISFIED,
                        patient_evidence=[f"Submitted HCPCS: {procedure}"],
                        policy_evidence=[
                            f"NCD {p.policy_id} {'contains' if hcpcs_matched else 'does not contain'} "
                            f"HCPCS {procedure} in its covered-procedure list."
                        ],
                        mandatory=True,
                        authoritative=True,
                        explanation=(
                            f"{'Procedure ' + procedure + ' is listed in NCD ' + p.policy_id + ' covered HCPCS codes. Criterion SATISFIED by deterministic SQL check.'}"
                            if hcpcs_matched else
                            f"Procedure {procedure} is not found in NCD {p.policy_id} covered HCPCS codes. Criterion NOT_SATISFIED by deterministic SQL check."
                        )
                    ))
                    if hcpcs_matched:
                        matched_policies.append(MatchedPolicy(policy_type="NCD", policy_id=p.policy_id, title=p.title))
                        all_evidence.append(Evidence(
                            type="HCPCS", identifier=p.policy_id, code=procedure,
                            result="MATCHED",
                            explanation=f"Procedure code '{procedure}' is listed in NCD {p.policy_id} covered codes."
                        ))
                        break  # First match is sufficient for NCD coverage
            
            # Phase 5: Criterion Extraction & Classification from RAG chunks
            for chunk_tuple in ncd_chunks:
                chunk, distance = chunk_tuple
                all_rag_evidence.append(
                    RagEvidence(
                        policy_id=chunk.policy_id,
                        policy_type=chunk.policy_type,
                        policy_title=ncd_candidates[0].title if ncd_candidates else None,
                        section=chunk.section,
                        chunk_id=str(chunk.id),
                        text=chunk.chunk_text,
                        similarity_score=max(0.0, 1.0 - distance),
                        source="CMS"
                    )
                )
                raw_criteria = CriterionExtractor.extract_from_chunk(chunk)
                for rc in raw_criteria:
                    classified_criterion = CriterionClassifier.classify(rc)
                    
                    # Phase 6: Strategy Evaluation
                    evaluated = self._evaluator.evaluate(classified_criterion, request)
                    ncd_criteria.append(evaluated)
            
            # Phase 7 & 8: Evidence Fusion & Result
            if ncd_criteria:
                ncd_matrix = EvidenceFusion.fuse(ncd_criteria)
                all_criteria.extend(ncd_matrix.criteria)
                ncd_result = EvidenceFusion.resolve_decision(ncd_matrix)
            else:
                # Deterministic fallback if neither RAG nor HCPCS list yielded criteria
                for p in ncd_candidates:
                    ncd_details = self._ncd_repo.get_by_id(p.policy_id)
                    if ncd_details and ncd_details.decision:
                        dec = ncd_details.decision.upper()
                        if "COVERED" in dec and "NON" not in dec:
                            ncd_result = "COVERED"
                            matched_policies.append(MatchedPolicy(policy_type="NCD", policy_id=p.policy_id, title=p.title))
                            all_evidence.append(Evidence(type="HCPCS", identifier=p.policy_id, code=procedure, result="COVERED", explanation="Explicit NCD coverage."))
                            all_criteria.append(EvaluatedCriterion(
                                criterion_id=f"NCD-{p.policy_id}-HCPCS",
                                policy_type="NCD",
                                policy_id=p.policy_id,
                                criterion=f"The requested procedure must be an applicable service under NCD {p.policy_id}.",
                                criterion_type=CriterionType.STRUCTURED,
                                evaluator=EvaluatorType.SQL,
                                status=EvaluationStatus.SATISFIED,
                                patient_evidence=[f"Submitted HCPCS: {procedure}"],
                                policy_evidence=[f"NCD {p.policy_id} explicitly lists {procedure} as covered."],
                                mandatory=True,
                                authoritative=True
                            ))
                            break
                        elif "EXCLUDED" in dec or "NON" in dec:
                            ncd_result = "EXCLUDED"
                            matched_policies.append(MatchedPolicy(policy_type="NCD", policy_id=p.policy_id, title=p.title))
                            all_evidence.append(Evidence(type="HCPCS", identifier=p.policy_id, code=procedure, result="EXCLUDED", explanation="Explicit NCD exclusion."))
                            all_criteria.append(EvaluatedCriterion(
                                criterion_id=f"NCD-{p.policy_id}-HCPCS",
                                policy_type="NCD",
                                policy_id=p.policy_id,
                                criterion=f"The requested procedure must not be explicitly excluded by NCD {p.policy_id}.",
                                criterion_type=CriterionType.STRUCTURED,
                                evaluator=EvaluatorType.SQL,
                                status=EvaluationStatus.NOT_SATISFIED,
                                patient_evidence=[f"Submitted HCPCS: {procedure}"],
                                policy_evidence=[f"NCD {p.policy_id} explicitly excludes {procedure}."],
                                mandatory=True,
                                authoritative=True
                            ))
                            break
            
            policy_path["ncd"] = {"policy_id": ncd_ids[0] if ncd_ids else ncd_candidates[0].policy_id, "result": ncd_result}

        # ── Jurisdiction & LCD (Phase 9 & 10) ─────────────────────────────────
        if ncd_result == "NOT_ADDRESSED":
            if not lcd_candidates:
                missing.append("Missing specific LCD or Article for evaluation.")
                final_decision, decision_reasons, decision_warnings = DecisionEngine.map_to_final(ncd_result, lcd_result, article_result, missing)
                return self._build_response(
                    final_decision, decision_reasons, matched_policies, policy_path,
                    procedure, diagnoses, all_evidence, all_rag_evidence, all_criteria,
                    missing, warnings + decision_warnings,
                    ncd_result=ncd_result, lcd_result=lcd_result, article_result=article_result
                )

            if state:
                jurisdiction_matching = [
                    p for p in lcd_candidates if self._policy_repo.is_state_in_jurisdiction(state, p)
                ]
                if not jurisdiction_matching:
                    all_evidence.append(Evidence(type="JURISDICTION", identifier="", state=state, result="NOT_MATCHED", explanation=f"State '{state}' is outside LCD jurisdictions."))
                    policy_path["jurisdiction"]["result"] = "NOT_MATCHED"
                    missing.append("State outside jurisdiction.")
                    final_decision, decision_reasons, decision_warnings = DecisionEngine.map_to_final(ncd_result, lcd_result, article_result, missing)
                    return self._build_response(
                        final_decision, decision_reasons, matched_policies, policy_path,
                        procedure, diagnoses, all_evidence, all_rag_evidence, all_criteria,
                        missing, warnings + decision_warnings,
                        ncd_result=ncd_result, lcd_result=lcd_result, article_result=article_result
                    )
                
                active_lcd = jurisdiction_matching[0]
                matched_policies.append(MatchedPolicy(policy_type=active_lcd.policy_type, policy_id=active_lcd.policy_id, title=active_lcd.title, article_id=active_lcd.article_id))
                all_evidence.append(Evidence(type="JURISDICTION", identifier=active_lcd.jurisdiction_id or active_lcd.policy_id, state=state, result="MATCHED", explanation=f"State '{state}' matches jurisdiction of LCD {active_lcd.policy_id}."))
                policy_path["jurisdiction"]["result"] = "MATCHED"
            else:
                missing.append("State not provided — jurisdiction could not be verified.")
                active_lcd = lcd_candidates[0] # Default to first if state unknown
                matched_policies.append(MatchedPolicy(policy_type=active_lcd.policy_type, policy_id=active_lcd.policy_id, title=active_lcd.title, article_id=active_lcd.article_id))

            # LCD Evaluation (Deterministic/Narrative)
            # NOTE: query_embedding may be [] in mock/no-LLM mode.
            # MockPolicyChunkRepository handles this gracefully.
            lcd_criteria = []
            lcd_chunks = self._chunk_repo.search_similar(
                query_embedding=query_embedding,
                policy_type="LCD",
                candidate_policy_ids=[active_lcd.policy_id],
                top_k=5,
                threshold=0.8
            )
            for chunk_tuple in lcd_chunks:
                chunk, distance = chunk_tuple
                all_rag_evidence.append(
                    RagEvidence(
                        policy_id=chunk.policy_id,
                        policy_type=chunk.policy_type,
                        policy_title=active_lcd.title if active_lcd else None,
                        section=chunk.section,
                        chunk_id=str(chunk.id),
                        text=chunk.chunk_text,
                        similarity_score=max(0.0, 1.0 - distance),
                        source="CMS"
                    )
                )
                raw_criteria = CriterionExtractor.extract_from_chunk(chunk)
                for rc in raw_criteria:
                    classified_criterion = CriterionClassifier.classify(rc)
                    lcd_criteria.append(self._evaluator.evaluate(classified_criterion, request))
            
            if lcd_criteria:
                lcd_matrix = EvidenceFusion.fuse(lcd_criteria)
                all_criteria.extend(lcd_matrix.criteria)
                lcd_result = EvidenceFusion.resolve_decision(lcd_matrix)
            else:
                lcd_result = "COVERED"  # No RAG criteria extracted → permit Article check
                
            policy_path["lcd"] = {"policy_id": active_lcd.policy_id, "result": lcd_result}

            # ── Article (Phase 11) ───────────────────────────────────────────
            if lcd_result == "COVERED" and active_lcd.article_id:
                article_id = active_lcd.article_id
                
                # Deterministic HCPCS
                hcpcs_codes = {c.code for c in self._article_repo.get_hcpcs(article_id)}
                procedure_matched = procedure in hcpcs_codes
                all_evidence.append(Evidence(type="HCPCS", identifier=article_id, code=procedure, result="MATCHED" if procedure_matched else "NOT_FOUND", explanation=f"Procedure code '{procedure}' {'is' if procedure_matched else 'was not'} listed in article {article_id}."))
                
                all_criteria.append(EvaluatedCriterion(
                    criterion_id=f"ARTICLE-{article_id}-HCPCS",
                    policy_type="ARTICLE",
                    policy_id=article_id,
                    criterion="The requested procedure must be an applicable service under the Article.",
                    criterion_type=CriterionType.STRUCTURED,
                    evaluator=EvaluatorType.SQL,
                    status=EvaluationStatus.SATISFIED if procedure_matched else EvaluationStatus.NOT_SATISFIED,
                    patient_evidence=[f"Submitted HCPCS: {procedure}"],
                    policy_evidence=[f"Article {article_id} {'contains' if procedure_matched else 'does not contain'} HCPCS {procedure} in its coverage list."],
                    mandatory=True,
                    authoritative=True
                ))
                
                # Deterministic ICD-10
                covered_set = {c.code for c in self._article_repo.get_icd10_covered(article_id)}
                noncovered_set = {c.code for c in self._article_repo.get_icd10_noncovered(article_id)}
                
                all_noncovered = True if diagnoses else False
                has_covered = False
                
                for dx in diagnoses:
                    if dx in covered_set:
                        matched_diagnoses.add(dx)
                        has_covered = True
                        all_noncovered = False
                        all_evidence.append(Evidence(type="ICD10", identifier=article_id, code=dx, result="COVERED", explanation=f"Diagnosis '{dx}' is covered."))
                        all_criteria.append(EvaluatedCriterion(
                            criterion_id=f"ARTICLE-{article_id}-ICD10-{dx}",
                            policy_type="ARTICLE",
                            policy_id=article_id,
                            criterion="The patient's diagnosis must be an eligible diagnosis under the Article.",
                            criterion_type=CriterionType.STRUCTURED,
                            evaluator=EvaluatorType.SQL,
                            status=EvaluationStatus.SATISFIED,
                            patient_evidence=[f"Submitted ICD-10: {dx}"],
                            policy_evidence=[f"Diagnosis {dx} is present in the Article's covered ICD-10 data."],
                            mandatory=True,
                            authoritative=True
                        ))
                    elif dx in noncovered_set:
                        all_evidence.append(Evidence(type="ICD10", identifier=article_id, code=dx, result="NOT_COVERED", explanation=f"Diagnosis '{dx}' is explicitly non-covered."))
                        all_criteria.append(EvaluatedCriterion(
                            criterion_id=f"ARTICLE-{article_id}-ICD10-{dx}",
                            policy_type="ARTICLE",
                            policy_id=article_id,
                            criterion="The patient's diagnosis must not be explicitly excluded by the Article.",
                            criterion_type=CriterionType.STRUCTURED,
                            evaluator=EvaluatorType.SQL,
                            status=EvaluationStatus.NOT_SATISFIED,
                            patient_evidence=[f"Submitted ICD-10: {dx}"],
                            policy_evidence=[f"Diagnosis {dx} is present in the Article's non-covered ICD-10 data."],
                            mandatory=True,
                            authoritative=True
                        ))
                    else:
                        all_noncovered = False
                        missing.append(f"Diagnosis code '{dx}' not found in policy code lists.")
                        all_evidence.append(Evidence(type="ICD10", identifier=article_id, code=dx, result="NOT_FOUND", explanation=f"Diagnosis '{dx}' not found in article {article_id}."))
                        
                # Decision Engine (Phase 12)
                if has_covered:
                    article_result = "COVERED"
                elif all_noncovered:
                    article_result = "EXCLUDED"
                else:
                    article_result = "UNKNOWN"
                    missing.append("Missing explicitly covered diagnosis codes.")
                policy_path["article"] = {"policy_id": active_lcd.article_id, "result": article_result}

        final_decision, decision_reasons, decision_warnings = DecisionEngine.map_to_final(ncd_result, lcd_result, article_result, missing)
        return self._build_response(
            final_decision, decision_reasons, matched_policies, policy_path,
            procedure, diagnoses, all_evidence, all_rag_evidence, all_criteria,
            missing, warnings + decision_warnings,
            ncd_result=ncd_result, lcd_result=lcd_result, article_result=article_result
        )

    def _build_response(
        self,
        decision: TriageDecision,
        reason_codes: List[str],
        policies: List[MatchedPolicy],
        policy_path: dict,
        procedure: str,
        diagnoses: List[str],
        evidence: List[Evidence],
        rag_evidence: List[RagEvidence],
        criteria: List[EvaluatedCriterion],
        missing: List[str],
        warnings: List[str],
        ncd_result: str = "NOT_ADDRESSED",
        lcd_result: str = "NOT_ADDRESSED",
        article_result: str = "NOT_ADDRESSED",
    ) -> TriageResponse:

        # Compute evidence_fusion_result: the intermediate coverage resolution
        # before DecisionEngine maps it to the public decision.
        # Priority: article > lcd > ncd (most specific wins)
        if article_result not in ("NOT_ADDRESSED", ""):
            fusion_result = article_result
        elif lcd_result not in ("NOT_ADDRESSED", ""):
            fusion_result = lcd_result
        elif ncd_result not in ("NOT_ADDRESSED", ""):
            fusion_result = ncd_result
        else:
            fusion_result = "NOT_ADDRESSED"

        # Build human-readable reason string
        reason = _build_reason_narrative(decision, reason_codes, ncd_result, lcd_result, article_result, missing)

        # Build decision_basis narrative
        decision_basis = _build_decision_basis(
            decision, reason_codes, fusion_result, criteria
        )

        # Calculate naive deterministic score for backward compatibility
        score = 0.5 if decision != TriageDecision.PEND else 0.0
        if decision == TriageDecision.APPROVE:
            score = 0.9

        dx_evals = [DiagnosisEvaluation(code=d, status="COVERED") for d in diagnoses]

        return TriageResponse(
            decision=decision,
            evidence_score=score,
            requires_prior_authorization=None,
            reason=reason,
            reason_codes=reason_codes,
            policies=policies,
            policy_path=policy_path,
            matched_codes=MatchedCodes(procedure=procedure, diagnosis=diagnoses),
            diagnosis_evaluation=dx_evals,
            evidence=evidence,
            rag_evidence=rag_evidence,
            criteria=criteria,
            missing_information=missing,
            warnings=warnings,
            evidence_fusion_result=fusion_result,
            decision_basis=decision_basis,
        )


def _build_reason_narrative(
    decision: TriageDecision,
    reason_codes: List[str],
    ncd_result: str,
    lcd_result: str,
    article_result: str,
    missing: List[str],
) -> str:
    """Build a human-readable reason string for the triage decision.

    The primary reason code is embedded in parentheses so that automated
    checks on d["reason"] continue to work.
    """
    primary_code = reason_codes[0] if reason_codes else ""

    if decision == TriageDecision.APPROVE:
        if "ARTICLE_CRITERIA_SATISFIED" in reason_codes:
            text = (
                "All applicable policy criteria were satisfied. "
                "The submitted procedure and diagnosis codes are covered under the applicable Article."
            )
        elif "LCD_CRITERIA_SATISFIED" in reason_codes:
            text = (
                "All applicable policy criteria were satisfied. "
                "The submitted procedure meets the Local Coverage Determination criteria."
            )
        elif "NCD_CRITERIA_SATISFIED" in reason_codes:
            text = (
                "All applicable policy criteria were satisfied. "
                "The submitted procedure meets the National Coverage Determination criteria."
            )
        else:
            text = "All applicable policy criteria were satisfied. The request is approved."
        return f"{text} [{primary_code}]" if primary_code else text

    if decision == TriageDecision.PEND:
        if "NCD_EXCLUDES_PROCEDURE" in reason_codes:
            text = (
                "The submitted procedure is explicitly excluded by an applicable "
                "National Coverage Determination (NCD). The request is pended for manual review."
            )
            return f"{text} [NCD_EXCLUDES_PROCEDURE]"
        if "LCD_EXCLUDES_PROCEDURE" in reason_codes:
            text = (
                "The submitted procedure is explicitly excluded by the applicable "
                "Local Coverage Determination (LCD). The request is pended for manual review."
            )
            return f"{text} [LCD_EXCLUDES_PROCEDURE]"
        if "ARTICLE_EXCLUDES_PROCEDURE" in reason_codes:
            text = (
                "The submitted diagnosis is explicitly listed as non-covered in the applicable "
                "Billing and Coding Article. The request is pended for manual review."
            )
            return f"{text} [ARTICLE_EXCLUDES_PROCEDURE]"
        if "AMBIGUOUS_EVIDENCE_REQUIRES_REVIEW" in reason_codes:
            text = (
                "Policy evidence was ambiguous or conflicting. "
                "Manual clinical review is required to determine coverage."
            )
            return f"{text} [AMBIGUOUS_EVIDENCE_REQUIRES_REVIEW]"
        text = (
            "The request could not be automatically approved based on available policy data. "
            "Manual review is required."
        )
        return f"{text} [{primary_code}]" if primary_code else text

    # REQUEST_MORE_INFORMATION
    if "POLICY_NOT_FOUND" in reason_codes:
        text = (
            "No applicable coverage policy was found for the submitted procedure code. "
            "Additional information is required."
        )
        return f"{text} [POLICY_NOT_FOUND]"
    if "MISSING_REQUIRED_INFORMATION" in reason_codes and missing:
        # Strip trailing periods from each item so we don't produce "Item.." double-period.
        items = "; ".join(m.rstrip(".") for m in missing)
        text = (
            f"The request is missing required information: {items}. "
            f"Additional information must be provided before a coverage determination can be made."
        )
        return f"{text} [MISSING_REQUIRED_INFORMATION]"
    text = (
        "Insufficient information is available to determine coverage. "
        "Additional clinical or administrative information is required."
    )
    return f"{text} [{primary_code}]" if primary_code else text



def _build_decision_basis(
    decision: TriageDecision,
    reason_codes: List[str],
    fusion_result: str,
    criteria: List[EvaluatedCriterion],
) -> str:
    """Build a human-readable decision_basis narrative.

    Shows the evidence fusion result, criterion summary, and how the
    DecisionEngine mapped it to the final public decision.
    """
    lines = []

    if decision == TriageDecision.APPROVE:
        lines.append("All mandatory policy criteria were satisfied.")
    elif decision == TriageDecision.PEND:
        lines.append("The request was pended because one or more mandatory policy criteria "
                     "were not satisfied or evidence was ambiguous.")
    else:
        lines.append("Additional information is required to determine coverage.")

    # Criterion bullets
    if criteria:
        for c in criteria:
            evaluator_label = c.evaluator.value
            if evaluator_label == "LLM":
                evaluator_label = "Qwen"
            # Short criterion label from criterion_id
            c_id = c.criterion_id
            status_str = c.status.value
            suffix = f" by {evaluator_label}" if evaluator_label == "Qwen" else ""
            lines.append(f"  • {c_id}: {status_str}{suffix}")
    else:
        lines.append("  • No formal criteria were evaluated (deterministic code matching applied).")

    lines.append(f"Evidence Fusion: {fusion_result}")
    lines.append(f"DecisionEngine: {fusion_result} → {decision.value}")

    return "\n".join(lines)

