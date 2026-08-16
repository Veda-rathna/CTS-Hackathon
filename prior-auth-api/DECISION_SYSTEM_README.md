# CMS Prior Authorization API — Decision System & Evaluation Architecture

## 1. Executive Summary & Core Mission

The **Decision System** in the `prior-auth-api` project is an enterprise-grade, deterministic-first evaluation engine designed to process **Medicare Prior Authorization (PA)** requests. It evaluates submitted patient clinical requests against Centers for Medicare & Medicaid Services (CMS) coverage policies:
* **NCDs** (National Coverage Determinations) — Federal policies.
* **LCDs** (Local Coverage Determinations) — Regional Medicare Administrative Contractor (MAC) policies.
* **Articles** (Billing & Coding Articles) — Code mapping tables linking procedure and diagnosis codes to coverage rules.

The primary objective of the decision system is to deliver **deterministic, explainable, and audit-ready authorization decisions** (`APPROVE`, `PEND`, `REQUEST_MORE_INFORMATION`, `POLICY_EXPIRED`) while guaranteeing that artificial intelligence (LLM) never overrides deterministic medical code rules.

---

## 2. High-Level System Architecture

The decision engine follows a **layered, hierarchical pipeline architecture** structured into five clear stages:

```
                            ┌───────────────────────────┐
                            │    1. Triage Request      │
                            │ (HCPCS, ICD-10, Age, Notes)│
                            └─────────────┬─────────────┘
                                          │
                                          ▼
                            ┌───────────────────────────┐
                            │ 2. Input Normalization &  │
                            │   Policy Search (RAG/SQL) │
                            └─────────────┬─────────────┘
                                          │
                                          ▼
                            ┌───────────────────────────┐
                            │ 3. Criteria Extraction &  │
                            │      Classification       │
                            └─────────────┬─────────────┘
                                          │
                        ┌─────────────────┴─────────────────┐
                        ▼                                   ▼
            ┌──────────────────────┐             ┌──────────────────────┐
            │ StructuredEvaluator  │             │  SemanticEvaluator   │
            │ (Deterministic SQL)  │             │  (4-Agent Pipeline)  │
            │ Authoritative: TRUE  │             │ Authoritative: FALSE │
            └───────────┬──────────┘             └───────────┬──────────┘
                        │                                    │
                        └─────────────────┬──────────────────┘
                                          │
                                          ▼
                            ┌───────────────────────────┐
                            │  4. Evidence Fusion Layer │
                            │ (Authority Ladder Resolv.)│
                            └─────────────┬─────────────┘
                                          │
                                          ▼
                            ┌───────────────────────────┐
                            │   5. Decision Engine      │
                            │ (APPROVE / PEND / RMI)    │
                            └─────────────┬─────────────┘
```

---

## 3. Step-by-Step Breakdown of Evaluation Components

### Step 1: Input Normalization & Policy Filtering (`triage_service.py`)
* **Privacy Enforcement**: Accepts zero Patient Health Information (PHI) — no patient names, SSNs, or dates of birth.
* **Code Standardization**: Strips whitespace and normalizes HCPCS/CPT procedure codes, ICD-10 diagnosis codes, and US state abbreviations to uppercase.
* **Effective Date Filtering**: Validates that candidate policies are actively effective on the service date, discarding expired or future policies.

---

### Step 2: Policy Criteria Extraction & Classification

Before evaluation can take place, policy text is broken down into atomic **Criteria** (`PolicyCriterion`). Each criterion is assigned a classification by `CriterionClassifier`:

| Criterion Type | Classification Signal | Handling Mechanism | Example |
| :--- | :--- | :--- | :--- |
| **`STRUCTURED`** | Regex matches `HCPCS`, `CPT`, `ICD-10`, `code` | Evaluated against database code tables (SQL lookups) | *"Procedure must match HCPCS 64483"* |
| **`SEMANTIC`** | Narrative clinical requirement prose & numerical criteria | Evaluated via 4-agent LLM pipeline (Policy, Clinical, Reasoner, Critic) | *"Must document failure of 6 weeks of conservative therapy"* |

---

### Step 3: Strategy Pattern Evaluation (`multi_evaluator.py`)

The system uses the **Strategy Design Pattern** via `MultiEvaluator` to route each criterion to its dedicated evaluation engine:

#### 1. Structured Evaluator (`structured_evaluator.py`)
* **Engine**: Deterministic SQL queries against `NCDRepository`, `LCDRepository`, and `ArticleRepository`.
* **Logic**: Cross-references the submitted procedure code and diagnosis codes against covered/non-covered code lists stored in the database.
* **Authority**: **`authoritative = True`** (determines hard coverage boundaries and explicit exclusions).

