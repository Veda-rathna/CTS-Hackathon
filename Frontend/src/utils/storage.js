import { INITIAL_PA_REQUESTS } from './mockData';

const PA_STORAGE_KEY = 'pa_intelligence_requests_v1';
const DRAFT_STORAGE_KEY = 'pa_intelligence_form_draft_v1';

export function getStoredPARequests() {
  try {
    const raw = localStorage.getItem(PA_STORAGE_KEY);
    if (!raw) {
      // Seed with initial realistic cases
      localStorage.setItem(PA_STORAGE_KEY, JSON.stringify(INITIAL_PA_REQUESTS));
      return INITIAL_PA_REQUESTS;
    }
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      // Check if newly introduced initial requests (e.g. PA-005 rejected) are in storage; if not, merge them
      const existingIds = new Set(parsed.map(r => r.pa_request_id?.toUpperCase()));
      let hasNew = false;
      INITIAL_PA_REQUESTS.forEach(initReq => {
        if (!existingIds.has(initReq.pa_request_id?.toUpperCase())) {
          parsed.push(initReq);
          hasNew = true;
        }
      });
      if (hasNew) {
        localStorage.setItem(PA_STORAGE_KEY, JSON.stringify(parsed));
      }
      return parsed;
    }
    return INITIAL_PA_REQUESTS;
  } catch (err) {
    console.error('Error reading PA requests from storage:', err);
    return INITIAL_PA_REQUESTS;
  }
}

export function getPARequestById(id) {
  const requests = getStoredPARequests();
  return requests.find((r) => r.pa_request_id.toLowerCase() === id.toLowerCase());
}

export function savePARequest(paData, evaluationResult = null) {
  const requests = getStoredPARequests();
  const paId = paData.pa_request_id || `PA-${Date.now().toString().slice(-6)}`;

  const newRecord = {
    // The request-side display fields
    ...paData,
    pa_request_id: paId,
    status: evaluationResult ? 'COMPLETED' : 'PENDING',

    // Core TriageResponse fields
    decision: evaluationResult?.decision ?? 'PENDING_REVIEW',
    evidence_score: evaluationResult?.evidence_score ?? null,
    requires_prior_authorization: evaluationResult?.requires_prior_authorization ?? null,
    reason: evaluationResult?.reason ?? '',
    reason_codes: evaluationResult?.reason_codes ?? [],
    decision_basis: evaluationResult?.decision_basis ?? '',
    evidence_fusion_result: evaluationResult?.evidence_fusion_result ?? null,

    // Policy & code matching
    policies: evaluationResult?.policies ?? [],
    policy_path: evaluationResult?.policy_path ?? null,
    matched_codes: evaluationResult?.matched_codes ?? null,
    diagnosis_evaluation: evaluationResult?.diagnosis_evaluation ?? [],

    // Evidence items
    evidence: evaluationResult?.evidence ?? [],
    rag_evidence: evaluationResult?.rag_evidence ?? [],

    // Criteria (structured + semantic evaluation results)
    criteria: evaluationResult?.criteria ?? [],

    // Additional info
    missing_information: evaluationResult?.missing_information ?? [],
    warnings: evaluationResult?.warnings ?? [],

    created_at: new Date().toISOString(),
  };

  const existingIdx = requests.findIndex((r) => r.pa_request_id === paId);
  let updated;
  if (existingIdx >= 0) {
    updated = [...requests];
    updated[existingIdx] = { ...updated[existingIdx], ...newRecord };
  } else {
    updated = [newRecord, ...requests];
  }

  try {
    localStorage.setItem(PA_STORAGE_KEY, JSON.stringify(updated));
  } catch (err) {
    console.error('Error saving PA request to localStorage:', err);
  }

  return newRecord;
}

export function saveFormDraft(formData) {
  try {
    localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(formData));
  } catch (err) {
    console.error('Error saving form draft:', err);
  }
}

export function getFormDraft() {
  try {
    const raw = localStorage.getItem(DRAFT_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (err) {
    console.error('Error loading form draft:', err);
    return null;
  }
}

export function clearFormDraft() {
  try {
    localStorage.removeItem(DRAFT_STORAGE_KEY);
  } catch (err) {
    console.error('Error clearing draft:', err);
  }
}
