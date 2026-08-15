import axios from 'axios';

// Get base URL from environment or default to local FastAPI server
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Response interceptor for clear error messaging
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorMsg =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred while communicating with the backend.';
    console.warn(`[API Client Error] ${error.config?.url}:`, errorMsg);
    return Promise.reject(new Error(errorMsg));
  }
);

/**
 * Prior Authorization Triage API
 */
export async function runTriage(requestData) {
  const response = await apiClient.post('/triage', requestData);
  return response.data;
}

/**
 * Policies Search API
 */
export async function searchPolicies(params) {
  const cleanParams = Object.fromEntries(
    Object.entries(params).filter(([_, v]) => v !== null && v !== undefined && v !== '')
  );
  const response = await apiClient.get('/policies/search', { params: cleanParams });
  return response.data;
}

/**
 * LCD Details API
 */
export async function getLcd(lcdId) {
  const response = await apiClient.get(`/lcds/${encodeURIComponent(lcdId)}`);
  return response.data;
}

/**
 * NCD Details API
 */
export async function getNcd(ncdId) {
  const response = await apiClient.get(`/ncds/${encodeURIComponent(ncdId)}`);
  return response.data;
}

/**
 * Article Details API
 */
export async function getArticle(articleId) {
  const response = await apiClient.get(`/articles/${encodeURIComponent(articleId)}`);
  return response.data;
}

export async function getArticleCoveredIcd10(articleId) {
  const response = await apiClient.get(`/articles/${encodeURIComponent(articleId)}/icd10-covered`);
  return response.data;
}

export async function getArticleNonCoveredIcd10(articleId) {
  const response = await apiClient.get(`/articles/${encodeURIComponent(articleId)}/icd10-noncovered`);
  return response.data;
}

export async function getArticleHcpcs(articleId) {
  const response = await apiClient.get(`/articles/${encodeURIComponent(articleId)}/hcpcs`);
  return response.data;
}

/**
 * Health Check API
 */
export async function checkHealth() {
  try {
    const response = await apiClient.get('/health', { timeout: 3000 });
    return { online: true, data: response.data };
  } catch (error) {
    return { online: false, error: error.message };
  }
}

export async function checkDbHealth() {
  try {
    const response = await apiClient.get('/health/db', { timeout: 3000 });
    return { online: true, data: response.data };
  } catch (error) {
    return { online: false, error: error.message };
  }
}

/**
 * Helper to convert complex nested PA form data into the backend TriageRequest schema
 */
export function transformPAFormToTriageRequest(paData) {
  const pa = paData.pa_requests ? paData.pa_requests[0] : paData;
  
  // Extract procedure code from service
  const procedureCode = pa.service?.procedure_code || '64483';

  // Extract diagnosis codes
  const diagnosisCodes = (pa.diagnoses || [])
    .map((d) => d.icd10_code || d.source_code)
    .filter(Boolean);

  if (diagnosisCodes.length === 0) {
    diagnosisCodes.push('M54.16');
  }

  // Extract state
  let state = pa.patient?.state || pa.provider?.state || 'TX';
  if (state.length > 2) {
    const stateMap = {
      massachusetts: 'MA',
      texas: 'TX',
      california: 'CA',
      illinois: 'IL',
      newyork: 'NY',
      florida: 'FL',
    };
    const cleanState = state.toLowerCase().replace(/\s+/g, '');
    state = stateMap[cleanState] || 'TX';
  }

  return {
    procedure_code: procedureCode,
    diagnosis_codes: diagnosisCodes,
    state: state.toUpperCase().slice(0, 2),
    patient_age: pa.patient?.age ? Number(pa.patient.age) : 45,
    clinical_notes: pa.service?.service_description || 'Standard Prior Authorization submission.',
    service_date: pa.service?.start_date || new Date().toISOString().split('T')[0],
  };
}

export default {
  runTriage,
  searchPolicies,
  getLcd,
  getNcd,
  getArticle,
  getArticleCoveredIcd10,
  getArticleNonCoveredIcd10,
  getArticleHcpcs,
  checkHealth,
  checkDbHealth,
  transformPAFormToTriageRequest,
};
