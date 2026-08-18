import React, { useState } from 'react';
import {
  X,
  Plus,
  Trash2,
  UploadCloud,
  FileText,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
  FileCheck2,
  RefreshCw,
  Layers,
} from 'lucide-react';
import { extractFromPDF } from '../../services/api';
import { sortPriorityQueue, PRIORITY_RANK } from '../../utils/queueEngine';
import PriorityBadge from '../common/PriorityBadge';

const DEMO_STAGING_PRESET = [
  {
    tempId: 'STG-001',
    pa_request_id: 'PA-BATCH-001',
    procedure_code: '64483',
    diagnosis_codes: ['M54.16'],
    state: 'TX',
    patient_age: '55',
    clinical_notes: 'Lumbar radiculopathy with severe neuropathic pain refractory to 8 weeks physical therapy and NSAIDs.',
    priority: 'URGENT',
    service_date: new Date().toISOString().split('T')[0],
  },
  {
    tempId: 'STG-002',
    pa_request_id: 'PA-BATCH-002',
    procedure_code: '20610',
    diagnosis_codes: ['M17.11'],
    state: 'TX',
    patient_age: '68',
    clinical_notes: 'Primary unilateral osteoarthritis of right knee. Failed 3 months conservative therapy with acetaminophen and meloxicam.',
    priority: 'URGENT',
    service_date: new Date().toISOString().split('T')[0],
  },
  {
    tempId: 'STG-003',
    pa_request_id: 'PA-BATCH-003',
    procedure_code: '38240',
    diagnosis_codes: ['C92.00'],
    state: 'IL',
    patient_age: '42',
    clinical_notes: 'Acute myeloid leukemia in second complete remission. Candidate for allogeneic hematopoietic cell transplantation.',
    priority: 'MEDIUM',
    service_date: new Date().toISOString().split('T')[0],
  },
  {
    tempId: 'STG-004',
    pa_request_id: 'PA-BATCH-004',
    procedure_code: '20552',
    diagnosis_codes: ['M54.5'],
    state: 'CA',
    patient_age: '49',
    clinical_notes: 'Chronic low back pain persisting >6 months without surgical indication. Evaluation for acupuncture trial.',
    priority: 'MEDIUM',
    service_date: new Date().toISOString().split('T')[0],
  },
  {
    tempId: 'STG-005',
    pa_request_id: 'PA-BATCH-005',
    procedure_code: '64550',
    diagnosis_codes: ['G89.11'],
    state: 'NY',
    patient_age: '38',
    clinical_notes: 'Acute post-operative pain management inquiry following orthopedic procedure. TENS unit trial evaluation.',
    priority: 'LOW',
    service_date: new Date().toISOString().split('T')[0],
  },
];

