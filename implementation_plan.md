# Prior Authorization Triage & Policy Companion — Final Implementation Plan (v3)

> [!NOTE]
> Final revision incorporating all 18 original corrections + 5 final amendments. This plan is **implementation-ready**.

---

## Frozen Architecture

```
                PRIOR AUTH REQUEST
                        │
                        ▼
                FACT EXTRACTION
                        │
                        ▼
            STRUCTURED POLICY RESOLUTION
                        │
                        ▼
                  NCD CANDIDATES
                        │
                        ▼
                 CONSTRAINED RAG
                        │
                        ▼
                NCD POLICY CONTENT
                        │
                        ▼
              CRITERIA EXTRACTION
                        │
                        ▼
              CRITERION CLASSIFIER
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
       SQL/STRUCT     RULES          LLM
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                 EVIDENCE MATRIX
                        │
                        ▼
                   NCD RESULT
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
       COVERED       EXCLUDED     NOT_ADDRESSED
          │             │             │
          │             ▼             ▼
          │            DENY      JURISDICTION
          │                           │
          │                           ▼
          │                          LCD
          │                           │
          │                           ▼
          │                    MULTI-EVALUATOR
          │                           │
          │                           ▼
          │                    EVIDENCE MATRIX
          │                           │
          │                           ▼
          │                       LCD RESULT
          │                           │
          │              ┌────────────┼───────────┐
          │              ▼            ▼           ▼
          │           COVERED      EXCLUDED     UNKNOWN
          │              │            │           │
          │              │            ▼           ▼
          │              │           DENY        PEND
          │              │          (return)    (return)
          │              │
          └──────────────┤
                         ▼
                      ARTICLE
                   (downstream only —
                    cannot override
                    NCD/LCD coverage)
                         │
                  DETERMINISTIC
                   CODE CHECK
                         │
                         ▼
                  DOCUMENT CHECK
                     (LLM if needed)
                         │
                         ▼
                  FINAL VALIDATION
                         │
                         ▼
                  DECISION ENGINE
                         │
                 APPROVE / PEND / DENY
```

---

## Core Principle

```
┌─────────────────────────────┐
│       POLICY RESOLUTION     │
│  SQL + Relationships + RAG  │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      POLICY EVALUATION      │
│  SQL + Rules + LLM          │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       EVIDENCE FUSION       │
│  (criterion-type authority) │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│    DETERMINISTIC DECISION   │
└─────────────────────────────┘
```

---

## Amendment #1 — Article Authority Rule

> [!CAUTION]
> Article is downstream coding/documentation validation. It **cannot independently overturn** an established NCD or LCD coverage determination.

```
RULE: NCD/LCD COVERAGE AUTHORITY

NCD COVERED is authoritative for national coverage.
    → Article CANNOT override to DENY.

LCD COVERED establishes local coverage applicability.
    → Article CANNOT independently overturn LCD COVERED.

Article provides:
    - HCPCS/CPT code validation (is the code listed?)
    - ICD-10 coverage validation (is the diagnosis in the covered list?)
    - Documentation existence check (required docs present?)
    - Documentation content interpretation (LLM if needed)

Article issues produce:
    ┌──────────────────────────────────┬─────────────────────┐
    │ Article Finding                  │ Result              │
    ├──────────────────────────────────┼─────────────────────┤
    │ All codes match, docs complete   │ Continue → APPROVE  │
    │ Missing documentation            │ PEND                │
    │ Coding conflict (code not listed)│ Flag for review     │
    │ Non-covered ICD-10 in Article    │ Warning + review    │
    └──────────────────────────────────┴─────────────────────┘

Article does NOT independently produce:
    - DENY that overrides NCD COVERED
    - DENY that overrides LCD COVERED
    - A coverage determination of its own
```

This means the corrected NCD COVERED path is:

```python
if ncd_result == COVERED:
    # NCD coverage is authoritative
    article = resolve_article(facts)
    article_result = evaluate_article(facts, article)

    if article_result.has_missing_documentation:
        return pend(reason="NCD covers procedure; required documentation missing")
    if article_result.has_coding_conflict:
        return nurse_review(reason="NCD covers procedure; article coding conflict requires review")
    # All clear
    return likely_covered(ncd_evidence, article_evidence)
```

And the LCD COVERED path:

