import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Send,
  RotateCcw,
  Plus,
  X,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  FileText,
  Stethoscope,
  MapPin,
  User,
  ClipboardList,
  Calendar,
  Zap,
} from 'lucide-react';
import { runTriage } from '../../services/api';
import { savePARequest } from '../../utils/storage';

const US_STATES = [
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
  'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
  'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
  'VA','WA','WV','WI','WY',
];

const SAMPLE_CASES = [
  {
    label: 'Epidural Injection (LCD L39054)',
    data: {
      procedure_code: '64483',
      diagnosis_codes: ['M54.16'],
      state: 'TX',
      patient_age: 55,
      clinical_notes: 'Patient presents with lumbar radiculopathy confirmed on MRI. Conservative therapy including physical therapy was tried for 8 weeks without relief. Fluoroscopic guidance required.',
      service_date: new Date().toISOString().split('T')[0],
    },
  },
  {
    label: 'Stem Cell Transplant (NCD 110.23)',
    data: {
      procedure_code: '38240',
      diagnosis_codes: ['C91.0'],
      state: 'CA',
      patient_age: 42,
      clinical_notes: 'Patient diagnosed with acute myeloid leukemia. Allogeneic hematopoietic stem cell transplantation recommended following failure of first-line chemotherapy.',
      service_date: new Date().toISOString().split('T')[0],
    },
  },
  {
    label: 'Unknown Procedure (RMI)',
    data: {
      procedure_code: 'XXXXXXX',
      diagnosis_codes: ['Z00.00'],
      state: 'FL',
      patient_age: 67,
      clinical_notes: 'Routine annual wellness visit.',
      service_date: new Date().toISOString().split('T')[0],
    },
  },
];

const DEFAULT_FORM = {
  procedure_code: '',
  diagnosis_codes: [''],
  state: '',
  patient_age: '',
  clinical_notes: '',
  service_date: new Date().toISOString().split('T')[0],
};

function validate(form) {
  const errors = {};
  const proc = (form.procedure_code || '').trim();
  if (!proc) errors.procedure_code = 'Procedure code is required.';
  else if (!/^[A-Za-z0-9]{1,7}$/.test(proc)) errors.procedure_code = 'Enter a valid CPT/HCPCS code (e.g. 64483).';

  const codes = (form.diagnosis_codes || []).filter((c) => c.trim());
  if (codes.length === 0) errors.diagnosis_codes = 'At least one ICD-10 diagnosis code is required.';

  if (form.patient_age !== '' && form.patient_age !== null) {
    const age = Number(form.patient_age);
    if (isNaN(age) || age < 0 || age > 130) errors.patient_age = 'Enter a valid patient age (0–130).';
  }

  return errors;
}

