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
    return JSON.parse(raw);
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
  const paId = paData.pa_request_id || `PA-${Date.now().toString().slice(-4)}`;
  
  // Format into standard stored PA record
  const newRecord = {
    ...paData,
    pa_request_id: paId,
    status: evaluationResult ? 'COMPLETED' : 'PENDING',
    decision: evaluationResult ? evaluationResult.decision : 'PENDING_REVIEW',
    evidence_score: evaluationResult?.evidence_score ?? 0.8,
    requires_prior_authorization: evaluationResult?.requires_prior_authorization ?? true,
    reason: evaluationResult?.reason || 'Evaluation completed successfully.',
    decision_basis: evaluationResult?.decision_basis || '',
    policies: evaluationResult?.policies || [],
    evidence: evaluationResult?.evidence || [],
    criteria: evaluationResult?.criteria || [],
    missing_information: evaluationResult?.missing_information || [],
    warnings: evaluationResult?.warnings || [],
    created_at: new Date().toISOString(),
  };

  // Upsert into requests list
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