```python
if lcd_result == COVERED:
    article = resolve_article(facts)
    article_result = evaluate_article(facts, article)

    if article_result.has_missing_documentation:
        return pend(reason="LCD covers procedure; required documentation missing")
    if article_result.has_coding_conflict:
        return nurse_review(reason="LCD covers procedure; article coding conflict requires review")
    return likely_covered(lcd_evidence, article_evidence)
```

---

## Amendment #2 — service_date Handling

> [!CAUTION]
> Do NOT silently default `service_date` to `date.today()` for policy applicability.

```python
class TriageRequest(BaseModel):
    procedure_code: str = Field(..., min_length=1)
    diagnosis_codes: list[str] = Field(..., min_length=1)
    state: str | None = Field(default=None, max_length=2)
    patient_age: int | None = Field(default=None, ge=0)

    service_date: date | None = Field(
        default=None,
        description=(
            "Date of the proposed service. Determines which policy version applies. "
            "When omitted, policy-version applicability is flagged as UNVERIFIED."
        ),
    )

    clinical_notes: str | None = Field(
        default=None,
        description="Free-text clinical notes for semantic policy evaluation.",
    )
```

In the engine:

```python
def evaluate(request: TriageRequest) -> TriageResponse:
    if request.service_date:
        effective_as_of = request.service_date
        date_verified = True
    else:
        effective_as_of = date.today()  # used only for filtering, not as truth
        date_verified = False
        warnings.append(
            "Service date not provided. Policy version applicability is UNVERIFIED. "
            "The system used today's date for filtering, which may not reflect "
            "the actual service date."
        )

    active_policies = filter_effective(all_policies, as_of=effective_as_of)
    # ...
```

This way:
- The system still functions without `service_date`
- The response **explicitly warns** that policy version was not verified
- No silent assumption that today = actual service date

---

## Amendment #3 — NCD.decision Provenance

> [!CAUTION]
> Do not assume the existing `NCD.decision` field is CMS-authoritative ground truth. Inspect its provenance.

```python
# In the NCD evaluation flow:

def evaluate_ncd(ncd_detail, facts, rag_sections):
    # Check if the NCD has a pre-parsed decision field
    if ncd_detail.decision:
        # IMPORTANT: Determine provenance
        # If this was parsed from authoritative CMS data (e.g., the CMS
        # transmittal or NCD database explicitly states "Covered" / "Non-Covered"),
        # treat it as a structured criterion.
        #
        # If this was previously generated by an interpretation script,
        # it is a HINT for the multi-evaluator, NOT ground truth.

        decision_upper = ncd_detail.decision.upper()

        if decision_upper in ("COVERED", "NON_COVERED", "EXCLUDED"):
            # Use as a high-priority structured hint
            # But still run the multi-evaluator for full criterion evaluation
            # The decision field provides the NCD's OVERALL stance,
            # individual criteria may still need evaluation
            pass

        if "NOT_ADDRESSED" in decision_upper or "UNKNOWN" in decision_upper:
            # NCD does not cover/exclude this procedure nationally
            return NCDResult(status=NOT_ADDRESSED)

    # Always proceed to criterion-level evaluation for COVERED/EXCLUDED
    # to produce the full Evidence Matrix
    criteria = criteria_extractor.extract(ncd_detail, rag_sections, facts)
    evidence_matrix = multi_evaluate(criteria, facts)
    return evidence_fusion.determine_ncd_status(evidence_matrix, ncd_hint=ncd_detail.decision)
```

The key principle: **the `decision` field is used as a hint** that biases the NCD evaluation toward a particular outcome, but the multi-evaluator still runs to produce the Evidence Matrix. If the multi-evaluator contradicts the hint, that conflict is logged and the deterministic evidence takes precedence.

---

## Amendment #4 — RAG Failure vs No-Match Distinction

> [!CAUTION]
> Distinguish infrastructure failure from a genuine no-match result. They have different audit trails and fallback paths.

```python
from enum import Enum

class RetrievalStatus(str, Enum):
    """Internal retrieval outcome for audit trail."""
    MATCHED = "RETRIEVAL_MATCHED"
    NO_MATCH = "RETRIEVAL_NO_MATCH"       # search succeeded, nothing above threshold
    UNAVAILABLE = "RETRIEVAL_UNAVAILABLE"  # embedding service / vector DB down

class RetrievalResult(BaseModel):
    status: RetrievalStatus
    sections: list[PolicySection] = []
    scores: list[float] = []
    error: str | None = None  # populated only for UNAVAILABLE
```