export default function ManualPAForm() {
  const navigate = useNavigate();
  const [form, setForm] = useState(DEFAULT_FORM);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  // ── Handlers ────────────────────────────────────────────────────────────────
  const set = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) setErrors((prev) => { const next = { ...prev }; delete next[field]; return next; });
  };

  const setDiagCode = (idx, value) => {
    const next = [...form.diagnosis_codes];
    next[idx] = value.toUpperCase().trim();
    set('diagnosis_codes', next);
  };

  const addDiagCode = () => set('diagnosis_codes', [...form.diagnosis_codes, '']);

  const removeDiagCode = (idx) => {
    if (form.diagnosis_codes.length === 1) return;
    set('diagnosis_codes', form.diagnosis_codes.filter((_, i) => i !== idx));
  };

  const loadSample = (sample) => {
    setForm({ ...sample.data });
    setErrors({});
    setSubmitError(null);
  };

  const reset = () => {
    setForm(DEFAULT_FORM);
    setErrors({});
    setSubmitError(null);
  };

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
        procedure_code: form.procedure_code.trim().toUpperCase(),
        diagnosis_codes: form.diagnosis_codes.map((c) => c.trim().toUpperCase()).filter(Boolean),
        state: form.state || null,
        patient_age: form.patient_age !== '' ? Number(form.patient_age) : null,
        clinical_notes: form.clinical_notes.trim() || null,
        service_date: form.service_date || null,
      };

      const response = await runTriage(payload);

      // Build a display record storing both the request and the full triage response
      const paId = `PA-${Date.now().toString().slice(-6)}`;
      const displayRecord = {
        pa_request_id: paId,
        // Triage request for display
        procedure_code: payload.procedure_code,
        diagnosis_codes: payload.diagnosis_codes,
        state: payload.state,
        patient_age: payload.patient_age,
        clinical_notes: payload.clinical_notes,
        service_date: payload.service_date,
        created_at: new Date().toISOString(),
      };

      const saved = savePARequest(displayRecord, response);
      navigate(`/pa/${saved.pa_request_id}`);
    } catch (err) {
      const msg = err.message || 'An error occurred while submitting the request.';
      if (msg.toLowerCase().includes('network') || msg.toLowerCase().includes('connect') || msg.toLowerCase().includes('fetch')) {
        setSubmitError('Unable to connect to the Prior Authorization service. Please ensure the backend is running on http://localhost:8001.');
      } else {
        setSubmitError(msg);
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } finally {
      setSubmitting(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <form onSubmit={handleSubmit} className="space-y-5" noValidate>

      {/* Sample Case Templates */}
      <div className="flex flex-wrap items-center gap-2 p-3 bg-slate-50 border border-slate-200 rounded-xl">
        <span className="text-xs font-semibold text-slate-600 mr-1">Quick load:</span>
        {SAMPLE_CASES.map((s) => (
          <button
            key={s.label}
            type="button"
            onClick={() => loadSample(s)}
            className="px-2.5 py-1 text-xs font-medium rounded-lg bg-white border border-slate-200 hover:border-sky-400 hover:text-sky-700 shadow-sm transition-colors"
          >
            {s.label}
          </button>
        ))}
        <button
          type="button"
          onClick={reset}
          className="ml-auto flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-500 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Clear
        </button>
      </div>

      {/* Submit Error Banner */}
      {submitError && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-rose-800">
            <span className="font-bold block mb-0.5">Submission Failed</span>
            {submitError}
          </div>
        </div>
      )}

      {/* ── Procedure Code ─────────────────────────────────────────────────── */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-3">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
          <div className="p-1.5 rounded-lg bg-sky-50"><Stethoscope className="w-4 h-4 text-sky-600" /></div>
          <h3 className="text-sm font-bold text-slate-800">Procedure</h3>
          <span className="text-rose-500 text-sm">*</span>
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            CPT / HCPCS Procedure Code
          </label>
          <input
            type="text"
            value={form.procedure_code}
            onChange={(e) => set('procedure_code', e.target.value.toUpperCase())}
            placeholder="e.g. 64483"
            maxLength={7}
            className={`w-full sm:w-48 px-3 py-2 text-sm font-mono font-semibold rounded-lg border ${
              errors.procedure_code ? 'border-rose-400 bg-rose-50/40' : 'border-slate-300 focus:border-sky-500'
            } text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500/20 transition-colors uppercase`}
          />
          {errors.procedure_code && (
            <p className="mt-1 text-xs text-rose-600 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />{errors.procedure_code}
            </p>
          )}
          <p className="mt-1 text-[11px] text-slate-400">
            Enter a valid HCPCS Level II or CPT code. Auto-normalized to uppercase.
          </p>
        </div>
      </div>

      {/* ── Diagnosis Codes ──────────────────────────────────────────────────── */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-3">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
          <div className="p-1.5 rounded-lg bg-emerald-50"><FileText className="w-4 h-4 text-emerald-600" /></div>
          <h3 className="text-sm font-bold text-slate-800">Diagnosis Codes</h3>
          <span className="text-rose-500 text-sm">*</span>
        </div>

        <div className="space-y-2">
          {form.diagnosis_codes.map((code, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <div className="relative flex-1 sm:flex-initial">
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setDiagCode(idx, e.target.value)}
                  placeholder={`ICD-10 Code #${idx + 1} (e.g. M54.16)`}
                  maxLength={8}
                  className={`w-full sm:w-44 px-3 py-2 text-sm font-mono font-semibold rounded-lg border ${
                    errors.diagnosis_codes && idx === 0 ? 'border-rose-400 bg-rose-50/40' : 'border-slate-300 focus:border-emerald-500'
                  } text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 transition-colors uppercase`}
                />
              </div>
              {form.diagnosis_codes.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeDiagCode(idx)}
                  className="p-1.5 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-colors"
                  title="Remove code"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          ))}

          <button
            type="button"
            onClick={addDiagCode}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-lg transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Diagnosis Code
          </button>

          {errors.diagnosis_codes && (
            <p className="text-xs text-rose-600 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />{errors.diagnosis_codes}
            </p>
          )}
          <p className="text-[11px] text-slate-400">ICD-10-CM format. Multiple codes allowed (at least one required).</p>
        </div>
      </div>

      {/* ── Patient & Jurisdiction ────────────────────────────────────────────── */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
          <div className="p-1.5 rounded-lg bg-purple-50"><User className="w-4 h-4 text-purple-600" /></div>
          <h3 className="text-sm font-bold text-slate-800">Patient & Jurisdiction</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* State */}
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">
              <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5 text-purple-500" />Patient State</span>
            </label>
            <select
              value={form.state}
              onChange={(e) => set('state', e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 focus:outline-none bg-white text-slate-800 transition-colors"
            >
              <option value="">— Select state (optional) —</option>
              {US_STATES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <p className="mt-1 text-[11px] text-slate-400">Used for jurisdiction-based LCD lookup.</p>
          </div>

          {/* Patient Age */}
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">
              <span className="flex items-center gap-1"><User className="w-3.5 h-3.5 text-purple-500" />Patient Age (years)</span>
            </label>
            <input
              type="number"
              value={form.patient_age}
              onChange={(e) => set('patient_age', e.target.value)}
              placeholder="e.g. 55"
              min={0}
              max={130}
              className={`w-full px-3 py-2 text-sm rounded-lg border ${
                errors.patient_age ? 'border-rose-400 bg-rose-50/40' : 'border-slate-300 focus:border-purple-500'
              } focus:ring-2 focus:ring-purple-500/20 focus:outline-none text-slate-800 transition-colors`}
            />
            {errors.patient_age && (
              <p className="mt-1 text-xs text-rose-600">{errors.patient_age}</p>
            )}
            <p className="mt-1 text-[11px] text-slate-400">Optional. Contextual for age-related coverage criteria.</p>
          </div>
        </div>
      </div>

      {/* ── Service Date ────────────────────────────────────────────────────────── */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-3">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
          <div className="p-1.5 rounded-lg bg-teal-50"><Calendar className="w-4 h-4 text-teal-600" /></div>
          <h3 className="text-sm font-bold text-slate-800">Service Date</h3>
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">Date of Service</label>
          <input
            type="date"
            value={form.service_date}
            onChange={(e) => set('service_date', e.target.value)}
            className="px-3 py-2 text-sm rounded-lg border border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 focus:outline-none text-slate-800 transition-colors"
          />
          <p className="mt-1 text-[11px] text-slate-400">Used for policy effective date validation.</p>
        </div>
      </div>

      {/* ── Clinical Notes ────────────────────────────────────────────────────── */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-3">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
          <div className="p-1.5 rounded-lg bg-amber-50"><ClipboardList className="w-4 h-4 text-amber-600" /></div>
          <h3 className="text-sm font-bold text-slate-800">Clinical Notes</h3>
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">
            Clinical Documentation / Medical Justification
          </label>
          <textarea
            value={form.clinical_notes}
            onChange={(e) => set('clinical_notes', e.target.value)}
            placeholder="Describe the patient's clinical history, prior treatments, medical necessity, and supporting clinical evidence..."
            rows={5}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 focus:outline-none text-slate-800 leading-relaxed resize-y transition-colors"
          />
          <p className="mt-1 text-[11px] text-slate-400">
            Provide clinical context. This text is used by the semantic (Qwen) and agentic evaluation pipeline.
          </p>
        </div>
      </div>

      {/* ── Submit Bar ────────────────────────────────────────────────────────── */}
      <div className="sticky bottom-4 z-10">
        <div className="bg-white border border-slate-200 shadow-lg rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="text-xs text-slate-400 hidden sm:block">
            Submitting to <code className="font-mono text-sky-700">POST /api/v1/triage</code>
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3 rounded-xl bg-sky-600 hover:bg-sky-700 disabled:bg-sky-400 text-sm font-bold text-white shadow-sm transition-all"
          >
            {submitting ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Evaluating Policy...</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4" />
                <span>Submit for Policy Evaluation</span>
              </>
            )}
          </button>
        </div>
      </div>
    </form>
  );
}