#### 2. Semantic Evaluator & Agentic Pipeline (`semantic_evaluator.py` & `agent_orchestrator.py`)
* **Engine**: 4-Agent Sequential Pipeline powering Bedrock/local LLM evaluation (Qwen3).
* **Workflow**:
  1. **`PolicyAgent`**: Extracts exact required evidence points from policy prose.
  2. **`ClinicalEvidenceAgent`**: Searches clinical notes for matching patient observations.
  3. **`EvaluationAgent`**: Prepares a structured evaluation context comparing policy rules vs clinical notes.
  4. **`Qwen (LLM)`**: Evaluates criteria fulfillment (`SATISFIED`, `NOT_SATISFIED`, `UNKNOWN`).
  5. **`CriticAgent`**: Audits LLM output for logical errors or hallucinated claims. Rejects invalid outputs to `UNKNOWN`.
* **Authority**: **`authoritative = False`**. 
  > ⚠️ **Key Safety Principle**: AI outputs are never authoritative over deterministic medical code evidence.

---

### Step 4: Evidence Fusion & Authority Resolution (`evidence_fusion.py`)

`EvidenceFusion` merges all evaluated criteria (`EvaluatedCriterion`) for a policy and determines the policy-level evaluation status: `COVERED`, `EXCLUDED`, `UNKNOWN`, or `NOT_ADDRESSED`.

#### The Authority Ladder Rules:
1. **Deterministic Exclusion Wins**: If any mandatory *authoritative* criterion is `NOT_SATISFIED`, the policy outcome is immediately **`EXCLUDED`**.
2. **Deterministic Missing Data Blocks Approval**: If a mandatory *authoritative* criterion is `UNKNOWN` (e.g., missing patient age), the status is **`UNKNOWN`** (blocks approval).
3. **AI Non-Authoritative Abstention**: If at least one *authoritative* criterion is `SATISFIED`, any non-authoritative (LLM) mandatory `UNKNOWN` criterion **abstains** and does *not* block a `COVERED` decision.
4. **Coverage Confirmation**: When mandatory criteria are satisfied with no authoritative exclusions, the status is **`COVERED`**.

---

### Step 5: Final Decision Engine (`decision_engine.py`)

`DecisionEngine` takes the policy statuses from National (NCD), Regional (LCD), and Article levels along with any missing request fields, and produces the final user-facing decision:

```
                            Decision Matrix
┌──────────────────────────────────────┬─────────────────────────────┐
│ Condition                            │ Final Triage Decision       │
├──────────────────────────────────────┼─────────────────────────────┤
│ Required input fields are missing    │ REQUEST_MORE_INFORMATION    │
├──────────────────────────────────────┼─────────────────────────────┤
│ NCD, LCD, or Article is EXCLUDED     │ PEND (Manual Review)        │
├──────────────────────────────────────┼─────────────────────────────┤
│ Ambiguous evidence (UNKNOWN status)  │ PEND (Manual Review)        │
├──────────────────────────────────────┼─────────────────────────────┤
│ No policy found (NOT_ADDRESSED)      │ PEND (Manual Review)        │
├──────────────────────────────────────┼─────────────────────────────┤
│ Policy criteria satisfied (COVERED)  │ APPROVE                     │
└──────────────────────────────────────┴─────────────────────────────┘
```

---

## 4. Key Design Principles & Guardrails

1. **Deterministic First**: SQL code lookups and mathematical rules always take precedence over LLM text analysis.
2. **Explainability**: Every evaluated criterion returns structured `patient_evidence`, `policy_evidence`, and a clear, synthesized human-readable `explanation`.
3. **Fail-Safe Safety**: Any error or exception in the agentic LLM pipeline degrades gracefully to `UNKNOWN` and `PEND` — it never crashes the system or causes an erroneous approval.
4. **Strict Hierarchy**: Federal NCD rules supersede regional LCD rules, which supersede local Articles.

---

## 5. Summary Matrix of Evaluation Outcomes

| Outcome | Explanation | Action Required |
| :--- | :--- | :--- |
| **`APPROVE`** | All required policy criteria satisfied deterministically or via validated clinical evidence. | Immediate authorization granted. |
| **`PEND`** | Exclusion found, ambiguous clinical evidence, or policy gap identified. | Escalated to clinical staff for manual review. |
| **`REQUEST_MORE_INFORMATION`** | Critical data elements (e.g. procedure code, state) missing from request payload. | Resubmit request with complete data. |
| **`POLICY_EXPIRED`** | All matching policies have passed their expiration date. | Review policy version history. |
