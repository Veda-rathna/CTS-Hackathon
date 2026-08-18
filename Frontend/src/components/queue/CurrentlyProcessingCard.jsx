import React from 'react';
import { RefreshCw, Activity, MapPin, User, Clock, AlertCircle } from 'lucide-react';
import PriorityBadge from '../common/PriorityBadge';

export default function CurrentlyProcessingCard({ activeItem }) {
  if (!activeItem) return null;

  return (
    <div className="healthcare-card p-4 sm:p-5 bg-gradient-to-r from-sky-50/70 via-white to-slate-50 border border-sky-200 shadow-sm space-y-3.5 animate-in fade-in duration-200">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-sky-100">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-sky-600 text-white flex items-center justify-center">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          </div>
          <div>
            <span className="text-[10px] font-bold text-sky-800 uppercase tracking-wider block">
              Currently Processing Request
            </span>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-mono font-extrabold text-slate-900">
                {activeItem.pa_request_id}
              </h3>
              <PriorityBadge priority={activeItem.priority} size="xs" />
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-[11px] font-semibold text-sky-800 bg-sky-100/70 px-2.5 py-1 rounded-lg border border-sky-200">
          <Activity className="w-3.5 h-3.5 text-sky-600" />
          <span>Active In Single-Request Evaluation Engine</span>
        </div>
      </div>

      {/* Clinical Context Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
        <div className="p-2.5 rounded-lg bg-white border border-slate-200 space-y-0.5">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
            Requested Procedure
          </span>
          <span className="font-mono font-bold text-xs text-sky-900">
            {activeItem.procedure_code || 'Unspecified'}
          </span>
        </div>

        <div className="p-2.5 rounded-lg bg-white border border-slate-200 space-y-0.5">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
            Primary Indication (ICD-10)
          </span>
          <span className="font-mono font-bold text-xs text-slate-800 truncate block">
            {(activeItem.diagnosis_codes || []).join(', ') || 'Unspecified'}
          </span>
        </div>

        <div className="p-2.5 rounded-lg bg-white border border-slate-200 space-y-0.5">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
            Beneficiary & State
          </span>
          <span className="font-semibold text-xs text-slate-700 flex items-center gap-1">
            <User className="w-3 h-3 text-slate-400" />
            <span>Age {activeItem.patient_age || 'N/A'}</span>
            <span className="text-slate-300">•</span>
            <MapPin className="w-3 h-3 text-purple-600" />
            <span>{activeItem.state || 'TX'}</span>
          </span>
        </div>
      </div>

      {/* Live Processing Notice */}
      <div className="p-2.5 rounded-lg bg-sky-50/80 border border-sky-100 text-xs text-sky-900 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-sky-600 animate-pulse" />
          <span className="font-medium">
            Evaluating clinical evidence against CMS Medicare coverage policies via <code className="font-bold text-sky-800">POST /api/v1/triage</code>...
          </span>
        </div>
        <span className="text-[10px] text-slate-500 font-mono hidden sm:inline">
          Sequential lock active
        </span>
      </div>
    </div>
  );
}
