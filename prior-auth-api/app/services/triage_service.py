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
from app.repositories.interfaces.lcd_repository import LCDRepository
from app.repositories.interfaces.policy_repository import PolicyRepository
from app.repositories.postgres.lcd_repository import PostgresLCDRepository
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
    """Core triage service enforcing CMS Medicare hierarchical rules."""

    def __init__(
        self,
        policy_repository: PolicyRepository,
        article_repository: ArticleRepository,
        ncd_repository: NCDRepository,
        chunk_repository: PolicyChunkRepository,
        evaluator: MultiEvaluator,
        embedding_service: EmbeddingService,
        lcd_repository: LCDRepository | None = None,
    ) -> None:
        self._policy_repo = policy_repository
        self._article_repo = article_repository
        self._ncd_repo = ncd_repository
        if lcd_repository is not None:
            self._lcd_repo = lcd_repository
        else:
            from app.core.config import get_settings
            if get_settings().use_mock_repositories:
                from app.repositories.mock.lcd_repository import MockLCDRepository
                self._lcd_repo = MockLCDRepository()
            else:
                self._lcd_repo = PostgresLCDRepository()
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
        
        # Determine RAG Query text (embedding computed lazily on-demand)
        notes = getattr(request, "clinical_notes", "")
        query_text = f"Procedure {procedure}. Diagnoses {', '.join(diagnoses)}. {notes}".strip()
        query_embedding: List[float] = []

        def _get_query_embedding() -> List[float]:
            nonlocal query_embedding
            if not query_embedding and query_text:
                query_embedding = self._embedding_service.embed_text(query_text)
            return query_embedding

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
            reason_msg = f"No active coverage policy references procedure '{procedure}' in this jurisdiction."
            if evidence_result["status"] == "UNAVAILABLE":
                reason_msg = "Policy evidence is currently unavailable from Medicare systems. Additional review required."
                decision = TriageDecision.NEED_MORE_INFORMATION
            else:
                decision = TriageDecision.NEED_MORE_INFORMATION

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
                warnings=["CMS policy lookup returned no valid coverage policies." if evidence_result["status"] == "NOT_FOUND" else "CMS policy service temporarily unavailable."],
                evidence_fusion_result="NOT_ADDRESSED",
                decision_basis=f"{reason_msg} Additional documentation or manual review is required."
            )

        all_policies = evidence_result["policies"]

        active_policies = _filter_latest_effective_policies(all_policies)
        if not active_policies:
            return TriageResponse(
                decision=TriageDecision.PEND,
                evidence_score=0.2,
                reason=f"All Medicare policies referencing procedure code '{procedure}' have expired and are no longer active. The case requires nurse/UM review.",
                reason_codes=["POLICY_EXPIRED"],
                warnings=["All matching policies have expired."],
                evidence_fusion_result="NOT_ADDRESSED",
                decision_basis=f"All matching policies for procedure '{procedure}' have expired. Pended for nurse/UM review."
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
                query_embedding=_get_query_embedding(),
                policy_type="NCD",
                candidate_policy_ids=ncd_ids,
                top_k=5,
                threshold=0.85
            )
            
            ncd_criteria = []
            
            # Phase 4b: Deterministic HCPCS check for candidate NCDs
            # This runs ALWAYS (regardless of RAG) as the authoritative structured layer.
            # Even if RAG returns semantic/unknown criteria, a positive HCPCS match
            # provides a SATISFIED structured criterion so EvidenceFusion → COVERED.
            ncd_matched_policy = None
            ncd_excluded_policy = None

            for p in ncd_candidates:
                ncd_details = self._ncd_repo.get_by_id(p.policy_id)
                ncd_hcpcs_codes = {c.code for c in self._ncd_repo.get_hcpcs(p.policy_id)}
                dec = (ncd_details.decision or "").upper() if ncd_details else ""
                if ncd_hcpcs_codes:
                    if procedure in ncd_hcpcs_codes:
                        if "EXCLUDED" in dec or "NON" in dec:
                            ncd_excluded_policy = p
                            break
                        else:
                            ncd_matched_policy = p
                            break
                elif ncd_details and dec:
                    if "EXCLUDED" in dec or "NON" in dec:
                        ncd_excluded_policy = p
                        break
                    elif "COVERED" in dec:
                        ncd_matched_policy = p
                        break

            if ncd_excluded_policy:
                p = ncd_excluded_policy
                ncd_criteria.append(EvaluatedCriterion(
                    criterion_id=f"NCD-{p.policy_id}-HCPCS",
                    policy_type="NCD",
                    policy_id=p.policy_id,
                    criterion=f"The requested procedure must not be explicitly excluded by NCD {p.policy_id}.",
                    criterion_type=CriterionType.STRUCTURED,
                    evaluator=EvaluatorType.SQL,
                    status=EvaluationStatus.NOT_SATISFIED,
                    patient_evidence=[f"Submitted HCPCS: {procedure}"],
                    policy_evidence=[f"NCD {p.policy_id} explicitly excludes HCPCS {procedure}."],
                    mandatory=True,
                    authoritative=True,
                    explanation=f"Procedure {procedure} is listed in NCD {p.policy_id} which EXCLUDES coverage. Criterion NOT_SATISFIED by deterministic SQL check."
                ))
            elif ncd_matched_policy:
                p = ncd_matched_policy
                ncd_criteria.append(EvaluatedCriterion(
                    criterion_id=f"NCD-{p.policy_id}-HCPCS",
                    policy_type="NCD",
                    policy_id=p.policy_id,
                    criterion=f"The requested procedure must be an applicable service under NCD {p.policy_id}.",
                    criterion_type=CriterionType.STRUCTURED,
                    evaluator=EvaluatorType.SQL,
                    status=EvaluationStatus.SATISFIED,
                    patient_evidence=[f"Submitted HCPCS: {procedure}"],
                    policy_evidence=[
                        f"NCD {p.policy_id} contains HCPCS {procedure} in its covered-procedure list."
                    ],
                    mandatory=True,
                    authoritative=True,
                    explanation=f"Procedure {procedure} is listed in NCD {p.policy_id} covered HCPCS codes. Criterion SATISFIED by deterministic SQL check."
                ))
                matched_policies.append(MatchedPolicy(policy_type="NCD", policy_id=p.policy_id, title=p.title))
                all_evidence.append(Evidence(
                    type="HCPCS", identifier=p.policy_id, code=procedure,
                    result="MATCHED",
                    explanation=f"Procedure code '{procedure}' is listed in NCD {p.policy_id} covered codes."
                ))
            
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
                                authoritative=True,
                                explanation=f"Procedure code {procedure} is covered under National Coverage Determination {p.policy_id}."
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
                                authoritative=True,
                                explanation=f"Procedure code {procedure} is explicitly excluded under National Coverage Determination {p.policy_id}."
                            ))
                            break

            
            policy_path["ncd"] = {"policy_id": ncd_ids[0] if ncd_ids else ncd_candidates[0].policy_id, "result": ncd_result}

        # ── Jurisdiction & LCD (Phase 9 & 10) ─────────────────────────────────
        if ncd_result == "NOT_ADDRESSED":
            if not lcd_candidates:
                missing.append("Missing specific LCD or Article for evaluation.")
                final_decision, decision_reasons, decision_warnings = DecisionEngine.map_to_final(
                    ncd_result, lcd_result, article_result, missing, criteria=all_criteria
                )
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
                    final_decision, decision_reasons, decision_warnings = DecisionEngine.map_to_final(
                        ncd_result, lcd_result, article_result, missing, criteria=all_criteria
                    )
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

            # ── LCD Evaluation (Phase 10: SQL Deterministic + Semantic RAG) ──
            lcd_criteria = []

            # Phase 10a: Deterministic SQL checks for LCD (HCPCS & Covered/NonCovered ICD-10)
            lcd_hcpcs = {c.code for c in self._lcd_repo.get_hcpcs(active_lcd.policy_id)}
            if lcd_hcpcs:
                lcd_hcpcs_matched = procedure in lcd_hcpcs
                all_evidence.append(Evidence(
                    type="HCPCS",
                    identifier=active_lcd.policy_id,
                    code=procedure,
                    result="MATCHED" if lcd_hcpcs_matched else "NOT_FOUND",
                    explanation=f"Procedure code '{procedure}' {'is' if lcd_hcpcs_matched else 'was not'} listed in LCD {active_lcd.policy_id} applicable HCPCS data."
                ))
                lcd_criteria.append(EvaluatedCriterion(
                    criterion_id=f"LCD-{active_lcd.policy_id}-HCPCS",
                    policy_type="LCD",
                    policy_id=active_lcd.policy_id,
                    criterion=f"The requested procedure must be an applicable service under LCD {active_lcd.policy_id}.",
                    criterion_type=CriterionType.STRUCTURED,
                    evaluator=EvaluatorType.SQL,
                    status=EvaluationStatus.SATISFIED if lcd_hcpcs_matched else EvaluationStatus.NOT_SATISFIED,
                    patient_evidence=[f"Submitted HCPCS: {procedure}"],
                    policy_evidence=[
                        f"LCD {active_lcd.policy_id} {'contains' if lcd_hcpcs_matched else 'does not contain'} "
                        f"HCPCS {procedure} in its applicable procedure list."
                    ],
                    mandatory=True,
                    authoritative=True,
                    explanation=(
                        f"Procedure {procedure} is listed in LCD {active_lcd.policy_id} applicable HCPCS data. "
                        f"Criterion SATISFIED by deterministic SQL check."
                        if lcd_hcpcs_matched else
                        f"Procedure {procedure} was not found in LCD {active_lcd.policy_id} applicable HCPCS data. "
                        f"Criterion NOT_SATISFIED by deterministic SQL check."
                    )
                ))

            lcd_covered_dx = {c.code for c in self._lcd_repo.get_icd10_covered(active_lcd.policy_id)}
            lcd_noncovered_dx = {c.code for c in self._lcd_repo.get_icd10_noncovered(active_lcd.policy_id)}

            if lcd_covered_dx or lcd_noncovered_dx:
                lcd_has_covered = False
                for dx in diagnoses:
                    if dx in lcd_covered_dx:
                        matched_diagnoses.add(dx)
                        lcd_has_covered = True
                        all_evidence.append(Evidence(
                            type="ICD10", identifier=active_lcd.policy_id, code=dx,
                            result="COVERED",
                            explanation=f"Diagnosis '{dx}' is covered under LCD {active_lcd.policy_id}."
                        ))
                        lcd_criteria.append(EvaluatedCriterion(
                            criterion_id=f"LCD-{active_lcd.policy_id}-ICD10-{dx}",
                            policy_type="LCD",
                            policy_id=active_lcd.policy_id,
                            criterion=f"The patient's diagnosis must be an eligible diagnosis under LCD {active_lcd.policy_id}.",
                            criterion_type=CriterionType.STRUCTURED,
                            evaluator=EvaluatorType.SQL,
                            status=EvaluationStatus.SATISFIED,
                            patient_evidence=[f"Submitted ICD-10: {dx}"],
                            policy_evidence=[f"Diagnosis {dx} is present in LCD {active_lcd.policy_id} covered ICD-10 data."],
                            mandatory=True,
                            authoritative=True,
                            explanation=f"Diagnosis {dx} is covered under LCD {active_lcd.policy_id} structured data."
                        ))
                    elif dx in lcd_noncovered_dx:
                        all_evidence.append(Evidence(
                            type="ICD10", identifier=active_lcd.policy_id, code=dx,
                            result="NOT_COVERED",
                            explanation=f"Diagnosis '{dx}' is explicitly non-covered under LCD {active_lcd.policy_id}."
                        ))

                if not lcd_has_covered and any(dx in lcd_noncovered_dx for dx in diagnoses):
                    for dx in diagnoses:
                        if dx in lcd_noncovered_dx:
                            lcd_criteria.append(EvaluatedCriterion(
                                criterion_id=f"LCD-{active_lcd.policy_id}-ICD10-{dx}",
                                policy_type="LCD",
                                policy_id=active_lcd.policy_id,
                                criterion=f"The patient's diagnosis must not be explicitly excluded by LCD {active_lcd.policy_id}.",
                                criterion_type=CriterionType.STRUCTURED,
                                evaluator=EvaluatorType.SQL,
                                status=EvaluationStatus.NOT_SATISFIED,
                                patient_evidence=[f"Submitted ICD-10: {dx}"],
                                policy_evidence=[f"Diagnosis {dx} is present in LCD {active_lcd.policy_id} non-covered ICD-10 data."],
                                mandatory=True,
                                authoritative=True,
                                explanation=f"Diagnosis {dx} is explicitly non-covered under LCD {active_lcd.policy_id} structured data."
                            ))

            # Phase 10b: Constrained Vector Search & Semantic RAG Extraction for LCD
            lcd_chunks = self._chunk_repo.search_similar(
                query_embedding=_get_query_embedding(),
                policy_type="LCD",
                candidate_policy_ids=[active_lcd.policy_id],
                top_k=5,
                threshold=0.85
            )
            if not lcd_chunks:
                lcd_details = self._lcd_repo.get_by_id(active_lcd.policy_id)
                if lcd_details:
                    text_content = (lcd_details.indication or "") + "\n" + (lcd_details.summary_of_evidence or "")
                    if text_content.strip():
                        from app.models.policy_chunk import PolicyChunk
                        synthetic_chunk = PolicyChunk(
                            policy_type="LCD",
                            policy_id=active_lcd.policy_id,
                            section="indications_limitations",
                            chunk_text=text_content.strip()[:4000]
                        )
                        lcd_chunks = [(synthetic_chunk, 0.2)]

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
            
            # Phase 10c: Evidence Fusion for LCD
            if lcd_criteria:
                lcd_matrix = EvidenceFusion.fuse(lcd_criteria)
                all_criteria.extend(lcd_matrix.criteria)
                lcd_result = EvidenceFusion.resolve_decision(lcd_matrix)
            else:
                lcd_result = "COVERED"  # No criteria extracted → permit Article check
                
            policy_path["lcd"] = {"policy_id": active_lcd.policy_id, "result": lcd_result}

            # ── Article (Phase 11) ───────────────────────────────────────────
            if lcd_result in ("COVERED", "UNKNOWN") and active_lcd.article_id:
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
                    requirement="The requested procedure must be an applicable service under the Article.",
                    criterion_type=CriterionType.STRUCTURED,
                    evaluator=EvaluatorType.SQL,
                    status=EvaluationStatus.SATISFIED if procedure_matched else EvaluationStatus.NOT_SATISFIED,
                    patient_evidence=[f"Submitted HCPCS: {procedure}"],
                    policy_evidence=[f"Article {article_id} {'contains' if procedure_matched else 'does not contain'} HCPCS {procedure} in its coverage list."],
                    explanation=f"Procedure code {procedure} is {'present in' if procedure_matched else 'not found in'} Article {article_id} covered procedure list.",
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
                            requirement="The patient's diagnosis must be an eligible diagnosis under the Article.",
                            criterion_type=CriterionType.STRUCTURED,
                            evaluator=EvaluatorType.SQL,
                            status=EvaluationStatus.SATISFIED,
                            patient_evidence=[f"Submitted ICD-10: {dx}"],
                            policy_evidence=[f"Diagnosis {dx} is present in the Article's covered ICD-10 data."],
                            explanation=f"Diagnosis code {dx} is documented as an approved indication under Article {article_id}.",
                            mandatory=True,
                            authoritative=True
                        ))
                    elif dx in noncovered_set:
                        all_evidence.append(Evidence(type="ICD10", identifier=article_id, code=dx, result="NOT_COVERED", explanation=f"Diagnosis '{dx}' is explicitly non-covered."))
                    else:
                        all_noncovered = False
                        missing.append(f"Diagnosis code '{dx}' not found in policy code lists.")
                        all_evidence.append(Evidence(type="ICD10", identifier=article_id, code=dx, result="NOT_FOUND", explanation=f"Diagnosis '{dx}' not found in article {article_id}."))
                        
                # Decision Engine (Phase 12)
                if has_covered:
                    article_result = "COVERED"
                elif all_noncovered:
                    article_result = "EXCLUDED"
                    for dx in diagnoses:
                        if dx in noncovered_set:
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
                    article_result = "UNKNOWN"
                    missing.append("Missing explicitly covered diagnosis codes.")
                policy_path["article"] = {"policy_id": active_lcd.article_id, "result": article_result}

        # Populate clean, structured missing information from mandatory UNKNOWN criteria
        for c in all_criteria:
            if c.mandatory and c.status == EvaluationStatus.UNKNOWN:
                clean_item = _format_missing_criterion(c)
                if clean_item and clean_item not in missing:
                    missing.append(clean_item)

        # Deduplicate missing information
        missing = list(dict.fromkeys(m for m in missing if m and str(m).strip()))

        final_decision, decision_reasons, decision_warnings = DecisionEngine.map_to_final(
            ncd_result, lcd_result, article_result, missing, criteria=all_criteria
        )
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

        score = 0.9 if decision == TriageDecision.APPROVE else (0.5 if decision == TriageDecision.NEED_MORE_INFORMATION else 0.2)

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
    """Build a clean, nurse/provider-friendly reason string for the triage decision."""
    if decision == TriageDecision.APPROVE:
        if "ARTICLE_CRITERIA_SATISFIED" in reason_codes:
            return "All applicable policy criteria were satisfied. The submitted procedure and diagnosis codes are covered under the applicable Medicare policy."
        elif "LCD_CRITERIA_SATISFIED" in reason_codes:
            return "All applicable policy criteria were satisfied. The submitted procedure meets Local Coverage Determination criteria."
        elif "NCD_CRITERIA_SATISFIED" in reason_codes:
            return "All applicable policy criteria were satisfied. The submitted procedure meets National Coverage Determination criteria."
        return "All mandatory policy requirements were satisfied by the clinical documentation. The authorization request is approved."

    if decision in (TriageDecision.PEND, TriageDecision.DENY):
        if "POLICY_EXPIRED" in reason_codes:
            return "All matching coverage policies for this procedure code have expired and are no longer in effect. The case requires nurse/UM review."
        if "NCD_EXCLUDES_PROCEDURE" in reason_codes:
            return "The requested service conflicts with an applicable National Coverage Determination (NCD) policy exclusion. The case requires nurse/UM review to determine the appropriate disposition."
        if "LCD_EXCLUDES_PROCEDURE" in reason_codes:
            return "The requested service conflicts with an applicable Local Coverage Determination (LCD) policy exclusion. The case requires nurse/UM review to determine the appropriate disposition."
        if "ARTICLE_EXCLUDES_PROCEDURE" in reason_codes:
            return "The submitted diagnosis code conflicts with policy coverage rules. The case requires nurse/UM review to determine the appropriate disposition."
        if "MANDATORY_CRITERIA_NOT_SATISFIED" in reason_codes:
            return "One or more mandatory clinical policy requirements were not satisfied based on available documentation. The case requires nurse/UM review."
        return "The request conflicts with an applicable coverage policy or requires clinical adjudication. The case requires nurse/UM review to determine the appropriate disposition."

    # NEED_MORE_INFORMATION
    if "POLICY_NOT_FOUND" in reason_codes:
        return "No applicable Medicare coverage policy was found for the submitted procedure code in this jurisdiction. Additional documentation or manual review is required."
    if "MISSING_REQUIRED_INFORMATION" in reason_codes and missing:
        items = "; ".join(m.rstrip(".") for m in missing)
        return f"Additional documentation is required to complete evaluation: {items}."
    if "AMBIGUOUS_EVIDENCE_REQUIRES_DOCUMENTATION" in reason_codes or "AMBIGUOUS_EVIDENCE_REQUIRES_REVIEW" in reason_codes:
        return "Clinical documentation is required to verify medical necessity under applicable policy criteria."
    return "Insufficient documentation is available to determine coverage. Please provide supporting clinical notes."


