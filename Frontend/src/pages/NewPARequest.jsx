import React, { useState } from 'react';
import { UploadCloud, FileEdit, ShieldCheck } from 'lucide-react';
import PDFUploader from '../components/pa/PDFUploader';
import ManualPAForm from '../components/pa/ManualPAForm';

export default function NewPARequest() {
  const [activeMethod, setActiveMethod] = useState('manual'); // 'manual' | 'pdf'

  return (
    <div className="space-y-5">
      {/* Page Title & Tab Switcher Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200/90">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
              Prior Authorization Intake
            </h2>
            <span className="text-[10px] font-bold uppercase tracking-wider text-sky-800 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
              Clinical Review
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Submit clinical case data for real-time CMS Medicare coverage policy adjudication
          </p>
        </div>

        {/* Segmented Control Switcher */}
        <div className="inline-flex p-1 bg-slate-100 rounded-lg border border-slate-200 self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setActiveMethod('manual')}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-md transition-all ${
              activeMethod === 'manual'
                ? 'bg-white text-sky-800 shadow-sm border border-slate-200'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            <FileEdit className="w-3.5 h-3.5 text-sky-700" />
            <span>Structured Intake Form</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveMethod('pdf')}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-md transition-all ${
              activeMethod === 'pdf'
                ? 'bg-white text-sky-800 shadow-sm border border-slate-200'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            <UploadCloud className="w-3.5 h-3.5 text-sky-700" />
            <span>Upload PDF Document</span>
          </button>
        </div>
      </div>

      {/* Feature Guidance Banner */}
      <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 flex items-start gap-2.5 text-xs text-slate-700">
        <div className="p-1 rounded bg-sky-50 text-sky-700 border border-sky-100 flex-shrink-0 mt-0.5">
          <ShieldCheck className="w-3.5 h-3.5" />
        </div>
        <div className="space-y-0.5">
          <span className="font-bold text-slate-900 block">
            {activeMethod === 'manual'
              ? 'Structured Prior Authorization Intake'
              : 'Automated PDF Document Ingestion'}
          </span>
          <p className="text-slate-500 text-[11px] leading-relaxed">
            {activeMethod === 'manual'
              ? 'Enter procedure and diagnosis codes along with patient state and clinical notes. Deterministic SQL rules match CMS policy criteria and orchestrate agentic validation.'
              : 'Upload a prior authorization clinical packet. The ingestion pipeline extracts code identifiers, patient state, and clinical text for verification prior to evaluation.'}
          </p>
        </div>
      </div>

      {/* Main Workflow Form / Uploader */}
      <div className="transition-all duration-200">
        {activeMethod === 'manual' ? (
          <ManualPAForm />
        ) : (
          <PDFUploader />
        )}
      </div>
    </div>
  );
}