Handling:

```python
retrieval = rag_retriever.retrieve(query, candidate_ncd_ids)

match retrieval.status:
    case RetrievalStatus.MATCHED:
        # Normal path — proceed with retrieved sections
        criteria = extract_criteria(retrieval.sections, facts)
        # ...

    case RetrievalStatus.NO_MATCH:
        # RAG searched successfully but found nothing relevant
        # Fall back to deterministic evaluation using NCD.decision field
        # and any structured code relationships
        logger.info("RAG: no relevant sections found for NCD candidates %s", candidate_ncd_ids)
        return evaluate_ncd_deterministic_only(ncd_detail, facts)

    case RetrievalStatus.UNAVAILABLE:
        # Infrastructure failure — log for ops, fall back safely
        logger.error("RAG: retrieval infrastructure unavailable: %s", retrieval.error)
        warnings.append("Policy content retrieval unavailable. Evaluation limited to structured data.")
        return evaluate_ncd_deterministic_only(ncd_detail, facts)
```

Audit trail records which path was taken:

```python
evidence.append(Evidence(
    type="RAG_RETRIEVAL",
    identifier=ncd_id,
    result=retrieval.status.value,
    explanation="..." ,
))
```

---

## Amendment #5 — Criterion Provenance

> [!CAUTION]
> Every extracted criterion must record exactly where it came from for full audit traceability.

```python
class CriterionSource(BaseModel):
    """Traces a criterion back to its origin in the policy text."""
    policy_type: str               # NCD, LCD, ARTICLE
    policy_id: str                 # e.g., "L39054"
    policy_version: str | None = None
    section: str                   # e.g., "indications_limitations", "doc_reqs"
    chunk_id: str | None = None    # RAG chunk ID if retrieved via vector search
    extraction_method: Literal[
        "STRUCTURED_FIELD",         # directly from DB column (e.g., LCD.diagnoses_support)
        "CODE_RELATIONSHIP",        # from code tables (LCDIcd10Covered, etc.)
        "DETERMINISTIC_PARSER",     # regex/rule-based extraction from text
        "LLM"                       # LLM extracted from unstructured text
    ]

class CriterionEvaluation(BaseModel):
    criterion_id: str
    criterion: str                  # human-readable criterion text
    criterion_type: Literal["STRUCTURED", "RULE_BASED", "SEMANTIC", "DOCUMENT"]
    source: CriterionSource         # ← PROVENANCE

    evaluator: Literal["SQL", "RULE_ENGINE", "LLM", "DOCUMENT_RULE"]
    status: Literal["SATISFIED", "NOT_SATISFIED", "UNKNOWN"]
    authoritative: bool = True      # False if overridden by higher-precedence evaluator

    patient_evidence: list[str] = []
    policy_evidence: list[str] = []
    explanation: str = ""
    confidence: float | None = None  # metadata only, never used for decisions
```

Example:

```json
{
    "criterion_id": "C1",
    "criterion": "Diagnosis must be M17.12",
    "criterion_type": "STRUCTURED",
    "source": {
        "policy_type": "LCD",
        "policy_id": "L39054",
        "policy_version": "1",
        "section": "diagnoses_support",
        "chunk_id": null,
        "extraction_method": "CODE_RELATIONSHIP"
    },
    "evaluator": "SQL",
    "status": "SATISFIED",
    "authoritative": true,
    "patient_evidence": ["Submitted diagnosis: M17.12"],
    "policy_evidence": ["M17.12 listed in LCD L39054 covered ICD-10 codes"],
    "explanation": "ICD-10 M17.12 exact match in covered code list."
}
```

```json
{
    "criterion_id": "C4",
    "criterion": "Failed conservative treatment for at least 6 months",
    "criterion_type": "SEMANTIC",
    "source": {
        "policy_type": "NCD",
        "policy_id": "NCD123",
        "policy_version": "2",
        "section": "indications_limitations",
        "chunk_id": "NCD123_chunk_04",
        "extraction_method": "LLM"
    },
    "evaluator": "LLM",
    "status": "SATISFIED",
    "authoritative": true,
    "patient_evidence": ["Patient completed PT twice weekly for six months with persistent symptoms."],
    "policy_evidence": ["Policy requires documented failure of conservative treatment."],
    "explanation": "Clinical notes describe 6 months of PT with ongoing symptoms, satisfying the conservative treatment failure requirement."
}
```

