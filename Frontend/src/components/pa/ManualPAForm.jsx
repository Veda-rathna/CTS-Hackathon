import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  RotateCcw, Plus, X, RefreshCw, AlertCircle, ShieldCheck, User, Stethoscope, Building2, ChevronRight, ChevronLeft
} from 'lucide-react';
import { createPARequest } from '../../services/api';
import { savePARequest } from '../../utils/storage';

const US_STATES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA',
  'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT',
  'VA', 'WA', 'WV', 'WI', 'WY',
];

const REALISTIC_SCENARIOS = [
  {
    id: 'PA-OPT-001',
    label: 'PA-OPT-001',
    badgeLabel: '⚡ OPTIMIZED',
    name: 'Knee Viscosupplementation',
    subtitle: '0ms Cache • 89% Token Cut',
    expected: 'APPROVE',
    expectedBadge: 'bg-emerald-100 text-emerald-800 border-emerald-300 font-extrabold',
    description: 'High-volume repeat policy (CPT 20610 / M17.11) demonstrating 0ms Policy Cache hit, sub-second latency, and maximum token efficiency.',
    data: {
      pa_request_id: 'PA-OPT-001',
      patient: { patient_id: '1f2982d5-e5da-6d4a-38d7-d7e7323880bb', date_of_birth: '1958-04-12', age: 68, gender: 'F', state: 'TX' },
      coverage: { payer: 'Medicare', plan_id: 'MED-TX-001', plan_name: 'Medicare Traditional' },
      request: { review_type: 'NON_URGENT', request_type: 'INITIAL', urgency_reason: '', previous_authorization_number: '' },
      provider: { provider_id: 'PRV-ORTHO-01', specialty: 'Orthopedic Surgery', organization_id: 'ORG-TX-01', organization_name: 'Austin Orthopedic Institute', state: 'TX' },
      service: {
        service_description: 'Intraarticular Knee Injections of Hyaluronan (Viscosupplementation)',
        procedure_code: '20610',
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
        place_of_service: 'Outpatient Clinic',
        number_of_sessions: 1, duration: '1 day', frequency: 'Once',
      },
      diagnoses: [{ description: 'Unilateral primary osteoarthritis, right knee', icd10_code: 'M17.11' }],
      clinical_notes: 'Patient is a 68-year-old female presenting with persistent pain and functional limitation of the right knee due to primary osteoarthritis (M17.11). Symptoms have persisted for >6 months. Patient has completed a 12-week trial of structured physical therapy, daily acetaminophen, and oral NSAIDs (meloxicam) with inadequate relief. Plain radiographs demonstrate Grade 3 joint space narrowing and subchondral sclerosis without joint infection. Requesting intra-articular hyaluronan injection (20610).',
    },
  },
  {
    id: 'PA-REAL-001',
    label: 'PA-REAL-001',
    badgeLabel: 'APPROVE',
    name: 'Lumbar Epidural Steroid',
    subtitle: '10-Wk PT & MRI Met',
    expected: 'APPROVE',
    expectedBadge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    description: 'Covered lumbar radiculopathy (CPT 64483, ICD-10 M54.16) with 10-week conservative trial & MRI confirmation satisfying LCD L39054.',
    data: {
      pa_request_id: 'PA-REAL-001',
      patient: { patient_id: 'a1733070-046a-4506-bba6-47f32652e9d7', date_of_birth: '1962-09-18', age: 64, gender: 'F', state: 'TX' },
      coverage: { payer: 'Medicare', plan_id: 'MED-TX-001', plan_name: 'Medicare Traditional' },
      request: { review_type: 'NON_URGENT', request_type: 'INITIAL', urgency_reason: '', previous_authorization_number: '' },
      provider: { provider_id: 'PRV-PAIN-02', specialty: 'Interventional Pain Management', organization_id: 'ORG-TX-02', organization_name: 'Texas Spine & Pain Specialists', state: 'TX' },
      service: {
        service_description: 'Injection(s), anesthetic agent and/or steroid, transforaminal epidural; lumbar or sacral, single level',
        procedure_code: '64483',
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
        place_of_service: 'Ambulatory Surgery Center',
        number_of_sessions: 1, duration: '1 day', frequency: 'Once',
      },
      diagnoses: [{ description: 'Radiculopathy, lumbar region', icd10_code: 'M54.16' }],
      clinical_notes: 'Patient is a 64-year-old female with severe right-sided L5 lumbar radiculopathy (M54.16) lasting >14 weeks. Physical examination demonstrates positive straight-leg raise at 40 degrees, diminished sensation in L5 dermatome, and 4/5 weakness in extensor hallucis longus. Lumbar MRI confirms L4-L5 disc herniation with nerve root impingement. Patient has failed a 10-week conservative therapy regimen comprising formal physical therapy, gabapentin, and oral prednisone. Requesting lumbar transforaminal epidural steroid injection (64483).',
    },
  },
  {
    id: 'PA-REAL-002',
    label: 'PA-REAL-002',
    badgeLabel: 'PEND',
    name: 'Trigger Point - Joint Pain',
    subtitle: 'Atypical Presentation',
    expected: 'PEND',
    expectedBadge: 'bg-purple-50 text-purple-700 border-purple-200',
    description: 'Non-covered acute joint pain without trigger points (CPT 20552, ICD-10 M25.50). Pended for Nurse/UM clinical review.',
    data: {
      pa_request_id: 'PA-REAL-002',
      patient: { patient_id: 'ba234ff2-cefe-dfee-935a-8ea2378da8c2', date_of_birth: '1965-02-14', age: 61, gender: 'M', state: 'TX' },
      coverage: { payer: 'Medicare', plan_id: 'MED-TX-001', plan_name: 'Medicare Traditional' },
      request: { review_type: 'NON_URGENT', request_type: 'INITIAL', urgency_reason: '', previous_authorization_number: '' },
      provider: { provider_id: 'PRV-PAIN-03', specialty: 'Pain Medicine', organization_id: 'ORG-TX-03', organization_name: 'Dallas Pain Institute', state: 'TX' },
      service: {
        service_description: 'Injection(s), single or multiple trigger point(s), 1 or 2 muscle(s)',
        procedure_code: '20552',
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
        place_of_service: 'Outpatient Clinic',
        number_of_sessions: 1, duration: '1 day', frequency: 'Once',
      },
      diagnoses: [{ description: 'Pain in unspecified joint', icd10_code: 'M25.50' }],
      clinical_notes: 'Patient is a 61-year-old male presenting with acute, non-localized joint pain (M25.50) without documented myofascial trigger points or taut bands. Symptoms began 5 days ago. Patient has not undergone conservative physical therapy or trial of pharmacologic analgesics. Requesting trigger point injection (20552) for acute joint pain relief.',
    },
  },
  {
    id: 'PA-REAL-003',
    label: 'PA-REAL-003',
    badgeLabel: 'NEED INFO',
    name: 'Epidural - Missing Spine Docs',
    subtitle: 'Lacks MRI & Spine Exam',
    expected: 'NEED_MORE_INFORMATION',
    expectedBadge: 'bg-amber-50 text-amber-800 border-amber-200',
    description: 'Unlisted headache diagnosis (R51.9) lacking spinal physical exam and MRI. Generates actionable provider request checklist.',
    data: {
      pa_request_id: 'PA-REAL-003',
      patient: { patient_id: 'd20a36fc-23ba-8462-bf39-864000fbf25f', date_of_birth: '1959-11-03', age: 67, gender: 'M', state: 'TX' },
      coverage: { payer: 'Medicare', plan_id: 'MED-TX-001', plan_name: 'Medicare Traditional' },
      request: { review_type: 'NON_URGENT', request_type: 'INITIAL', urgency_reason: '', previous_authorization_number: '' },
      provider: { provider_id: 'PRV-NEURO-04', specialty: 'Neurology', organization_id: 'ORG-TX-04', organization_name: 'Houston Neurological Clinic', state: 'TX' },
      service: {
        service_description: 'Epidural injection, lumbar or sacral',
        procedure_code: '64483',
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
        place_of_service: 'Outpatient Hospital',
        number_of_sessions: 1, duration: '1 day', frequency: 'Once',
      },
      diagnoses: [{ description: 'Headache, unspecified', icd10_code: 'R51.9' }],
      clinical_notes: 'Patient is a 67-year-old male presenting with diffuse headache symptoms (R51.9). Provider requested lumbar transforaminal epidural injection (64483). The submitted medical record contains no spinal physical examination, no documentation of lumbar radicular symptoms or conservative spinal therapy, and no spine imaging reports.',
    },
  },
  {
    id: 'PA-REAL-004',
    label: 'PA-REAL-004',
    badgeLabel: 'REJECT',
    name: 'Dry Needling - NCD Exclusion',
    subtitle: 'NCD 373 Policy Exclusion',
    expected: 'REJECTED',
    expectedBadge: 'bg-rose-50 text-rose-700 border-rose-200',
    description: 'Explicit Medicare policy exclusion under NCD 373 for non-indicated acupuncture/dry needling trigger points.',
    data: {
      pa_request_id: 'PA-REAL-004',
      patient: { patient_id: '80c747ab-dc05-2bca-dafa-e2aa58619442', date_of_birth: '1969-07-29', age: 57, gender: 'M', state: 'TX' },
      coverage: { payer: 'Medicare', plan_id: 'MED-TX-001', plan_name: 'Medicare Traditional' },
      request: { review_type: 'NON_URGENT', request_type: 'INITIAL', urgency_reason: '', previous_authorization_number: '' },
      provider: { provider_id: 'PRV-PAIN-05', specialty: 'Physical Medicine & Rehabilitation', organization_id: 'ORG-TX-05', organization_name: 'San Antonio PM&R Associates', state: 'TX' },
      service: {
        service_description: 'Trigger point injection for acupuncture-related indications',
        procedure_code: '20552',
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
        place_of_service: 'Outpatient Clinic',
        number_of_sessions: 1, duration: '1 day', frequency: 'Once',
      },
      diagnoses: [{ description: 'Pain in unspecified joint', icd10_code: 'M25.50' }],
      clinical_notes: 'Patient is a 57-year-old male with chronic non-specific low back pain since 2014 requesting trigger point injections for generalized joint discomfort (M25.50). The requested service falls under acupuncture-related dry needling/trigger point exclusions under NCD 373 for non-indicated axial spine symptoms.',
    },
  },
  {
    id: 'PA-REAL-005',
    label: 'PA-REAL-005',
    badgeLabel: 'JURISDICTION',
    name: 'Knee - Out of Jurisdiction',
    subtitle: 'State Boundary Check (NY)',
    expected: 'NEED_MORE_INFORMATION',
    expectedBadge: 'bg-slate-100 text-slate-700 border-slate-300',
    description: 'Patient state outside regional Medicare Administrative Contractor (MAC) Novitas Jurisdiction J5.',
    data: {
      pa_request_id: 'PA-REAL-005',
      patient: { patient_id: '8a2af5b4-6f29-27d4-b5fd-bb687fa2169b', date_of_birth: '1956-01-25', age: 70, gender: 'M', state: 'NY' },
      coverage: { payer: 'Medicare', plan_id: 'MED-NY-001', plan_name: 'Medicare Traditional' },
      request: { review_type: 'NON_URGENT', request_type: 'INITIAL', urgency_reason: '', previous_authorization_number: '' },
      provider: { provider_id: 'PRV-MED-06', specialty: 'Internal Medicine', organization_id: 'ORG-NY-06', organization_name: 'New York Specialty Health', state: 'NY' },
      service: {
        service_description: 'Intra-articular knee viscosupplementation',
        procedure_code: '20610',
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
        place_of_service: 'Outpatient Clinic',
        number_of_sessions: 1, duration: '1 day', frequency: 'Once',
      },
      diagnoses: [{ description: 'Unilateral primary osteoarthritis, right knee', icd10_code: 'M17.11' }],
      clinical_notes: 'Patient is a 70-year-old male residing in New York requesting knee viscosupplementation (20610) for primary osteoarthritis (M17.11). Patient has failed 8 weeks of NSAIDs.',
    },
  },
];

