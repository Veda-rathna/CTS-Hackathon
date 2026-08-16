import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  RotateCcw, Plus, X, RefreshCw, AlertCircle, Zap, Sparkles, User, Stethoscope, Building2
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
    label: 'Epidural',
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
    label: 'Stem Cell',
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
    label: 'Dental',
    data: {
      pa_request_id: '',
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
  if (!proc) errors['service.procedure_code'] = 'Req';
  
  const validDx = (form.diagnoses || []).filter((d) => d.icd10_code && d.icd10_code.trim());
  if (validDx.length === 0) errors['diagnoses'] = 'Req';
  
  const age = form.patient?.age;
  if (age !== '' && age !== null && age !== undefined) {
    const n = Number(age);
    if (isNaN(n) || n < 0 || n > 130) errors['patient.age'] = 'Inv';
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
  const loadSample = (s) => { setForm({ ...s.data }); setErrors({}); setSubmitError(null); setActiveTab(1); };
  const reset = () => { setForm(DEFAULT_FORM); setErrors({}); setSubmitError(null); setActiveTab(1); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitError(null);
    const validationErrors = validate(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      // Auto switch tab if error exists
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
      setSubmitError(err.message || 'Error submitting request.');
    } finally {
      setSubmitting(false);
    }
  };

  const inputCls = (hasErr) =>
    `w-full px-3 py-2 text-sm rounded-lg border ${hasErr ? 'border-rose-400 bg-rose-50 text-rose-900' : 'border-slate-300 bg-white hover:border-slate-400 focus:bg-white focus:border-sky-500'} focus:outline-none focus:ring-4 focus:ring-sky-500/10 transition-all shadow-sm`;
  
  const lblCls = "block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1.5";

  return (
    <div className="flex flex-col h-[calc(100vh-100px)] w-full max-w-4xl mx-auto overflow-hidden bg-white/70 backdrop-blur-xl rounded-2xl border border-slate-200/80 shadow-lg">
      
      {/* HEADER / TOP BAR */}
      <div className="flex items-center justify-between p-4 border-b border-slate-200 bg-slate-50/50 flex-shrink-0">
        <h2 className="text-base font-extrabold text-slate-800">Prior Authorization Intake</h2>
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-400 mr-1 hidden sm:block">Quick Demo Loads:</span>
          {SAMPLE_CASES.map((s) => (
            <button key={s.label} type="button" onClick={() => loadSample(s)}
              className="px-2.5 py-1.5 text-xs font-bold rounded-lg bg-white border border-slate-200 text-slate-600 hover:text-sky-700 hover:border-sky-300 shadow-sm transition-all">
              {s.label}
            </button>
          ))}
          <button type="button" onClick={reset} className="ml-2 p-1.5 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-colors" title="Clear Form">
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {submitError && (
        <div className="mx-4 mt-4 p-3 rounded-xl bg-rose-50 border border-rose-200 flex items-center gap-3 flex-shrink-0">
          <AlertCircle className="w-5 h-5 text-rose-600" />
          <span className="text-sm font-medium text-rose-800">{submitError}</span>
        </div>
      )}

      {/* TABS NAVIGATION */}
      <div className="flex px-4 pt-4 gap-2 flex-shrink-0">
        {[
          { id: 1, label: 'Patient Info', icon: User },
          { id: 2, label: 'Clinical Data', icon: Stethoscope },
          { id: 3, label: 'Admin Details', icon: Building2 },
        ].map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center gap-2 py-3 px-2 rounded-t-xl text-sm font-bold border-t border-x transition-all ${
                isActive 
                  ? 'bg-white border-slate-200 text-sky-700' 
                  : 'bg-slate-50 border-transparent text-slate-500 hover:bg-slate-100 hover:text-slate-700'
              }`}
              style={isActive ? { marginBottom: '-1px', zIndex: 10 } : {}}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 overflow-hidden flex flex-col bg-white border-t border-slate-200">
        <form onSubmit={handleSubmit} className="flex-1 flex flex-col overflow-hidden" noValidate>
          
          <div className="flex-1 p-6 sm:p-8 overflow-y-auto">
            {/* TAB 1: PATIENT */}
            {activeTab === 1 && (
              <div className="max-w-2xl mx-auto space-y-6 animate-in fade-in duration-300">
                <div className="space-y-1 mb-6">
                  <h3 className="text-lg font-extrabold text-slate-800">Patient Demographics</h3>
                  <p className="text-sm text-slate-500">Enter patient ID to automatically trigger Synthea AI history linking.</p>
                </div>
                
                <div>
                  <label className={lblCls}>Patient ID</label>
                  <input type="text" value={form.patient.patient_id} onChange={(e) => setNested('patient', 'patient_id', e.target.value)} className={inputCls(false) + " font-mono font-bold"} placeholder="p-sample-1" />
                  {form.patient.patient_id && (
                    <div className="mt-2 text-xs font-bold text-purple-700 bg-purple-50 px-3 py-2 rounded-lg border border-purple-100 flex items-center gap-2">
                      <Sparkles className="w-4 h-4" /> Synthea Medical History Merging Active
                    </div>
                  )}
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={lblCls}>Date of Birth</label>
                    <input type="date" value={form.patient.date_of_birth} onChange={(e) => setNested('patient', 'date_of_birth', e.target.value)} className={inputCls(false)} />
                  </div>
                  <div>
                    <label className={lblCls}>Age</label>
                    <input type="number" value={form.patient.age} onChange={(e) => setNested('patient', 'age', e.target.value)} className={inputCls(!!errors['patient.age'])} />
                  </div>
                  <div>
                    <label className={lblCls}>Gender</label>
                    <select value={form.patient.gender} onChange={(e) => setNested('patient', 'gender', e.target.value)} className={inputCls(false)}>
                      <option value="">Select Gender</option><option value="M">Male (M)</option><option value="F">Female (F)</option>
                    </select>
                  </div>
                  <div>
                    <label className={lblCls}>Patient State</label>
                    <select value={form.patient.state} onChange={(e) => setNested('patient', 'state', e.target.value)} className={inputCls(false)}>
                      <option value="">Select State</option>
                      {US_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: CLINICAL */}
            {activeTab === 2 && (
              <div className="max-w-3xl mx-auto flex flex-col h-full animate-in fade-in duration-300">
                <div className="space-y-1 mb-5 flex-shrink-0">
                  <h3 className="text-lg font-extrabold text-slate-800">Clinical Evaluation Data</h3>
                  <p className="text-sm text-slate-500">Provide the codes and clinical notes required for policy matching.</p>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-5 flex-shrink-0">
                  <div>
                    <label className={lblCls}>CPT / HCPCS Code <span className="text-rose-500">*</span></label>
                    <input type="text" value={form.service.procedure_code} onChange={(e) => setNested('service', 'procedure_code', e.target.value.toUpperCase())} className={inputCls(!!errors['service.procedure_code']) + " font-mono uppercase font-bold"} placeholder="e.g. 64483" />
                  </div>
                  <div>
                    <label className={lblCls}>Place of Service</label>
                    <input type="text" value={form.service.place_of_service} onChange={(e) => setNested('service', 'place_of_service', e.target.value)} className={inputCls(false)} placeholder="Outpatient" />
                  </div>
                </div>

                <div className="mb-5 flex-shrink-0">
                  <label className={lblCls}>Diagnoses (ICD-10) <span className="text-rose-500">*</span></label>
                  <div className="space-y-2">
                    {form.diagnoses.map((dx, idx) => (
                      <div key={idx} className="flex gap-2 items-start">
                        <input type="text" value={dx.icd10_code} onChange={(e) => setDiagnosis(idx, 'icd10_code', e.target.value)} placeholder="Code" maxLength={8} className={inputCls(errors['diagnoses'] && idx===0) + " w-32 font-mono uppercase"} />
                        <input type="text" value={dx.description} onChange={(e) => setDiagnosis(idx, 'description', e.target.value)} placeholder="Diagnosis Description" className={inputCls(false) + " flex-1"} />
                        {form.diagnoses.length > 1 && (
                          <button type="button" onClick={() => removeDiagnosis(idx)} className="p-2 text-slate-400 hover:text-rose-500 bg-slate-50 hover:bg-rose-50 rounded-lg transition-colors border border-slate-200 mt-0.5"><X className="w-4 h-4" /></button>
                        )}
                      </div>
                    ))}
                    <button type="button" onClick={addDiagnosis} className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-sky-700 bg-sky-50 border border-sky-100 rounded-lg hover:bg-sky-100 transition-colors">
                      <Plus className="w-4 h-4" /> Add Diagnosis
                    </button>
                  </div>
                </div>

                <div className="flex-1 flex flex-col min-h-0">
                  <label className={lblCls}>Clinical Documentation / Justification</label>
                  <textarea 
                    value={form.clinical_notes} 
                    onChange={(e) => setFlat('clinical_notes', e.target.value)}
                    placeholder="Provide medical justification, previous treatments failed..."
                    className="flex-1 w-full p-4 text-sm rounded-xl bg-slate-50 border border-slate-200 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 focus:outline-none resize-none text-slate-800 leading-relaxed shadow-inner" 
                  />
                </div>
              </div>
            )}

            {/* TAB 3: ADMIN */}
            {activeTab === 3 && (
              <div className="max-w-2xl mx-auto space-y-6 animate-in fade-in duration-300">
                <div className="space-y-1 mb-6">
                  <h3 className="text-lg font-extrabold text-slate-800">Administrative Metadata</h3>
                  <p className="text-sm text-slate-500">Provider, coverage, and request routing details.</p>
                </div>

                <div className="grid grid-cols-2 gap-5 p-5 bg-slate-50 rounded-2xl border border-slate-100">
                  <div>
                    <label className={lblCls}>Review Type</label>
                    <select value={form.request.review_type} onChange={(e) => setNested('request', 'review_type', e.target.value)} className={inputCls(false)}>
                      <option value="NON_URGENT">Standard</option><option value="URGENT">Expedited</option>
                    </select>
                  </div>
                  <div>
                    <label className={lblCls}>Request Type</label>
                    <select value={form.request.request_type} onChange={(e) => setNested('request', 'request_type', e.target.value)} className={inputCls(false)}>
                      <option value="INITIAL">Initial</option><option value="REAUTHORIZATION">Reauthorization</option>
                    </select>
                  </div>
                  <div>
                    <label className={lblCls}>PA Request ID</label>
                    <input type="text" value={form.pa_request_id} onChange={(e) => setFlat('pa_request_id', e.target.value)} className={inputCls(false)} placeholder="Auto-generated" />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-5 p-5 bg-slate-50 rounded-2xl border border-slate-100">
                  <div>
                    <label className={lblCls}>Payer</label>
                    <input type="text" value={form.coverage.payer} onChange={(e) => setNested('coverage', 'payer', e.target.value)} className={inputCls(false)} placeholder="e.g. Medicare" />
                  </div>
                  <div>
                    <label className={lblCls}>Plan ID</label>
                    <input type="text" value={form.coverage.plan_id} onChange={(e) => setNested('coverage', 'plan_id', e.target.value)} className={inputCls(false)} />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-5 p-5 bg-slate-50 rounded-2xl border border-slate-100">
                  <div>
                    <label className={lblCls}>Provider Organization</label>
                    <input type="text" value={form.provider.organization_name} onChange={(e) => setNested('provider', 'organization_name', e.target.value)} className={inputCls(false)} />
                  </div>
                  <div>
                    <label className={lblCls}>Provider Specialty</label>
                    <input type="text" value={form.provider.specialty} onChange={(e) => setNested('provider', 'specialty', e.target.value)} className={inputCls(false)} />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* CONDITIONAL FOOTER */}
          <div className="p-4 border-t border-slate-200 bg-slate-50 flex-shrink-0 flex items-center justify-between">
            {activeTab > 1 ? (
              <button 
                type="button" 
                onClick={() => setActiveTab(prev => prev - 1)}
                className="px-6 py-3 rounded-xl text-sm font-bold text-slate-600 bg-white border border-slate-200 hover:bg-slate-100 hover:text-slate-900 transition-colors shadow-sm"
              >
                Previous Step
              </button>
            ) : <div />}

            {activeTab < 3 ? (
              <button 
                type="button" 
                onClick={() => setActiveTab(prev => prev + 1)}
                className="px-8 py-3 rounded-xl bg-sky-600 hover:bg-sky-700 text-sm font-extrabold text-white shadow-md transition-all"
              >
                Next Step
              </button>
            ) : (
              <button type="submit" disabled={submitting}
                className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 disabled:bg-slate-400 text-sm font-extrabold text-white shadow-lg transition-all flex items-center justify-center gap-2">
                {submitting ? (
                  <><RefreshCw className="w-5 h-5 animate-spin" /> Adjudicating Request...</>
                ) : (
                  <><Zap className="w-5 h-5 text-sky-400 fill-sky-400" /> Submit to AI Engine</>
                )}
              </button>
            )}
          </div>

        </form>
      </div>
    </div>
  );
}