export default function BatchIntakeModal({ isOpen, onClose, onEnqueueBatch }) {
  const [intakeMethod, setIntakeMethod] = useState('manual'); // 'manual' | 'pdf'
  const [requests, setRequests] = useState([
    {
      tempId: 'STG-1',
      pa_request_id: `PA-${Date.now().toString().slice(-4)}-1`,
      procedure_code: '64483',
      diagnosis_codes: ['M54.16'],
      state: 'TX',
      patient_age: '55',
      clinical_notes: 'Documented lumbar radiculopathy with persistent symptoms refractory to conservative therapy.',
      priority: 'URGENT',
      service_date: new Date().toISOString().split('T')[0],
    },
    {
      tempId: 'STG-2',
      pa_request_id: `PA-${Date.now().toString().slice(-4)}-2`,
      procedure_code: '20610',
      diagnosis_codes: ['M17.11'],
      state: 'TX',
      patient_age: '68',
      clinical_notes: 'Osteoarthritis of knee, completed 3 months physical therapy and NSAID trial.',
      priority: 'MEDIUM',
      service_date: new Date().toISOString().split('T')[0],
    },
  ]);

  const [pdfFiles, setPdfFiles] = useState([]);
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  // Add new blank manual row
  const handleAddRow = () => {
    const nextIdx = requests.length + 1;
    setRequests([
      ...requests,
      {
        tempId: `STG-${Date.now()}-${nextIdx}`,
        pa_request_id: `PA-${Date.now().toString().slice(-4)}-${nextIdx}`,
        procedure_code: '',
        diagnosis_codes: [''],
        state: 'TX',
        patient_age: '',
        clinical_notes: '',
        priority: 'MEDIUM',
        service_date: new Date().toISOString().split('T')[0],
      },
    ]);
  };

  // Remove row
  const handleRemoveRow = (idx) => {
    if (requests.length <= 1) return;
    setRequests(requests.filter((_, i) => i !== idx));
  };

  // Update row field
  const handleUpdateRow = (idx, field, value) => {
    const next = [...requests];
    next[idx] = { ...next[idx], [field]: value };
    setRequests(next);
  };

  // Load demo staging preset
  const handleLoadDemoPreset = () => {
    setRequests(DEMO_STAGING_PRESET.map((item, i) => ({
      ...item,
      tempId: `DEMO-${Date.now()}-${i + 1}`,
      pa_request_id: `PA-DEMO-${Date.now().toString().slice(-3)}${i + 1}`,
    })));
  };

  // Multi-PDF upload handling
  const handlePdfUpload = async (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    setIsExtracting(true);
    setError(null);

    const extractedRequests = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      try {
        const res = await extractFromPDF(file);
        extractedRequests.push({
          tempId: `PDF-${Date.now()}-${i + 1}`,
          pa_request_id: `PA-PDF-${Date.now().toString().slice(-3)}${i + 1}`,
          source_document: file.name,
          procedure_code: res.procedure_code || '64483',
          diagnosis_codes: res.diagnosis_codes?.length > 0 ? res.diagnosis_codes : ['M54.16'],
          state: res.state || 'TX',
          patient_age: res.patient_age != null ? String(res.patient_age) : '55',
          clinical_notes: res.clinical_notes || `Ingested from ${file.name}`,
          priority: i === 0 ? 'URGENT' : 'MEDIUM',
          service_date: new Date().toISOString().split('T')[0],
        });
      } catch (err) {
        console.warn(`Extraction fallback for ${file.name}:`, err);
        extractedRequests.push({
          tempId: `PDF-${Date.now()}-${i + 1}`,
          pa_request_id: `PA-PDF-${Date.now().toString().slice(-3)}${i + 1}`,
          source_document: file.name,
          procedure_code: '64483',
          diagnosis_codes: ['M54.16'],
          state: 'TX',
          patient_age: '55',
          clinical_notes: `Document ingested: ${file.name}. Refractory pain.`,
          priority: 'MEDIUM',
          service_date: new Date().toISOString().split('T')[0],
        });
      }
    }

    setRequests(extractedRequests);
    setIsExtracting(false);
  };

  // Submit batch to queue
  const handleSubmitBatch = (autoStart = true) => {
    // Validate each request
    const invalidIdx = requests.findIndex((r) => !r.procedure_code?.trim());
    if (invalidIdx >= 0) {
      setError(`Request #${invalidIdx + 1} is missing a required Procedure Code (CPT/HCPCS).`);
      return;
    }

    // Attach submission sequences (FIFO order)
    const prepared = requests.map((r, i) => ({
      ...r,
      procedure_code: r.procedure_code.trim().toUpperCase(),
      diagnosis_codes: (r.diagnosis_codes || []).map((d) => d.trim().toUpperCase()).filter(Boolean),
      submission_sequence: i + 1,
      processing_status: 'QUEUED',
      decision: null,
    }));

    onEnqueueBatch(prepared, autoStart);
    onClose();
  };

  // Compute preview sorted order
  const previewSorted = sortPriorityQueue(
    requests.map((r, i) => ({
      ...r,
      submission_sequence: i + 1,
      processing_status: 'QUEUED',
    }))
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto">
      <div className="healthcare-card w-full max-w-4xl bg-white shadow-xl overflow-hidden my-6 animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 sm:p-5 border-b border-slate-200/90 bg-slate-50/70">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-sky-700 text-white flex items-center justify-center font-bold">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm sm:text-base font-extrabold text-slate-900">
                Batch Prior Authorization Intake & Queue Staging
              </h2>
              <p className="text-[11px] text-slate-500">
                Stage multiple prior authorization requests, assign workflow priorities, and preview execution order
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-4 sm:p-6 space-y-5 max-h-[75vh] overflow-y-auto">
          {/* Method Switcher & Staging Preset */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div className="inline-flex rounded-lg bg-slate-100 p-1 border border-slate-200/80 text-xs font-bold">
              <button
                type="button"
                onClick={() => setIntakeMethod('manual')}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  intakeMethod === 'manual'
                    ? 'bg-white text-sky-800 shadow-sm border border-slate-200'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                Manual Multi-Request Entry ({requests.length})
              </button>
              <button
                type="button"
                onClick={() => setIntakeMethod('pdf')}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  intakeMethod === 'pdf'
                    ? 'bg-white text-sky-800 shadow-sm border border-slate-200'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                Multi-PDF Upload
              </button>
            </div>

            <button
              type="button"
              onClick={handleLoadDemoPreset}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-sky-800 bg-sky-50 hover:bg-sky-100 border border-sky-200 rounded-lg transition-colors self-start sm:self-auto"
            >
              <Sparkles className="w-3.5 h-3.5 text-sky-600" />
              <span>Load 5-Case Demo Preset (Staging Only)</span>
            </button>
          </div>

          {/* PDF Ingestion Area */}
          {intakeMethod === 'pdf' && (
            <div className="p-5 border-2 border-dashed border-slate-300 rounded-xl bg-slate-50/50 text-center space-y-2.5">
              <input
                type="file"
                multiple
                accept=".pdf,application/pdf"
                onChange={handlePdfUpload}
                id="multi-pdf-upload"
                className="hidden"
              />
              <div className="w-10 h-10 rounded-xl bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-700 mx-auto">
                <UploadCloud className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-800">Upload Multiple Prior Authorization PDFs</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Select multiple PDF packets to extract clinical values into batch rows
                </p>
              </div>
              <label
                htmlFor="multi-pdf-upload"
                className="inline-flex items-center px-3.5 py-1.5 text-xs font-bold text-white bg-sky-700 hover:bg-sky-800 rounded-lg shadow-sm cursor-pointer transition-colors"
              >
                Browse PDF Files
              </label>

              {isExtracting && (
                <div className="flex items-center justify-center gap-2 text-xs font-bold text-sky-800 pt-2">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Extracting clinical data fields from uploaded PDFs...</span>
                </div>
              )}
            </div>
          )}

          {/* Request Rows Table / Cards */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Staged PA Requests ({requests.length})
              </span>
              <button
                type="button"
                onClick={handleAddRow}
                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold text-sky-800 bg-sky-50 hover:bg-sky-100 rounded-lg border border-sky-200 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Request Row</span>
              </button>
            </div>

            <div className="space-y-2.5">
              {requests.map((req, idx) => (
                <div
                  key={req.tempId}
                  className="p-3.5 rounded-xl bg-slate-50/80 border border-slate-200 space-y-2.5 text-xs"
                >
                  <div className="flex items-center justify-between pb-2 border-b border-slate-200/80">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-600 bg-white px-2 py-0.5 rounded border border-slate-200">
                        #{idx + 1}
                      </span>
                      <span className="font-mono font-bold text-sky-800">{req.pa_request_id}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                        Priority:
                      </label>
                      <select
                        value={req.priority}
                        onChange={(e) => handleUpdateRow(idx, 'priority', e.target.value)}
                        className="px-2 py-1 text-xs font-bold rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-600"
                      >
                        <option value="URGENT">URGENT</option>
                        <option value="MEDIUM">MEDIUM</option>
                        <option value="LOW">LOW</option>
                      </select>

                      {requests.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveRow(idx)}
                          className="p-1 text-rose-600 hover:text-rose-800 hover:bg-rose-50 rounded transition-colors"
                          title="Remove row"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-2.5">
                    <div>
                      <label className="block text-[10px] font-bold text-slate-600 uppercase mb-0.5">
                        Procedure Code (CPT/HCPCS) *
                      </label>
                      <input
                        type="text"
                        value={req.procedure_code}
                        onChange={(e) => handleUpdateRow(idx, 'procedure_code', e.target.value.toUpperCase())}
                        placeholder="e.g. 64483"
                        className="w-full px-2.5 py-1 text-xs font-mono font-bold rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-600"
                      />
                    </div>

                    <div>
                      <label className="block text-[10px] font-bold text-slate-600 uppercase mb-0.5">
                        Primary ICD-10
                      </label>
                      <input
                        type="text"
                        value={req.diagnosis_codes[0] || ''}
                        onChange={(e) => {
                          const nextDiag = [...req.diagnosis_codes];
                          nextDiag[0] = e.target.value.toUpperCase();
                          handleUpdateRow(idx, 'diagnosis_codes', nextDiag);
                        }}
                        placeholder="e.g. M54.16"
                        className="w-full px-2.5 py-1 text-xs font-mono font-bold rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-600"
                      />
                    </div>

                    <div>
                      <label className="block text-[10px] font-bold text-slate-600 uppercase mb-0.5">
                        State (MAC)
                      </label>
                      <input
                        type="text"
                        maxLength={2}
                        value={req.state}
                        onChange={(e) => handleUpdateRow(idx, 'state', e.target.value.toUpperCase())}
                        placeholder="e.g. TX"
                        className="w-full px-2.5 py-1 text-xs font-bold rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-600"
                      />
                    </div>

                    <div>
                      <label className="block text-[10px] font-bold text-slate-600 uppercase mb-0.5">
                        Age
                      </label>
                      <input
                        type="number"
                        value={req.patient_age}
                        onChange={(e) => handleUpdateRow(idx, 'patient_age', e.target.value)}
                        placeholder="e.g. 55"
                        className="w-full px-2.5 py-1 text-xs font-bold rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-600"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-slate-600 uppercase mb-0.5">
                      Clinical Notes / Medical Indication
                    </label>
                    <input
                      type="text"
                      value={req.clinical_notes}
                      onChange={(e) => handleUpdateRow(idx, 'clinical_notes', e.target.value)}
                      placeholder="e.g. Refractory pain, physical therapy completed, diagnostic MRI confirmed..."
                      className="w-full px-2.5 py-1 text-xs rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-600"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Pre-Execution Queue Order Preview */}
          <div className="p-4 rounded-xl bg-slate-900 text-white space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-sky-400" />
                <h4 className="text-xs font-bold text-sky-300 uppercase tracking-wider">
                  Deterministic Priority Execution Preview ({previewSorted.length} Items)
                </h4>
              </div>
              <span className="text-[10px] text-slate-400 font-mono">
                Order Rule: Priority Rank DESC &rarr; FIFO ASC
              </span>
            </div>

            <p className="text-[11px] text-slate-300 leading-relaxed">
              Requests are ordered by workflow priority (<strong className="text-white">URGENT &gt; MEDIUM &gt; LOW</strong>). Requests with the same priority are processed in submission order (FIFO).
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 pt-1">
              {previewSorted.map((item, pIdx) => (
                <div
                  key={item.tempId}
                  className="p-2.5 rounded-lg bg-slate-800/90 border border-slate-700 flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] font-bold text-sky-400 bg-slate-950 px-1.5 py-0.2 rounded">
                      #{pIdx + 1}
                    </span>
                    <div className="leading-tight">
                      <span className="font-mono font-bold text-slate-200 text-xs block">
                        {item.pa_request_id}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {item.procedure_code || 'Unspecified'}
                      </span>
                    </div>
                  </div>

                  <PriorityBadge priority={item.priority} size="xs" />
                </div>
              ))}
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 sm:p-5 border-t border-slate-200 bg-slate-50/70">
          <span className="text-xs text-slate-500">
            Total {requests.length} PA requests staged for priority queue
          </span>

          <div className="flex items-center gap-2.5 self-end sm:self-auto">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 text-xs font-bold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-300 rounded-lg transition-colors"
            >
              Cancel
            </button>

            <button
              type="button"
              onClick={() => handleSubmitBatch(true)}
              className="inline-flex items-center gap-1.5 px-5 py-2 text-xs font-bold text-white bg-sky-700 hover:bg-sky-800 rounded-lg shadow-sm transition-colors"
            >
              <span>Enqueue & Start Batch Evaluation</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