const DEFAULT_FORM = {
  pa_request_id: '',
  patient: { patient_id: '', date_of_birth: '', age: '', gender: '', state: '' },
  coverage: { payer: '', plan_id: '', plan_name: '' },
  request: { review_type: 'NON_URGENT', request_type: 'INITIAL', urgency_reason: '', previous_authorization_number: '' },
  provider: { provider_id: '', specialty: '', organization_id: '', organization_name: '', state: '' },
  service: {
    service_description: '', procedure_code: '',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    place_of_service: '', number_of_sessions: '', duration: '', frequency: '',
  },
  diagnoses: [{ description: '', icd10_code: '' }],
  clinical_notes: '',
};

function validate(form) {
  const errors = {};
  const proc = (form.service?.procedure_code || '').trim();
  if (!proc) errors['service.procedure_code'] = 'Procedure code is required';
  
  const validDx = (form.diagnoses || []).filter((d) => d.icd10_code && d.icd10_code.trim());
  if (validDx.length === 0) errors['diagnoses'] = 'At least one ICD-10 diagnosis code is required';
  
  const age = form.patient?.age;
  if (age !== '' && age !== null && age !== undefined) {
    const n = Number(age);
    if (isNaN(n) || n < 0 || n > 130) errors['patient.age'] = 'Invalid age';
  }
  return errors;
}