def _build_decision_basis(
    decision: TriageDecision,
    reason_codes: List[str],
    fusion_result: str,
    criteria: List[EvaluatedCriterion],
) -> str:
    """Build a clean, provider-friendly decision basis narrative."""
    lines = []

    if decision == TriageDecision.APPROVE:
        lines.append("All mandatory policy requirements were satisfied by clinical evidence.")
    elif decision in (TriageDecision.PEND, TriageDecision.DENY):
        lines.append("The requested service conflicts with an applicable policy exclusion or requires human adjudication. The case has been pended for nurse/UM review.")
    else:
        lines.append("Additional clinical information or documentation is required before an approval can be issued.")

    if criteria:
        for c in criteria:
            status_str = c.status.value
            lines.append(f"  • {c.criterion_id}: {status_str} — {c.criterion}")
    else:
        lines.append("  • Evaluated via deterministic code and coverage rules.")

    return "\n".join(lines)


def _format_missing_criterion(c: EvaluatedCriterion) -> str:
    """Format clean, concise provider-facing missing clinical information."""
    txt = (c.requirement or c.criterion or "").strip()
    txt_lower = txt.lower()
    if any(k in txt_lower for k in ("conservative", "physical therapy", "trial", "failed", "drug", "nsaid")):
        return "Evidence of failed conservative physical therapy or medication trial."
    if any(k in txt_lower for k in ("mri", "imaging", "radiograph", "x-ray", "scan")):
        return "Diagnostic imaging report or radiographic confirmation (MRI / X-ray)."
    if any(k in txt_lower for k in ("radiculopathy", "nerve root", "straight leg raise")):
        return "Documentation of confirmed lumbar or cervical radiculopathy."
    if any(k in txt_lower for k in ("biopsy",)):
        return "Biopsy confirmation of diagnosis."
    if any(k in txt_lower for k in ("osteoarthritis", "joint space", "kellgren")):
        return "Clinical documentation of documented joint disease severity."
    # Clean fallback: strip bullets and truncate if too long
    import re
    clean = re.sub(r'^(?:[-*•]|\d+\.)\s*', '', txt)
    if len(clean) > 100:
        clean = clean[:97].rstrip() + "..."
    return f"Clinical documentation for: {clean}"