---

## Evidence Fusion — Criterion-Type Authority

> [!IMPORTANT]
> Authority belongs to the **criterion type**, not a blanket SQL > LLM rule.

```python
def fuse_evidence(criteria_results: list[CriterionEvaluation]) -> EvidenceMatrix:
    """Fuse multi-evaluator results with criterion-type-based authority."""
    for result in criteria_results:
        if result.criterion_type == "STRUCTURED":
            # Structured criteria: deterministic evaluator is authoritative
            # LLM cannot override an exact code match/non-match
            if result.evaluator in ("SQL", "RULE_ENGINE"):
                result.authoritative = True
            elif result.evaluator == "LLM":
                # LLM attempted to evaluate a structured criterion
                # Check if deterministic result exists
                det = find_deterministic_for_criterion(result.criterion_id)
                if det:
                    result.status = det.status
                    result.authoritative = False
                    result.explanation += f" [Overridden by {det.evaluator}]"

        elif result.criterion_type == "RULE_BASED":
            # Rule-based criteria: Python rule engine is authoritative for calculation
            # LLM may have extracted the facts, but the rule evaluates them
            if result.evaluator == "RULE_ENGINE":
                result.authoritative = True

        elif result.criterion_type == "SEMANTIC":
            # Semantic criteria: LLM is the appropriate evaluator
            # No deterministic override applicable
            result.authoritative = True

        elif result.criterion_type == "DOCUMENT":
            # Document criteria: existence is deterministic, meaning is LLM
            result.authoritative = True

    return EvidenceMatrix(criteria=criteria_results)
```

**Example — LLM Disagreement (structured criterion):**

```
Criterion: ICD-10 must be M17.12
Submitted: M17.11

SQL evaluator:  NOT_SATISFIED  (M17.11 ≠ M17.12)
LLM evaluator:  SATISFIED      ("M17.11 is closely related to M17.12")

FINAL: NOT_SATISFIED  ← SQL wins because this is a STRUCTURED criterion
```

**Example — LLM evaluates semantic criterion:**

```
Criterion: Clinical evidence demonstrates failed conservative therapy
Submitted: "Patient completed PT for 6 months with persistent pain"

LLM evaluator: SATISFIED

FINAL: SATISFIED  ← LLM is the appropriate evaluator for SEMANTIC criteria
```

---

## Schema Naming Hierarchy

> [!NOTE]
> Three-layer naming that makes the architecture immediately readable.

```python
# Layer 1: Per-criterion (internal)
class CriterionEvaluation(BaseModel):
    """Result of evaluating a single atomic policy criterion."""
    status: Literal["SATISFIED", "NOT_SATISFIED", "UNKNOWN"]
    # ...

# Layer 2: Per-policy (internal)
class PolicyEvaluationResult(BaseModel):
    """Aggregated result of evaluating all criteria for one policy."""
    policy_id: str
    policy_type: Literal["NCD", "LCD", "ARTICLE"]
    criteria: list[CriterionEvaluation]
    overall_status: str  # NCD: COVERED/EXCLUDED/NOT_ADDRESSED
                         # LCD: COVERED/EXCLUDED/UNKNOWN
                         # Article: MATCHED/NOT_MATCHED/UNKNOWN
    retrieval_status: RetrievalStatus | None = None
    explanation: str = ""

# Layer 3: Final decision (external — maps to existing TriageDecision enum)
# Uses existing TriageResponse with TriageDecision enum (preserved)
# Extended with optional criteria_evaluation and policy_path
```

---

## Corrected Pseudocode (Final)

