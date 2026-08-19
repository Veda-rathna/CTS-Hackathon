import axios from 'axios';

// Base URL — override via VITE_API_URL or VITE_API_BASE_URL env var
const rawBaseUrl = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';
export const API_BASE_URL = rawBaseUrl.replace(/\/+$/, '');

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  // 120s: agentic LLM pipeline (Qwen via LM Studio) can take up to 60s on CPU
  timeout: 120000,
});

// Normalize errors to human-readable messages
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg =
      err.response?.data?.detail ||
      err.response?.data?.message ||
      err.message ||
      'Unexpected error communicating with backend.';
    console.warn(`[API] ${err.config?.method?.toUpperCase()} ${err.config?.url}:`, msg);
    return Promise.reject(new Error(msg));
  }
);

/**
 * POST /api/v1/triage
 * Submit a TriageRequest and receive a TriageResponse.
 */
export async function runTriage(requestData) {
  const res = await apiClient.post('/triage', requestData);
  return res.data;
}

/**
 * POST /api/v1/pa-requests
 * Submit a full structured CanonicalPARequest (patient, coverage, provider,
 * service, diagnoses) and receive a TriageResponse.
 *
 * The backend owns normalization:
 *   - State full names -> 2-letter abbreviations
 *   - request_date auto-populated if absent
 *   - pa_request_id auto-generated if absent
 *   - All diagnoses ICD-10 codes extracted and passed to triage
 */
export async function createPARequest(payload) {
  const res = await apiClient.post('/pa-requests', payload);
  return res.data;
}

/**
 * POST /api/v1/extract  (multipart/form-data)
 * Upload a PA PDF document. Backend extracts triage fields.
 * Returns { procedure_code, diagnosis_codes, state, patient_age, clinical_notes, confidence, missing_fields }
 */
export async function extractFromPDF(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await apiClient.post('/extract', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  });
  return res.data;
}

/**
 * GET /api/v1/health
 */
export async function checkHealth() {
  try {
    const res = await apiClient.get('/health', { timeout: 5000 });
    return { online: true, data: res.data };
  } catch (e) {
    return { online: false, error: e.message };
  }
}

/**
 * GET /api/v1/health/db
 */
export async function checkDbHealth() {
  try {
    const res = await apiClient.get('/health/db', { timeout: 5000 });
    return { online: true, data: res.data };
  } catch (e) {
    return { online: false, error: e.message };
  }
}

/**
 * GET /api/v1/policies/search
 */
export async function searchPolicies(params) {
  const clean = Object.fromEntries(
    Object.entries(params).filter(([, v]) => v != null && v !== '')
  );
  const res = await apiClient.get('/policies/search', { params: clean });
  return res.data;
}

export async function getLcd(id) {
  const res = await apiClient.get(`/lcds/${encodeURIComponent(id)}`);
  return res.data;
}

export async function getNcd(id) {
  const res = await apiClient.get(`/ncds/${encodeURIComponent(id)}`);
  return res.data;
}

export async function getArticle(id) {
  const res = await apiClient.get(`/articles/${encodeURIComponent(id)}`);
  return res.data;
}

export async function getArticleCoveredIcd10(id) {
  const res = await apiClient.get(`/articles/${encodeURIComponent(id)}/icd10-covered`);
  return res.data;
}

export async function getArticleNonCoveredIcd10(id) {
  const res = await apiClient.get(`/articles/${encodeURIComponent(id)}/icd10-noncovered`);
  return res.data;
}

export async function getArticleHcpcs(id) {
  const res = await apiClient.get(`/articles/${encodeURIComponent(id)}/hcpcs`);
  return res.data;
}

/**
 * Normalize any form data into a clean TriageRequest object.
 *
 * Supports two shapes:
 * 1. New simple form: { procedure_code, diagnosis_codes[], state, patient_age, clinical_notes, service_date }
 * 2. Legacy nested shape: { pa_requests[0]: { patient, service, diagnoses, ... } }
 */
export function transformPAFormToTriageRequest(formData) {
  // New shape — already in TriageRequest format
  if (formData && formData.procedure_code !== undefined) {
    return {
      procedure_code: (formData.procedure_code || '').trim().toUpperCase(),
      diagnosis_codes: (formData.diagnosis_codes || [])
        .map((c) => (c || '').trim().toUpperCase())
        .filter(Boolean),
      state: formData.state || null,
      patient_age:
        formData.patient_age != null && formData.patient_age !== ''
          ? Number(formData.patient_age)
          : null,
      clinical_notes: formData.clinical_notes || null,
      service_date: formData.service_date || null,
    };
  }

  // Legacy nested shape fallback
  const pa = formData?.pa_requests?.[0] ?? formData ?? {};
  const procedureCode = pa.service?.procedure_code || '';
  const diagnosisCodes = (pa.diagnoses || [])
    .map((d) => d.icd10_code || d.source_code)
    .filter(Boolean);

  let state = pa.patient?.state || pa.provider?.state || '';
  if (state.length > 2) {
    const map = {
      massachusetts: 'MA', texas: 'TX', california: 'CA', florida: 'FL',
      illinois: 'IL', newyork: 'NY', ohio: 'OH', georgia: 'GA',
    };
    state = map[state.toLowerCase().replace(/\s+/g, '')] || state.slice(0, 2).toUpperCase();
  }

  return {
    procedure_code: procedureCode.toUpperCase(),
    diagnosis_codes: diagnosisCodes,
    state: state.toUpperCase() || null,
    patient_age: pa.patient?.age ? Number(pa.patient.age) : null,
    clinical_notes: pa.clinical_notes || pa.service?.service_description || null,
    service_date: pa.service?.start_date || null,
  };
}

export default {
  API_BASE_URL,
  runTriage,
  createPARequest,
  extractFromPDF,
  checkHealth,
  checkDbHealth,
  searchPolicies,
  getLcd,
  getNcd,
  getArticle,
  getArticleCoveredIcd10,
  getArticleNonCoveredIcd10,
  getArticleHcpcs,
  transformPAFormToTriageRequest,
};