export default function ManualPAForm() {
  const navigate = useNavigate();
  const [form, setForm] = useState(DEFAULT_FORM);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [activeTab, setActiveTab] = useState(1);
  const [selectedScenarioId, setSelectedScenarioId] = useState('');

  const setFlat = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) setErrors((prev) => { const n = { ...prev }; delete n[field]; return n; });
  };
  const setNested = (section, field, value) => {
    setForm((prev) => ({ ...prev, [section]: { ...prev[section], [field]: value } }));
    const key = `${section}.${field}`;
    if (errors[key]) setErrors((prev) => { const n = { ...prev }; delete n[key]; return n; });
  };
  const setDiagnosis = (idx, field, value) => {
    const next = [...form.diagnoses];
    next[idx] = { ...next[idx], [field]: field === 'icd10_code' ? value.toUpperCase() : value };
    setFlat('diagnoses', next);
    if (errors['diagnoses']) setErrors((prev) => { const n = { ...prev }; delete n['diagnoses']; return n; });
  };
  const addDiagnosis = () => setFlat('diagnoses', [...form.diagnoses, { description: '', icd10_code: '' }]);
  const removeDiagnosis = (idx) => {
    if (form.diagnoses.length === 1) return;
    setFlat('diagnoses', form.diagnoses.filter((_, i) => i !== idx));
  };
  const loadScenario = (scenario) => {
    setForm({ ...scenario.data });
    setSelectedScenarioId(scenario.id);
    setErrors({});
    setSubmitError(null);
    setActiveTab(2); // Jump to clinical data tab to show populated codes & notes
  };
  const reset = () => {
    setForm(DEFAULT_FORM);
    setSelectedScenarioId('');
    setErrors({});
    setSubmitError(null);
    setActiveTab(1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitError(null);
    const validationErrors = validate(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      if (validationErrors['patient.age']) setActiveTab(1);
      else if (validationErrors['service.procedure_code'] || validationErrors['diagnoses']) setActiveTab(2);
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        pa_request_id: form.pa_request_id?.trim() || undefined,
        patient: {
          patient_id: form.patient.patient_id?.trim() || undefined,
          date_of_birth: form.patient.date_of_birth || undefined,
          age: form.patient.age !== '' ? Number(form.patient.age) : undefined,
          gender: form.patient.gender || undefined,
          state: form.patient.state || undefined,
        },
        coverage: {
          payer: form.coverage.payer?.trim() || undefined,
          plan_id: form.coverage.plan_id?.trim() || undefined,
          plan_name: form.coverage.plan_name?.trim() || undefined,
        },
        request: {
          request_date: null,
          review_type: form.request.review_type,
          request_type: form.request.request_type,
          urgency_reason: form.request.urgency_reason?.trim() || undefined,
          previous_authorization_number: form.request.previous_authorization_number?.trim() || undefined,
        },
        provider: {
          provider_id: form.provider.provider_id?.trim() || undefined,
          specialty: form.provider.specialty?.trim() || undefined,
          organization_id: form.provider.organization_id?.trim() || undefined,
          organization_name: form.provider.organization_name?.trim() || undefined,
          state: form.provider.state || undefined,
        },
        service: {
          service_description: form.service.service_description?.trim() || '',
          procedure_code: form.service.procedure_code?.trim().toUpperCase() || undefined,
          start_date: form.service.start_date || undefined,
          end_date: form.service.end_date || undefined,
          place_of_service: form.service.place_of_service?.trim() || undefined,
          number_of_sessions: form.service.number_of_sessions !== '' ? Number(form.service.number_of_sessions) : undefined,
          duration: form.service.duration?.trim() || undefined,
          frequency: form.service.frequency?.trim() || undefined,
        },
        diagnoses: form.diagnoses
          .filter((d) => d.icd10_code?.trim())
          .map((d) => ({ description: d.description?.trim() || '', icd10_code: d.icd10_code.trim().toUpperCase() })),
        clinical_notes: form.clinical_notes?.trim() || undefined,
      };

      const response = await createPARequest(payload);
      const paId = payload.pa_request_id || `PA-${Date.now().toString().slice(-6)}`;
      const displayRecord = {
        pa_request_id: paId,
        procedure_code: payload.service?.procedure_code,
        diagnosis_codes: payload.diagnoses.map((d) => d.icd10_code),
        state: payload.patient?.state,
        patient_age: payload.patient?.age,
        clinical_notes: form.clinical_notes?.trim() || payload.service?.service_description || null,
        service_date: payload.service?.start_date,
        created_at: new Date().toISOString(),
      };
      const saved = savePARequest(displayRecord, response);
      navigate(`/pa/${saved.pa_request_id}`);
    } catch (err) {
      setSubmitError(err.message || 'Error submitting request.');
    } finally {
      setSubmitting(false);
    }
  };

  const inputCls = (hasErr) =>
    `w-full px-3 py-2 text-xs rounded-lg border ${hasErr ? 'border-rose-400 bg-rose-50 text-rose-900' : 'border-slate-200 bg-white hover:border-slate-300 focus:bg-white focus:border-sky-600'} focus:outline-none focus:ring-2 focus:ring-sky-500/20 transition-all`;
  
  const lblCls = "block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1";

  return (
    <div className="relative healthcare-card overflow-hidden bg-white">
      
      {/* EVALUATION LOADING OVERLAY */}
      {submitting && (
        <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex flex-col items-center justify-center p-6 text-white text-center">
          <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 shadow-xl max-w-sm w-full space-y-4">
            <div className="w-10 h-10 mx-auto rounded-full bg-sky-900/60 border border-sky-600 flex items-center justify-center text-sky-400">
              <RefreshCw className="w-5 h-5 animate-spin" />
            </div>
            <div className="space-y-1">
              <h4 className="text-sm font-bold text-white">Evaluating Prior Authorization</h4>
              <p className="text-xs text-slate-400">
                Evaluating clinical evidence against CMS Medicare policies...
              </p>
            </div>
            <div className="space-y-1.5 pt-2 text-left text-[11px] text-slate-400 border-t border-slate-800">
              <div className="flex items-center gap-2 text-sky-300">
                <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-ping" />
                <span>1. Matching CMS NCD/LCD & Article rules</span>
              </div>
              <div className="flex items-center gap-2 text-slate-400">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-600" />
                <span>2. Evaluating patient clinical documentation</span>
              </div>
              <div className="flex items-center gap-2 text-slate-400">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-600" />
                <span>3. Adjudicating final coverage determination</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* HEADER / DEMO SCENARIO SELECTOR */}
      <div className="p-4 border-b border-slate-200/90 bg-slate-50/50 space-y-2.5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-sky-700" />
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Prior Authorization Intake Form
            </h3>
          </div>
          <button
            type="button"
            onClick={reset}
            className="self-end sm:self-auto inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-slate-600 hover:text-rose-700 hover:bg-rose-50 rounded-md border border-slate-200 transition-colors"
            title="Clear and reset form"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Clear Form</span>
          </button>
        </div>

        {/* Demo Scenarios Quick-Picker */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
              Demo Scenarios (Select to auto-populate test payload):
            </span>
            <span className="hidden sm:inline text-[10px] font-semibold text-slate-400">
              Covers 4 Core Determinations + Live Optimization
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
            {REALISTIC_SCENARIOS.map((s) => {
              const isSelected = selectedScenarioId === s.id;
              return (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => loadScenario(s)}
                  className={`p-2.5 text-left rounded-xl border transition-all text-xs flex flex-col justify-between gap-1 ${
                    isSelected
                      ? 'bg-sky-50 border-sky-500 ring-2 ring-sky-500/20 text-sky-950 font-bold shadow-2xs'
                      : 'bg-white hover:bg-slate-50 border-slate-200 text-slate-700 font-medium hover:border-slate-300'
                  }`}
                  title={`${s.name} - ${s.description}`}
                >
                  <div className="flex items-center justify-between gap-1">
                    <span className="font-mono text-[10px] font-extrabold text-slate-900">{s.label}</span>
                    <span className={`text-[9px] font-extrabold px-1.5 py-0.5 rounded-md border whitespace-nowrap ${s.expectedBadge}`}>
                      {s.badgeLabel || (s.expected === 'NEED_MORE_INFORMATION' ? 'NEED INFO' : s.expected)}
                    </span>
                  </div>
                  <span className="text-[11px] font-bold leading-snug line-clamp-1 text-slate-800">
                    {s.name}
                  </span>
                  <span className="text-[10px] text-slate-400 font-medium line-clamp-1">
                    {s.subtitle || s.description}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {submitError && (
        <div className="mx-4 mt-3 p-3 rounded-lg bg-rose-50 border border-rose-200 flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span className="text-xs font-semibold text-rose-800">{submitError}</span>
        </div>
      )}

      {/* TABS NAVIGATION */}
      <div className="flex px-4 pt-2.5 gap-1.5 border-b border-slate-200 bg-slate-50/30">
        {[
          { id: 1, label: 'Patient Information', icon: User },
          { id: 2, label: 'Clinical & Service Details', icon: Stethoscope },
          { id: 3, label: 'Provider & Organization', icon: Building2 },
        ].map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 py-2 px-3.5 rounded-t-lg text-xs font-bold border-t border-x transition-all ${
                isActive 
                  ? 'bg-white border-slate-200 text-sky-800 border-b-white' 
                  : 'bg-transparent border-transparent text-slate-500 hover:text-slate-800'
              }`}
              style={isActive ? { marginBottom: '-1px' } : {}}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* MAIN CONTENT AREA */}
      <div className="p-4 sm:p-6 bg-white">
        <form onSubmit={handleSubmit} noValidate>
          {/* TAB 1: PATIENT */}
          {activeTab === 1 && (
            <div className="max-w-2xl mx-auto space-y-4">
              <div className="space-y-0.5 pb-2 border-b border-slate-100">
                <h4 className="text-sm font-bold text-slate-800">Patient Demographics</h4>
                <p className="text-xs text-slate-500">Patient identification and Medicare beneficiary jurisdiction.</p>
              </div>
              
              <div>
                <label className={lblCls}>Patient ID</label>
                <input
                  type="text"
                  value={form.patient.patient_id}
                  onChange={(e) => setNested('patient', 'patient_id', e.target.value)}
                  className={inputCls(false) + " font-mono font-bold"}
                  placeholder="e.g. p-sample-1"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={lblCls}>Date of Birth</label>
                  <input
                    type="date"
                    value={form.patient.date_of_birth}
                    onChange={(e) => setNested('patient', 'date_of_birth', e.target.value)}
                    className={inputCls(false)}
                  />
                </div>
                <div>
                  <label className={lblCls}>Age</label>
                  <input
                    type="number"
                    value={form.patient.age}
                    onChange={(e) => setNested('patient', 'age', e.target.value)}
                    className={inputCls(!!errors['patient.age'])}
                    placeholder="e.g. 68"
                  />
                </div>
                <div>
                  <label className={lblCls}>Gender</label>
                  <select
                    value={form.patient.gender}
                    onChange={(e) => setNested('patient', 'gender', e.target.value)}
                    className={inputCls(false)}
                  >
                    <option value="">Select Gender</option>
                    <option value="M">Male (M)</option>
                    <option value="F">Female (F)</option>
                  </select>
                </div>
                <div>
                  <label className={lblCls}>Patient State</label>
                  <select
                    value={form.patient.state}
                    onChange={(e) => setNested('patient', 'state', e.target.value)}
                    className={inputCls(false)}
                  >
                    <option value="">Select State</option>
                    {US_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: CLINICAL */}
          {activeTab === 2 && (
            <div className="max-w-3xl mx-auto space-y-4">
              <div className="space-y-0.5 pb-2 border-b border-slate-100">
                <h4 className="text-sm font-bold text-slate-800">Clinical & Service Details</h4>
                <p className="text-xs text-slate-500">Provide the procedure code, ICD-10 diagnoses, and medical documentation for policy matching.</p>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className={lblCls}>CPT / HCPCS Procedure Code <span className="text-rose-500">*</span></label>
                  <input
                    type="text"
                    value={form.service.procedure_code}
                    onChange={(e) => setNested('service', 'procedure_code', e.target.value.toUpperCase())}
                    className={inputCls(!!errors['service.procedure_code']) + " font-mono uppercase font-bold"}
                    placeholder="e.g. 64483"
                  />
                  {errors['service.procedure_code'] && (
                    <p className="text-[10px] text-rose-600 mt-1 font-medium">{errors['service.procedure_code']}</p>
                  )}
                </div>
                <div>
                  <label className={lblCls}>Place of Service</label>
                  <input
                    type="text"
                    value={form.service.place_of_service}
                    onChange={(e) => setNested('service', 'place_of_service', e.target.value)}
                    className={inputCls(false)}
                    placeholder="e.g. Outpatient Clinic"
                  />
                </div>
              </div>

              <div>
                <label className={lblCls}>Diagnoses (ICD-10) <span className="text-rose-500">*</span></label>
                <div className="space-y-2">
                  {form.diagnoses.map((dx, idx) => (
                    <div key={idx} className="flex gap-2 items-start">
                      <input
                        type="text"
                        value={dx.icd10_code}
                        onChange={(e) => setDiagnosis(idx, 'icd10_code', e.target.value)}
                        placeholder="ICD-10 Code"
                        maxLength={8}
                        className={inputCls(errors['diagnoses'] && idx===0) + " w-28 font-mono uppercase"}
                      />
                      <input
                        type="text"
                        value={dx.description}
                        onChange={(e) => setDiagnosis(idx, 'description', e.target.value)}
                        placeholder="Diagnosis Description (e.g. Lumbar radiculopathy)"
                        className={inputCls(false) + " flex-1"}
                      />
                      {form.diagnoses.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeDiagnosis(idx)}
                          className="p-1.5 text-slate-400 hover:text-rose-600 bg-slate-50 hover:bg-rose-50 rounded-lg transition-colors border border-slate-200"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  ))}
                  {errors['diagnoses'] && (
                    <p className="text-[10px] text-rose-600 font-medium">{errors['diagnoses']}</p>
                  )}
                  <button
                    type="button"
                    onClick={addDiagnosis}
                    className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold text-sky-800 bg-sky-50 border border-sky-200 rounded-lg hover:bg-sky-100 transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Secondary Diagnosis</span>
                  </button>
                </div>
              </div>

              <div>
                <label className={lblCls}>Clinical Documentation & Medical Notes</label>
                <textarea 
                  value={form.clinical_notes} 
                  onChange={(e) => setFlat('clinical_notes', e.target.value)}
                  placeholder="Provide clinical justification, conservative treatment trials failed, imaging findings, exam severity..."
                  rows={6}
                  className="w-full p-3 text-xs rounded-lg bg-slate-50 border border-slate-200 focus:border-sky-600 focus:ring-2 focus:ring-sky-500/20 focus:outline-none resize-y text-slate-800 leading-relaxed font-sans" 
                />
              </div>
            </div>
          )}

          {/* TAB 3: ADMIN */}
          {activeTab === 3 && (
            <div className="max-w-2xl mx-auto space-y-4">
              <div className="space-y-0.5 pb-2 border-b border-slate-100">
                <h4 className="text-sm font-bold text-slate-800">Administrative & Provider Details</h4>
                <p className="text-xs text-slate-500">Provider specialty, coverage plan, and review urgency classification.</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3.5 bg-slate-50 rounded-lg border border-slate-200/80">
                <div>
                  <label className={lblCls}>Review Type (Urgency)</label>
                  <select
                    value={form.request.review_type}
                    onChange={(e) => setNested('request', 'review_type', e.target.value)}
                    className={inputCls(false)}
                  >
                    <option value="URGENT">Expedited Review (24h)</option>
                    <option value="NON_URGENT">Standard Review (72h)</option>
                    <option value="ROUTINE">Routine Review (14d)</option>
                  </select>
                </div>
                <div>
                  <label className={lblCls}>Request Type</label>
                  <select
                    value={form.request.request_type}
                    onChange={(e) => setNested('request', 'request_type', e.target.value)}
                    className={inputCls(false)}
                  >
                    <option value="INITIAL">Initial Authorization</option>
                    <option value="REAUTHORIZATION">Reauthorization / Renewal</option>
                  </select>
                </div>
                <div className="sm:col-span-2">
                  <label className={lblCls}>PA Request ID (Optional)</label>
                  <input
                    type="text"
                    value={form.pa_request_id}
                    onChange={(e) => setFlat('pa_request_id', e.target.value)}
                    className={inputCls(false) + " font-mono"}
                    placeholder="Leave empty to auto-generate (e.g. PA-REAL-001)"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3.5 bg-slate-50 rounded-lg border border-slate-200/80">
                <div>
                  <label className={lblCls}>Payer</label>
                  <input
                    type="text"
                    value={form.coverage.payer}
                    onChange={(e) => setNested('coverage', 'payer', e.target.value)}
                    className={inputCls(false)}
                    placeholder="e.g. Medicare"
                  />
                </div>
                <div>
                  <label className={lblCls}>Plan ID</label>
                  <input
                    type="text"
                    value={form.coverage.plan_id}
                    onChange={(e) => setNested('coverage', 'plan_id', e.target.value)}
                    className={inputCls(false)}
                    placeholder="e.g. MED-TX-001"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3.5 bg-slate-50 rounded-lg border border-slate-200/80">
                <div>
                  <label className={lblCls}>Provider Organization</label>
                  <input
                    type="text"
                    value={form.provider.organization_name}
                    onChange={(e) => setNested('provider', 'organization_name', e.target.value)}
                    className={inputCls(false)}
                    placeholder="e.g. Texas Spine Specialists"
                  />
                </div>
                <div>
                  <label className={lblCls}>Provider Specialty</label>
                  <input
                    type="text"
                    value={form.provider.specialty}
                    onChange={(e) => setNested('provider', 'specialty', e.target.value)}
                    className={inputCls(false)}
                    placeholder="e.g. Interventional Pain Management"
                  />
                </div>
              </div>
            </div>
          )}

          {/* ACTIONS FOOTER */}
          <div className="mt-6 pt-4 border-t border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              {activeTab > 1 ? (
                <button 
                  type="button" 
                  onClick={() => setActiveTab(prev => prev - 1)}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 transition-colors shadow-2xs"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  <span>Previous</span>
                </button>
              ) : <div />}

              {activeTab < 3 && (
                <button 
                  type="button" 
                  onClick={() => setActiveTab(prev => prev + 1)}
                  className="inline-flex items-center gap-1 px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-900 text-xs font-bold text-white transition-colors"
                >
                  <span>Next Step</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={reset}
                className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Clear
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center gap-1.5 px-5 py-2 rounded-lg bg-sky-700 hover:bg-sky-800 disabled:bg-slate-400 text-xs font-bold text-white shadow-2xs transition-all"
              >
                {submitting ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Evaluating Request...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4" />
                    <span>Evaluate Prior Authorization</span>
                  </>
                )}
              </button>
            </div>
          </div>

        </form>
      </div>
    </div>
  );
}