```python
def evaluate(self, request: TriageRequest) -> TriageResponse:
    facts = extract_request_facts(request)
    evidence: list[Evidence] = []
    warnings: list[str] = []
    policy_path: list[PolicyEvaluationResult] = []

    # ── Service date handling ──────────────────────────────────
    if request.service_date:
        effective_as_of = request.service_date
    else:
        effective_as_of = date.today()
        warnings.append(
            "Service date not provided. Policy version applicability is UNVERIFIED."
        )

    # ── Policy resolution (existing) ──────────────────────────
    all_policies = self._policy_repo.find_policies_for_procedure(facts.procedure_code)
    active_policies = filter_effective(all_policies, as_of=effective_as_of)
    ncd_policies, lcd_policies = split_by_type(active_policies)

    # ── NCD Evaluation (enhanced) ─────────────────────────────
    ncd_result = None
    for ncd_policy in ncd_policies:
        ncd_detail = self._ncd_repo.get_by_id(ncd_policy.policy_id)

        # Stage 1: Structured candidate (already resolved by find_policies)
        # Stage 2: Constrained RAG within this NCD
        ncd_sections = self._policy_content.get_ncd_sections(ncd_policy.policy_id)
        retrieval = self._rag_retriever.retrieve(
            query=build_query(facts),
            candidate_sections=ncd_sections,
            min_score=settings.vector_min_score
        )

        if retrieval.status == RETRIEVAL_UNAVAILABLE:
            warnings.append("RAG unavailable. Using structured evaluation only.")
            ncd_eval = evaluate_ncd_deterministic(ncd_detail, facts)
        elif retrieval.status == RETRIEVAL_NO_MATCH:
            ncd_eval = evaluate_ncd_deterministic(ncd_detail, facts)
        else:
            # Full multi-evaluator pipeline
            criteria = self._extractor.extract(
                structured_data=ncd_detail,
                policy_sections=retrieval.sections,
                request_facts=facts
            )
            matrix = self._multi_evaluate(criteria, facts)
            ncd_eval = self._fusion.determine_ncd_status(
                matrix, ncd_hint=ncd_detail.decision
            )

        policy_path.append(ncd_eval)

        if ncd_eval.overall_status == "EXCLUDED":
            return deny(ncd_eval, policy_path, evidence, warnings)

        if ncd_eval.overall_status == "COVERED":
            ncd_result = ncd_eval
            break  # proceed to Article (NCD coverage is authoritative)

        # NOT_ADDRESSED → continue

    # ── Jurisdiction + LCD (when NCD NOT_ADDRESSED) ───────────
    lcd_result = None
    if ncd_result is None or ncd_result.overall_status == "NOT_ADDRESSED":
        # Jurisdiction resolution (fully deterministic)
        jurisdiction = resolve_jurisdiction(facts, lcd_policies)
        if not jurisdiction:
            return outside_jurisdiction(...)

        lcd = resolve_lcd(facts, jurisdiction)
        lcd_sections = self._policy_content.get_lcd_sections(lcd.id)

        lcd_criteria = self._extractor.extract(
            structured_data=lcd,
            policy_sections=lcd_sections,
            request_facts=facts
        )
        lcd_matrix = self._multi_evaluate(lcd_criteria, facts)
        lcd_result = self._fusion.determine_lcd_status(lcd_matrix)
        policy_path.append(lcd_result)

        if lcd_result.overall_status == "EXCLUDED":
            return deny(lcd_result, policy_path, evidence, warnings)

        if lcd_result.overall_status == "UNKNOWN":
            return pend(lcd_result, policy_path, evidence, warnings)
            # ← Article is NOT executed

    # ── Article Validation (downstream only) ──────────────────
    # Reached only when NCD COVERED or LCD COVERED
    article = resolve_article(facts)
    article_result = evaluate_article_deterministic(facts, article)
    # HCPCS → SQL, ICD-10 covered/non-covered → SQL
    # Documentation existence → deterministic
    # Documentation meaning → LLM only if needed

    policy_path.append(article_result)

    # Article CANNOT override NCD/LCD coverage
    if article_result.has_missing_documentation:
        return pend(
            reason="Coverage established; required documentation missing",
            policy_path=policy_path
        )
    if article_result.has_coding_conflict:
        return nurse_review(
            reason="Coverage established; article coding conflict requires review",
            policy_path=policy_path
        )

    # ── Final Decision ────────────────────────────────────────
    return self._decision_engine.decide(
        ncd_result=ncd_result,
        lcd_result=lcd_result,
        article_result=article_result,
        policy_path=policy_path,
        evidence=evidence,
        warnings=warnings
    )
```

---

## Decision Engine — Explicit Precedence

