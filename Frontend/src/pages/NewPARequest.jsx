import React, { useState } from 'react';
import { UploadCloud, FileEdit, Info } from 'lucide-react';
import PDFUploader from '../components/pa/PDFUploader';
import ManualPAForm from '../components/pa/ManualPAForm';

export default function NewPARequest() {
  const [activeMethod, setActiveMethod] = useState('manual'); // 'pdf' | 'manual'

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Create Prior Authorization Request
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Submit patient clinical documentation via digital PDF upload or structured schema form
          </p>
        </div>

        {/* Input Method Switcher */}
        <div className="inline-flex p-1 bg-slate-200/80 rounded-xl border border-slate-300/80 self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setActiveMethod('pdf')}
            className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-bold rounded-lg transition-all ${
              activeMethod === 'pdf'
                ? 'bg-white text-sky-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
            }`}
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload PDF</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveMethod('manual')}
            className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-bold rounded-lg transition-all ${
              activeMethod === 'manual'
                ? 'bg-white text-sky-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
            }`}
          >
            <FileEdit className="w-4 h-4" />
            <span>Manual Form</span>
          </button>
        </div>
      </div>

      {/* Primary Workflow Container */}
      <div className="transition-all duration-300">
        {activeMethod === 'pdf' ? (
          <div className="space-y-4">
            <div className="p-4 bg-sky-50/70 border border-sky-200 rounded-xl flex items-start gap-3 text-xs text-sky-900">
              <Info className="w-4 h-4 text-sky-600 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold block">PDF Processing Workflow:</span>
                Upload a clinical PA PDF document. The ingestion pipeline extracts the procedure, diagnosis codes, and patient context for policy evaluation.
              </div>
            </div>
            <PDFUploader />
          </div>
        ) : (
          <ManualPAForm />
        )}
      </div>
    </div>
  );
}
