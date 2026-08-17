import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Award,
  Layers,
  FileCheck2,
  XCircle,
  HelpCircle,
} from 'lucide-react';
import { computeBatchSummary } from '../../utils/queueEngine';

export default function BatchSummaryCard({ items = [] }) {
  const summary = computeBatchSummary(items);
  if (summary.total === 0 || (summary.completed === 0 && summary.failed === 0)) {
    return null;
  }

  const isAllDone = summary.queued === 0 && summary.processing === 0;

  return (
    <div className="healthcare-card p-5 sm:p-6 bg-white space-y-5 border-emerald-200/90 shadow-sm animate-in fade-in duration-300">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
            <Award className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              {isAllDone ? 'Batch Evaluation Complete' : 'Batch Evaluation Progress Summary'}
            </h3>
            <p className="text-xs text-slate-500">
              Computed from {summary.completed + summary.failed} of {summary.total} evaluated prior authorization requests
            </p>
          </div>
        </div>

        <span className={`px-2.5 py-1 rounded-lg text-xs font-bold border ${
          isAllDone 
            ? 'bg-emerald-50 text-emerald-800 border-emerald-300' 
            : 'bg-sky-50 text-sky-800 border-sky-300'
        }`}>
          {isAllDone ? '100% Processed' : `${summary.completed + summary.failed} / ${summary.total} Processed`}
        </span>
      </div>

      {/* Primary KPI Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
        <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
            Total Requests
          </span>
          <span className="text-xl font-extrabold text-slate-900">{summary.total}</span>
        </div>

        <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-200">
          <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider block">
            Completed
          </span>
          <span className="text-xl font-extrabold text-emerald-800">{summary.completed}</span>
        </div>

        <div className="p-3 rounded-xl bg-rose-50/60 border border-rose-200">
          <span className="text-[10px] font-bold text-rose-800 uppercase tracking-wider block">
            Failed
          </span>
          <span className="text-xl font-extrabold text-rose-800">{summary.failed}</span>
        </div>

        <div className="p-3 rounded-xl bg-sky-50/60 border border-sky-200">
          <span className="text-[10px] font-bold text-sky-800 uppercase tracking-wider block">
            Remaining In Queue
          </span>
          <span className="text-xl font-extrabold text-sky-800">{summary.queued + summary.processing}</span>
        </div>
      </div>

      {/* Decision Distribution Breakdown */}
      <div className="space-y-2 pt-1 border-t border-slate-100">
        <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
          Authorization Decision Breakdown
        </span>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
          <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-900 border border-emerald-200 flex items-center justify-between">
            <span className="font-semibold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              Approved
            </span>
            <span className="font-extrabold font-mono text-sm">{summary.decisions.APPROVE}</span>
          </div>

          <div className="p-2.5 rounded-lg bg-purple-50 text-purple-900 border border-purple-200 flex items-center justify-between">
            <span className="font-semibold flex items-center gap-1">
              <Layers className="w-3.5 h-3.5 text-purple-600" />
              Pended
            </span>
            <span className="font-extrabold font-mono text-sm">{summary.decisions.PEND}</span>
          </div>

          <div className="p-2.5 rounded-lg bg-amber-50 text-amber-900 border border-amber-200 flex items-center justify-between">
            <span className="font-semibold flex items-center gap-1">
              <HelpCircle className="w-3.5 h-3.5 text-amber-600" />
              Need More Info
            </span>
            <span className="font-extrabold font-mono text-sm">{summary.decisions.NEED_MORE_INFORMATION}</span>
          </div>

          <div className="p-2.5 rounded-lg bg-rose-50 text-rose-900 border border-rose-200 flex items-center justify-between">
            <span className="font-semibold flex items-center gap-1">
              <XCircle className="w-3.5 h-3.5 text-rose-600" />
              Rejected
            </span>
            <span className="font-extrabold font-mono text-sm">{summary.decisions.REJECTED}</span>
          </div>
        </div>
      </div>

      {/* Priority Distribution Breakdown */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs">
        <span className="font-bold text-slate-700 uppercase tracking-wider text-[11px]">
          Batch Priority Mix:
        </span>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 font-semibold text-rose-700">
            <span className="w-2 h-2 rounded-full bg-rose-500" />
            Urgent: {summary.priorities.URGENT}
          </span>
          <span className="flex items-center gap-1 font-semibold text-amber-700">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            Medium: {summary.priorities.MEDIUM}
          </span>
          <span className="flex items-center gap-1 font-semibold text-slate-600">
            <span className="w-2 h-2 rounded-full bg-slate-400" />
            Low: {summary.priorities.LOW}
          </span>
        </div>
      </div>
    </div>
  );
}