```python
class DecisionEngine:
    """Deterministic final decision from Evidence Matrix + policy path."""

    PRECEDENCE = [
        # 1. Explicit deterministic exclusion
        ("EXCLUSION", "Any policy explicitly excludes → DENY"),
        # 2. Mandatory criterion NOT_SATISFIED (deterministic)
        ("MANDATORY_FAIL", "Mandatory criterion failed → DENY"),
        # 3. Mandatory criterion UNKNOWN
        ("MANDATORY_UNKNOWN", "Mandatory criterion unknown → PEND"),
        # 4. All mandatory criteria SATISFIED
        ("ALL_SATISFIED", "All criteria met → continue toward APPROVE"),
    ]

    def decide(self, ncd_result, lcd_result, article_result, **ctx) -> TriageResponse:
        # Explicit exclusion at any level → DENY
        for result in [ncd_result, lcd_result]:
            if result and result.overall_status == "EXCLUDED":
                return self._deny(result, ctx)

        # Mandatory criterion NOT_SATISFIED → DENY
        all_criteria = self._collect_criteria(ncd_result, lcd_result, article_result)
        mandatory_failed = [c for c in all_criteria
                           if c.mandatory and c.status == "NOT_SATISFIED"]
        if mandatory_failed:
            return self._deny_criteria(mandatory_failed, ctx)

        # Mandatory criterion UNKNOWN → PEND
        mandatory_unknown = [c for c in all_criteria
                            if c.mandatory and c.status == "UNKNOWN"]
        if mandatory_unknown:
            return self._pend(mandatory_unknown, ctx)

        # Article issues → PEND or REVIEW (cannot override coverage)
        if article_result and article_result.has_missing_documentation:
            return self._pend_documentation(article_result, ctx)
        if article_result and article_result.has_coding_conflict:
            return self._nurse_review(article_result, ctx)

        # All clear
        return self._approve(ctx)
```

---

## Complete Component Structure

```
app/
├── services/
│   ├── triage_service.py                 # [MODIFY] integrate new pipeline
│   ├── ncd_service.py                    # [PRESERVE]
│   ├── lcd_service.py                    # [PRESERVE]
│   ├── article_service.py               # [PRESERVE]
│   ├── policy_service.py                 # [PRESERVE]
│   │
│   ├── policy_content_service.py         # [NEW] normalized section extraction
│   │
│   ├── rag/                              # [NEW] constrained RAG subsystem
│   │   ├── __init__.py
│   │   ├── embedding_service.py          # configurable embedding model
│   │   ├── chunking_service.py           # normalize → section → chunk → metadata
│   │   ├── policy_retriever.py           # Protocol (RetrievalResult with status)
│   │   └── vector_policy_retriever.py    # pgvector impl (threshold, no IVFFlat)
│   │
│   ├── evaluation/                       # [NEW] multi-evaluator pipeline
│   │   ├── __init__.py
│   │   ├── schemas.py                    # CriterionEvaluation (with CriterionSource),
│   │   │                                 # PolicyEvaluationResult, EvidenceMatrix,
│   │   │                                 # RetrievalStatus, RetrievalResult
│   │   ├── criterion_classifier.py       # structured-metadata-first classification
│   │   ├── criteria_extractor.py         # structured → parser → LLM (with provenance)
│   │   ├── structured_evaluator.py       # SQL/exact-match evaluator
│   │   ├── rule_evaluator.py             # Python deterministic rules
│   │   ├── semantic_evaluator.py         # LLM (graceful degradation per criterion)
│   │   ├── evidence_fusion.py            # criterion-type authority precedence
│   │   └── decision_engine.py            # explicit precedence → TriageDecision
│   │
│   └── llm/                              # [NEW] LLM integration
│       ├── __init__.py
│       ├── llm_client.py                 # Abstract client (Claude default)
│       ├── clinical_extractor.py         # Extract facts from clinical_notes
│       └── prompts/
│           ├── __init__.py
│           ├── criteria_extraction.py
│           ├── semantic_evaluation.py
│           ├── clinical_extraction.py
│           └── explanation_generation.py
│
├── models/
│   └── policy_embedding.py              # [NEW] pgvector (configurable dimension)
│
├── schemas/
│   └── evaluation.py                    # [NEW] CriterionEvaluation, PolicyEvaluationResult,
│                                        #        CriterionSource, RetrievalStatus
```

---

## Files to Modify

