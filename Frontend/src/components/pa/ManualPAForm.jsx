import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Send,
  RotateCcw,
  Plus,
  X,
  RefreshCw,
  AlertCircle,
  FileText,
  Stethoscope,
  MapPin,
  User,
  ClipboardList,
  Calendar,
  Zap,
  Building2,
  Shield,
  Hash,
} from 'lucide-react';
import { createPARequest } from '../../services/api';
import { savePARequest } from '../../utils/storage';

const US_STATES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA',
  'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT',
  'VA', 'WA', 'WV', 'WI', 'WY',
];

const SAMPLE_CASES = [
  {
    label: 'Epidural Injection (LCD L39054)',
    data: {
      pa_request_id: '',
      patient: { patient_id: 'p-sample-1', date_of_birth: '1969-03-15', age: 55, gender: 'M', state: 'TX' },
      coverage: { payer: 'Medicare', plan_id: '', plan_name: '' },
      request: { review_type: 'NON_URGENT', request_type: 'INITIAL', urgency_reason: '', previous_authorization_number: '' },
      provider: { provider_id: '', specialty: 'Pain Management', organization_id: '', organization_name: '', state: 'TX' },
      service: {
        service_description: 'Epidural steroid injection for lumbar radiculopathy',
        procedure_code: '64483',
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
        place_of_service: 'Outpatient',
        number_of_sessions: 1, duration: '1 day', frequency: 'Once',
      },
      diagnoses: [{ description: 'Lumbar radiculopathy', icd10_code: 'M54.16' }],
      clinical_notes: 'Patient presents with lumbar radiculopathy confirmed on MRI. Conservative therapy including physical therapy was tried for 8 weeks without relief.',
    },
  },
  {
    label: 'Stem Cell Transplant (NCD 110.23)',
    data: {
      pa_request_id: '',
      patient: { patient_id: 'p-sample-2', date_of_birth: '1982-07-22', age: 42, gender: 'F', state: 'CA' },
      coverage: { payer: 'Medicare', plan_id: '', plan_name: '' },
      request: { review_type: 'NON_URGENT', request_type: 'INITIAL', urgency_reason: '', previous_authorization_number: '' },
      provider: { provider_id: '', specialty: 'Oncology', organization_id: '', organization_name: '', state: 'CA' },
      service: {
        service_description: 'Allogeneic hematopoietic stem cell transplantation',
        procedure_code: '38240',
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
        place_of_service: 'Inpatient',
        number_of_sessions: 1, duration: '1 day', frequency: 'Once',
      },
      diagnoses: [{ description: 'Acute lymphoblastic leukemia', icd10_code: 'C91.0' }],
      clinical_notes: 'Allogeneic HSCT recommended following failure of first-line chemotherapy.',
    },
  },
  {
    label: 'Dental Gingivectomy',
    data: {
      pa_request_id: 'PA-001',
      patient: { patient_id: 'p001', date_of_birth: '1979-02-20', age: 47, gender: 'M', state: 'Massachusetts' },
      coverage: { payer: 'Medicare', plan_id: 'MED-MA-001', plan_name: 'Medicare Advantage Example Plan' },
      request: { review_type: 'NON_URGENT', request_type: 'INITIAL', urgency_reason: '', previous_authorization_number: '' },
      provider: { provider_id: 'prov018', specialty: 'GENERAL PRACTICE', organization_id: 'org018', organization_name: 'FENWAY COMMUNITY HEALTH CENTER INC', state: 'MA' },
      service: {
        service_description: 'Gingivectomy or gingivoplasty, four or more contiguous teeth',
        procedure_code: 'D4210',
        start_date: '2026-08-15', end_date: '2026-08-15',
        place_of_service: 'Outpatient Dental Surgical Suite',
        number_of_sessions: 1, duration: '1 day', frequency: 'Once',
      },
      diagnoses: [
        { description: 'Gingival disease', icd10_code: 'K06.8' },
        { description: 'Chronic gingivitis', icd10_code: 'K05.10' },
      ],
      clinical_notes: '',
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
  if (!proc) errors['service.procedure_code'] = 'Procedure code is required.';
  else if (!/^[A-Za-z0-9]{1,7}$/.test(proc)) errors['service.procedure_code'] = 'Enter a valid CPT/HCPCS code.';
  const validDx = (form.diagnoses || []).filter((d) => d.icd10_code && d.icd10_code.trim());
  if (validDx.length === 0) errors['diagnoses'] = 'At least one diagnosis with an ICD-10 code is required.';
  const age = form.patient?.age;
  if (age !== '' && age !== null && age !== undefined) {
    const n = Number(age);
    if (isNaN(n) || n < 0 || n > 130) errors['patient.age'] = 'Enter a valid age (0-130).';
  }
  return errors;
}

export default function ManualPAForm() {
  const navigate = useNavigate();
  const [form, setForm] = useState(DEFAULT_FORM);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

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
  const loadSample = (s) => { setForm({ ...s.data }); setErrors({}); setSubmitError(null); };
  const reset = () => { setForm(DEFAULT_FORM); setErrors({}); setSubmitError(null); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitError(null);
    const validationErrors = validate(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      window.scrollTo({ top: 0, behavior: 'smooth' });
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
          service_description: form.clinical_notes?.trim() || form.service.service_description?.trim() || '',
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
      const msg = err.message || 'An error occurred while submitting the request.';
      if (msg.toLowerCase().includes('network') || msg.toLowerCase().includes('connect') || msg.toLowerCase().includes('fetch')) {
        setSubmitError('Unable to connect to the Prior Authorization service. Please ensure the backend is running on http://localhost:8000.');
      } else {
        setSubmitError(msg);
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } finally {
      setSubmitting(false);
    }
  };

  const inputCls = (hasErr) =>
    `w-full px-3 py-2 text-sm rounded-lg border ${hasErr ? 'border-rose-400 bg-rose-50/40' : 'border-slate-300 focus:border-sky-500'} focus:outline-none focus:ring-2 focus:ring-sky-500/20 text-slate-800 transition-colors`;
  const selectCls = (accent) =>
    `w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:border-${accent}-500 focus:ring-2 focus:ring-${accent}-500/20 focus:outline-none bg-white text-slate-800 transition-colors`;

  return (
    <form onSubmit={handleSubmit} className="space-y-5" noValidate>

      {/* Quick load */}
      <div className="flex flex-wrap items-center gap-2 p-3 bg-slate-50 border border-slate-200 rounded-xl">
        <span className="text-xs font-semibold text-slate-600 mr-1">Quick load:</span>
        {SAMPLE_CASES.map((s) => (
          <button key={s.label} type="button" onClick={() => loadSample(s)}
            className="px-2.5 py-1 text-xs font-medium rounded-lg bg-white border border-slate-200 hover:border-sky-400 hover:text-sky-700 shadow-sm transition-colors">
            {s.label}
          </button>
        ))}
        <button type="button" onClick={reset}
          className="ml-auto flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-500 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors">
          <RotateCcw className="w-3.5 h-3.5" />Clear
        </button>
      </div>

      {submitError && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-rose-800"><span className="font-bold block mb-0.5">Submission Failed</span>{submitError}</div>
        </div>
      )}

      {/* REQUEST META */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
          <div className="p-1.5 rounded-lg bg-indigo-50"><Hash className="w-4 h-4 text-indigo-600" /></div>
          <h3 className="text-sm font-bold text-slate-800">Request Info</h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">PA Request ID <span className="text-slate-400 font-normal">(auto if blank)</span></label>
            <input type="text" value={form.pa_request_id} onChange={(e) => setFlat('pa_request_id', e.target.value)}
              placeholder="e.g. PA-001" className={inputCls(false)} />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Review Type</label>
            <select value={form.request.review_type} onChange={(e) => setNested('request', 'review_type', e.target.value)} className={selectCls('indigo')}>
              <option value="NON_URGENT">NON_URGENT</option>
              <option value="URGENT">URGENT</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Request Type</label>
            <select value={form.request.request_type} onChange={(e) => setNested('request', 'request_type', e.target.value)} className={selectCls('indigo')}>
              <option value="INITIAL">INITIAL</option>
              <option value="REAUTHORIZATION">REAUTHORIZATION</option>
            </select>
          </div>
        </div>
      </div>

      {/* SERVICE & PROCEDURE */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
          <div className="p-1.5 rounded-lg bg-sky-50"><Stethoscope className="w-4 h-4 text-sky-600" /></div>
          <h3 className="text-sm font-bold text-slate-800">Service & Procedure</h3>
          <span className="text-rose-500 text-sm">*</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">CPT / HCPCS Code <span className="text-rose-500">*</span></label>
            <input type="text" value={form.service.procedure_code}
              onChange={(e) => setNested('service', 'procedure_code', e.target.value.toUpperCase())}
              placeholder="e.g. 64483 or D4210" maxLength={7}
              className={`w-full sm:w-48 px-3 py-2 text-sm font-mono font-semibold rounded-lg border ${errors['service.procedure_code'] ? 'border-rose-400 bg-rose-50/40' : 'border-slate-300 focus:border-sky-500'} focus:outline-none focus:ring-2 focus:ring-sky-500/20 transition-colors uppercase`} />
            {errors['service.procedure_code'] && (
              <p className="mt-1 text-xs text-rose-600 flex items-center gap-1"><AlertCircle className="w-3 h-3" />{errors['service.procedure_code']}</p>
            )}
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Place of Service</label>
            <input type="text" value={form.service.place_of_service} onChange={(e) => setNested('service', 'place_of_service', e.target.value)}
              placeholder="e.g. Outpatient" className={inputCls(false)} />
          </div>
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">Service Description</label>
          <input type="text" value={form.service.service_description} onChange={(e) => setNested('service', 'service_description', e.target.value)}
            placeholder="Human-readable description of the requested service" className={inputCls(false)} />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Start Date</label>
            <input type="date" value={form.service.start_date} onChange={(e) => setNested('service', 'start_date', e.target.value)} className={inputCls(false)} />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">End Date</label>
            <input type="date" value={form.service.end_date} onChange={(e) => setNested('service', 'end_date', e.target.value)} className={inputCls(false)} />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1"># Sessions</label>
            <input type="number" value={form.service.number_of_sessions} onChange={(e) => setNested('service', 'number_of_sessions', e.target.value)}
              min={1} placeholder="1" className={inputCls(false)} />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Frequency</label>
            <input type="text" value={form.service.frequency} onChange={(e) => setNested('service', 'frequency', e.target.value)}
              placeholder="e.g. Once" className={inputCls(false)} />
          </div>
        </div>
      </div>

      {/* DIAGNOSES */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-3">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
          <div className="p-1.5 rounded-lg bg-emerald-50"><FileText className="w-4 h-4 text-emerald-600" /></div>
          <h3 className="text-sm font-bold text-slate-800">Diagnoses</h3>
          <span className="text-rose-500 text-sm">*</span>
        </div>
        <div className="space-y-3">
          {form.diagnoses.map((dx, idx) => (
            <div key={idx} className="flex items-start gap-2">
              <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-2">
                <input type="text" value={dx.icd10_code} onChange={(e) => setDiagnosis(idx, 'icd10_code', e.target.value)}
                  placeholder={`ICD-10 Code #${idx + 1}`} maxLength={8}
                  className={`px-3 py-2 text-sm font-mono font-semibold rounded-lg border ${errors['diagnoses'] && idx === 0 ? 'border-rose-400 bg-rose-50/40' : 'border-slate-300 focus:border-emerald-500'} focus:outline-none focus:ring-2 focus:ring-emerald-500/20 uppercase`} />
                <input type="text" value={dx.description} onChange={(e) => setDiagnosis(idx, 'description', e.target.value)}
                  placeholder="Description (optional)"
                  className="px-3 py-2 text-sm rounded-lg border border-slate-300 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20" />
              </div>
              {form.diagnoses.length > 1 && (
                <button type="button" onClick={() => removeDiagnosis(idx)}
                  className="p-1.5 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-colors mt-0.5" title="Remove">
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          ))}
          <button type="button" onClick={addDiagnosis}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-lg transition-colors">
            <Plus className="w-3.5 h-3.5" />Add Diagnosis
          </button>
          {errors['diagnoses'] && (
            <p className="text-xs text-rose-600 flex items-center gap-1"><AlertCircle className="w-3 h-3" />{errors['diagnoses']}</p>
          )}
          <p className="text-[11px] text-slate-400">ICD-10-CM format. Multiple diagnoses supported.</p>
        </div>
      </div>

      {/* PATIENT */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
          <div className="p-1.5 rounded-lg bg-purple-50"><User className="w-4 h-4 text-purple-600" /></div>
          <h3 className="text-sm font-bold text-slate-800">Patient</h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Patient ID</label>
            <input type="text" value={form.patient.patient_id} onChange={(e) => setNested('patient', 'patient_id', e.target.value)}
              placeholder="e.g. p001" className={inputCls(false)} />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Date of Birth</label>
            <input type="date" value={form.patient.date_of_birth} onChange={(e) => setNested('patient', 'date_of_birth', e.target.value)} className={inputCls(false)} />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Age (years)</label>
            <input type="number" value={form.patient.age} onChange={(e) => setNested('patient', 'age', e.target.value)}
              placeholder="e.g. 55" min={0} max={130} className={inputCls(!!errors['patient.age'])} />
            {errors['patient.age'] && <p className="mt-1 text-xs text-rose-600">{errors['patient.age']}</p>}
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Gender</label>
            <select value={form.patient.gender} onChange={(e) => setNested('patient', 'gender', e.target.value)} className={selectCls('purple')}>
              <option value="">Select</option>
              <option value="M">M - Male</option>
              <option value="F">F - Female</option>
              <option value="O">O - Other</option>
              <option value="U">U - Unknown</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">
              <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5 text-purple-500" />Patient State</span>
            </label>
            <select value={form.patient.state} onChange={(e) => setNested('patient', 'state', e.target.value)} className={selectCls('purple')}>
              <option value="">Select state (optional)</option>
              {US_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <p className="mt-1 text-[11px] text-slate-400">Used for jurisdiction-based LCD lookup.</p>
          </div>
        </div>
      </div>

      {/* COVERAGE */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
          <div className="p-1.5 rounded-lg bg-teal-50"><Shield className="w-4 h-4 text-teal-600" /></div>
          <h3 className="text-sm font-bold text-slate-800">Coverage</h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Payer</label>
            <input type="text" value={form.coverage.payer} onChange={(e) => setNested('coverage', 'payer', e.target.value)}
              placeholder="e.g. Medicare" className={inputCls(false)} />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Plan ID</label>
            <input type="text" value={form.coverage.plan_id} onChange={(e) => setNested('coverage', 'plan_id', e.target.value)}
              placeholder="e.g. MED-MA-001" className={inputCls(false)} />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Plan Name</label>
            <input type="text" value={form.coverage.plan_name} onChange={(e) => setNested('coverage', 'plan_name', e.target.value)}
              placeholder="e.g. Medicare Advantage" className={inputCls(false)} />
          </div>
        </div>
      </div>

      {/* PROVIDER */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
          <div className="p-1.5 rounded-lg bg-orange-50"><Building2 className="w-4 h-4 text-orange-600" /></div>
          <h3 className="text-sm font-bold text-slate-800">Provider</h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Organization Name</label>
            <input type="text" value={form.provider.organization_name} onChange={(e) => setNested('provider', 'organization_name', e.target.value)}
              placeholder="e.g. FENWAY COMMUNITY HEALTH CENTER" className={inputCls(false)} />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Specialty</label>
            <input type="text" value={form.provider.specialty} onChange={(e) => setNested('provider', 'specialty', e.target.value)}
              placeholder="e.g. GENERAL PRACTICE" className={inputCls(false)} />
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Provider ID</label>
            <input type="text" value={form.provider.provider_id} onChange={(e) => setNested('provider', 'provider_id', e.target.value)}
              placeholder="e.g. prov018" className={inputCls(false)} />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Organization ID</label>
            <input type="text" value={form.provider.organization_id} onChange={(e) => setNested('provider', 'organization_id', e.target.value)}
              placeholder="e.g. org018" className={inputCls(false)} />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Provider State</label>
            <select value={form.provider.state} onChange={(e) => setNested('provider', 'state', e.target.value)} className={selectCls('orange')}>
              <option value="">Select state</option>
              {US_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* CLINICAL NOTES */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-3">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
          <div className="p-1.5 rounded-lg bg-amber-50"><ClipboardList className="w-4 h-4 text-amber-600" /></div>
          <h3 className="text-sm font-bold text-slate-800">Clinical Notes</h3>
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">Clinical Documentation / Medical Justification</label>
          <textarea value={form.clinical_notes} onChange={(e) => setFlat('clinical_notes', e.target.value)}
            placeholder="Describe the patient clinical history, prior treatments, medical necessity and supporting evidence..."
            rows={5}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 focus:outline-none text-slate-800 leading-relaxed resize-y transition-colors" />
          <p className="mt-1 text-[11px] text-slate-400">Used by semantic and agentic evaluation pipeline.</p>
        </div>
      </div>

      {/* SUBMIT */}
      <div className="sticky bottom-4 z-10">
        <div className="bg-white border border-slate-200 shadow-lg rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="text-xs text-slate-400 hidden sm:block">
            Submitting to <code className="font-mono text-sky-700">POST /api/v1/pa-requests</code>
          </div>
          <button type="submit" disabled={submitting}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3 rounded-xl bg-sky-600 hover:bg-sky-700 disabled:bg-sky-400 text-sm font-bold text-white shadow-sm transition-all">
            {submitting ? (
              <><RefreshCw className="w-4 h-4 animate-spin" /><span>Evaluating Policy...</span></>
            ) : (
              <><Zap className="w-4 h-4" /><span>Submit for Policy Evaluation</span></>
            )}
          </button>
        </div>
      </div>
    </form>
  );
}
