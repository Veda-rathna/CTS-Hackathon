import React, { useState } from 'react';
import { UploadCloud, FileEdit, Info, Sparkles, CheckCircle2, ShieldCheck, Zap } from 'lucide-react';
import PDFUploader from '../components/pa/PDFUploader';
import ManualPAForm from '../components/pa/ManualPAForm';

export default function NewPARequest() {
  const [activeMethod, setActiveMethod] = useState('manual'); // 'manual' | 'pdf'

  return (
    <div className="space-y-6">
      {/* Page Title & Tab Switcher Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-sky-700 bg-sky-50 px-2 py-0.5 rounded-full border border-sky-200">
              Clinical Intake & Evaluation
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight mt-1">
            Prior Authorization Intake
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Submit clinical data for real-time CMS Medicare coverage policy adjudication
          </p>
        </div>

        {/* Segmented Control Switcher */}
        <div className="inline-flex p-1 bg-slate-100/90 rounded-2xl border border-slate-200/80 self-start sm:self-auto shadow-2xs">
          <button
            type="button"
            onClick={() => setActiveMethod('manual')}
            className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-bold rounded-xl transition-all ${
              activeMethod === 'manual'
                ? 'bg-white text-sky-700 shadow-sm border border-slate-200/60'
                : 'text-slate-500 hover:text-slate-800 hover:bg-white/50'
            }`}
          >
            <FileEdit className="w-4 h-4 text-sky-600" />
            <span>Structured Intake Form</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveMethod('pdf')}
            className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-bold rounded-xl transition-all ${
              activeMethod === 'pdf'
                ? 'bg-white text-sky-700 shadow-sm border border-slate-200/60'
                : 'text-slate-500 hover:text-slate-800 hover:bg-white/50'
            }`}
          >
            <UploadCloud className="w-4 h-4 text-sky-600" />
            <span>Upload PDF Document</span>
          </button>
        </div>
      </div>

      {/* Feature Guidance Banner */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-sky-50/70 via-white to-indigo-50/50 border border-sky-100 flex items-start gap-3 text-xs text-slate-700 shadow-2xs">
        <div className="p-2 rounded-xl bg-sky-100/80 text-sky-700 flex-shrink-0 mt-0.5">
          <Sparkles className="w-4 h-4" />
        </div>
        <div className="space-y-0.5">
          <span className="font-bold text-slate-900 block">
            {activeMethod === 'manual'
              ? 'Interactive Prior Authorization Form'
              : 'Automated PDF Extraction & Ingestion'}
          </span>
          <p className="text-slate-600 text-[11px] leading-relaxed">
            {activeMethod === 'manual'
              ? 'Enter procedure and diagnosis codes along with patient state and clinical notes. The deterministic rule engine evaluates SQL code logic and routes complex criteria through the 4-agent semantic evaluator.'
              : 'Upload a prior authorization PDF document. The ingestion pipeline extracts code identifiers, state, and medical documentation for human verification prior to evaluation.'}
          </p>
        </div>
      </div>

      {/* Main Workflow Form / Uploader */}
      <div className="transition-all duration-300">
        {activeMethod === 'manual' ? (
          <ManualPAForm />
        ) : (
          <PDFUploader />
        )}
      </div>
    </div>
  );
}