| File | Modification |
|---|---|
| [`config.py`](file:///d:/PROJECTS/CTS-Hackathon/prior-auth-api/app/core/config.py) | Add LLM/RAG/embedding/threshold settings |
| [`triage_service.py`](file:///d:/PROJECTS/CTS-Hackathon/prior-auth-api/app/services/triage_service.py) | Integrate multi-evaluator; correct LCD→Article flow; service_date; Article authority |
| [`triage.py` (schema)](file:///d:/PROJECTS/CTS-Hackathon/prior-auth-api/app/schemas/triage.py) | Add `service_date`, `clinical_notes` to request; `criteria_evaluation`, `policy_path` to response |
| [`repositories.py` (DI)](file:///d:/PROJECTS/CTS-Hackathon/prior-auth-api/app/dependencies/repositories.py) | Wire PolicyContentService, evaluators, RAG, LLM |
| [`base.py` (db)](file:///d:/PROJECTS/CTS-Hackathon/prior-auth-api/app/db/base.py) | Import PolicyEmbedding model |
| [`handlers.py`](file:///d:/PROJECTS/CTS-Hackathon/prior-auth-api/app/exceptions/handlers.py) | Add `LLMServiceError` exception |
| [`requirements.txt`](file:///d:/PROJECTS/CTS-Hackathon/prior-auth-api/requirements.txt) | Add: `anthropic`, `sentence-transformers`, `pgvector`, `numpy` |
| [`docker-compose.yml`](file:///d:/PROJECTS/CTS-Hackathon/prior-auth-api/docker-compose.yml) | Use `pgvector/pgvector:pg16`; add LLM env vars |
| [`.env`](file:///d:/PROJECTS/CTS-Hackathon/prior-auth-api/.env) | Add LLM/RAG/embedding config vars |

> [!NOTE]
> No modifications to repository interfaces. Existing `get_by_id()` already returns all text fields. New `PolicyContentService` wraps existing repos.

---

## Database Changes

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE policy_embeddings (
    id SERIAL PRIMARY KEY,
    policy_type VARCHAR(10) NOT NULL,
    policy_id VARCHAR(50) NOT NULL,
    policy_version INT NOT NULL,
    section VARCHAR(100) NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector,                    -- dimension set by application
    effective_date DATE,
    end_date DATE,
    status VARCHAR(20),
    jurisdiction_id VARCHAR(50),
    contractor_id VARCHAR(50),
    source_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- NO ANN index initially. Use exact cosine search.
-- Benchmark with actual corpus before adding HNSW/IVFFlat.
```

---

## Configuration

```env
# LLM
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514
LLM_API_KEY=
LLM_ENABLED=true

# Embedding
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# RAG
RAG_ENABLED=true
VECTOR_TOP_K=5
VECTOR_MIN_SCORE=0.65
```

---

## Implementation Sequence

### Phase 3 — Foundation

1. Create `evaluation/schemas.py` — `CriterionEvaluation`, `CriterionSource`, `PolicyEvaluationResult`, `EvidenceMatrix`, `RetrievalStatus`, `RetrievalResult`
2. Add `service_date`, `clinical_notes` to `TriageRequest`; `criteria_evaluation`, `policy_path` to `TriageResponse`
3. Add all config settings (`LLM_*`, `RAG_*`, `EMBEDDING_*`, `VECTOR_*`)
4. Add `LLMServiceError` exception
5. Create `PolicyContentService` (normalize NCD/LCD/Article sections)
6. Add pgvector extension + `policy_embeddings` table (Alembic migration)
7. Implement `embedding_service.py` + `chunking_service.py` (normalization pipeline)
8. Create `scripts/ingest_embeddings.py` (reads existing DB → chunks → embeds → stores)
9. Implement `vector_policy_retriever.py` (threshold + metadata filter + `RetrievalStatus`)
10. **Run existing 25 tests → must all pass**

### Phase 4 — NCD Multi-Evaluator

11. Implement `criterion_classifier.py` (structured-metadata-first)
12. Implement `criteria_extractor.py` (priority order + provenance tracking)
13. Implement `structured_evaluator.py` (SQL/exact-match)
14. Implement `rule_evaluator.py` (duration, age, date, frequency)
15. Implement LLM client + all 4 prompt templates
16. Implement `semantic_evaluator.py` (graceful per-criterion degradation)
17. Implement `evidence_fusion.py` (criterion-type authority)
18. Integrate two-stage NCD retrieval + multi-evaluator into TriageService
19. **Run tests — existing + new NCD tests**

### Phase 5 — Jurisdiction (Verify)

20. Verify NCD NOT_ADDRESSED → jurisdiction → LCD works with new flow
21. Add integration tests for jurisdiction
22. **Run tests**

### Phase 6 — LCD Multi-Evaluator

23. LCD structured resolution (existing)
24. LCD criteria extraction via PolicyContentService (structured-first + provenance)
25. LCD multi-evaluator pipeline
26. LCD evidence fusion
27. Correct flow: LCD EXCLUDED → DENY, LCD UNKNOWN → PEND (Article NOT executed), LCD COVERED → Article
28. **Run tests**

### Phase 7 — Article + Decision Engine + Final

29. Article HCPCS/ICD-10 deterministic matching (existing, preserved)
30. Article documentation validation (existence=deterministic, meaning=LLM if needed)
31. Article authority rule: cannot override NCD/LCD coverage
32. Implement `decision_engine.py` (explicit precedence rules)
33. Extend TriageResponse with `criteria_evaluation` and `policy_path`
34. Full end-to-end integration tests
35. Retrieval quality validation tests
36. LLM disagreement tests
37. **Run complete test suite**

---

## Testing Strategy

### Regression
```bash
python -m pytest tests/ -v   # Before and after every phase
```

### New Test Categories

| Category | Key Tests |
|---|---|
| **Retrieval Quality** | Correct NCD retrieved; threshold respected; wrong version rejected; RETRIEVAL_NO_MATCH handled; RETRIEVAL_UNAVAILABLE handled |
| **Criterion Classifier** | Structured field → STRUCTURED; duration → RULE_BASED; narrative → SEMANTIC |
| **Structured Evaluator** | ICD-10 exact match; CPT match; covered/non-covered; exclusion |
| **Rule Evaluator** | Duration calc; age threshold; date range; missing evidence → UNKNOWN |
| **Semantic Evaluator** | LLM mocked; evidence grounded; insufficient → UNKNOWN |
| **Evidence Fusion** | Criterion-type authority; SQL overrides LLM for STRUCTURED; LLM authoritative for SEMANTIC |
| **Decision Engine** | LCD UNKNOWN → PEND; exclusion → DENY; Article cannot override NCD/LCD coverage |
| **Integration A** | NCD NOT_ADDRESSED → Jurisdiction → LCD COVERED → Article → APPROVE |
| **Integration B** | NCD NOT_ADDRESSED → Jurisdiction → LCD UNKNOWN → PEND (Article NOT executed) |
| **LLM Disagreement** | SQL NOT_SATISFIED overrides LLM SATISFIED for STRUCTURED criterion; LLM UNKNOWN on SEMANTIC → PEND |
| **LLM Degradation** | LLM down + all criteria deterministic → normal decision; LLM down + semantic needed → UNKNOWN → PEND |
| **Provenance** | Every criterion has source.policy_id, source.section, source.extraction_method populated |
| **Service Date** | Missing service_date → warning in response; provided date filters correct policy version |
| **NCD Decision Provenance** | Pre-parsed decision is hint, not override of multi-evaluator |

---

## Final Checklist

| Requirement | Status |
|---|---|
| NCD → Jurisdiction → LCD hierarchy | ✅ |
| LCD UNKNOWN → PEND (Article not executed) | ✅ |
| Article only after LCD/NCD COVERED | ✅ |
| Article cannot override NCD/LCD coverage | ✅ |
| RAG constrained by SQL candidates | ✅ |
| RAG threshold (VECTOR_MIN_SCORE) | ✅ |
| RAG failure vs no-match distinction | ✅ |
| Retrieval quality testing | ✅ |
| Structured-first criterion extraction | ✅ |
| Criterion provenance tracking | ✅ |
| SQL evaluator | ✅ |
| Rule evaluator | ✅ |
| LLM semantic evaluator | ✅ |
| LLM graceful per-criterion degradation | ✅ |
| Evidence fusion with criterion-type authority | ✅ |
| Deterministic Decision Engine with explicit precedence | ✅ |
| PolicyContentService (not repo methods) | ✅ |
| pgvector (configurable dimension, no premature ANN) | ✅ |
| Policy text normalization before embedding | ✅ |
| service_date (not silently defaulted) | ✅ |
| clinical_notes (optional) | ✅ |
| NCD.decision provenance check | ✅ |
| LLM disagreement tests | ✅ |
| Three-layer naming (Criterion → Policy → Decision) | ✅ |
| Existing tests preserved | ✅ |
| Mock mode continues working | ✅ |
