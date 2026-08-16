import React from 'react';
import { Scale, CheckCircle2, XCircle, HelpCircle, ShieldCheck } from 'lucide-react';

export default function EvidenceFusionPanel({ fusionResult, criteria = [], decisionBasis }) {
  if (!fusionResult && (!criteria || criteria.length === 0)) {
    return null;
  }

  // Count criteria statuses
  const satisfiedCount = criteria.filter((c) => (c.status || '').toUpperCase() === 'SATISFIED').length;
  const notSatisfiedCount = criteria.filter((c) => (c.status || '').toUpperCase() === 'NOT_SATISFIED').length;
  const unknownCount = criteria.filter((c) => (c.status || '').toUpperCase() === 'UNKNOWN').length;

  const resultNorm = (fusionResult || '').toUpperCase();

  let fusionConfig = {
    label: fusionResult || 'EVALUATED',
    bg: 'bg-slate-50',
    border: 'border-slate-300',
    text: 'text-slate-700',
  };

  if (resultNorm === 'COVERED') {
    fusionConfig = { label: 'COVERED — All Mandatory Criteria Satisfied', bg: 'bg-emerald-50', border: 'border-emerald-300', text: 'text-emerald-800' };
  } else if (resultNorm === 'EXCLUDED') {
    fusionConfig = { label: 'EXCLUDED — Non-Covered Policy Exclusions Triggered', bg: 'bg-rose-50', border: 'border-rose-300', text: 'text-rose-800' };
  } else if (resultNorm === 'NOT_ADDRESSED') {
    fusionConfig = { label: 'NOT ADDRESSED — Requirements Require Additional Documentation', bg: 'bg-amber-50', border: 'border-amber-300', text: 'text-amber-800' };
  }

  return (
    <div className="healthcare-card p-5 space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-teal-50 text-teal-600">
            <Scale className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Evidence Fusion Engine Consolidation
            </h3>
            <p className="text-[11px] text-slate-500">
              Deterministic priority ladder: SQL (Rule) &gt; LLM (Semantic)
            </p>
          </div>
        </div>
      </div>

      {/* Fusion Banner */}
      <div className={`p-4 rounded-xl border ${fusionConfig.bg} ${fusionConfig.border} flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs`}>
        <div className="space-y-0.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
            Fused Evidence Evaluation Result
          </span>
          <span className={`text-sm font-extrabold font-mono ${fusionConfig.text}`}>
            {fusionConfig.label}
          </span>
        </div>

        {/* Criteria Breakdown Pill Counters */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-100/70 text-emerald-800 font-bold text-xs">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            {satisfiedCount} Satisfied
          </span>
          {notSatisfiedCount > 0 && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-100/70 text-rose-800 font-bold text-xs">
              <XCircle className="w-3.5 h-3.5 text-rose-600" />
              {notSatisfiedCount} Not Satisfied
            </span>
          )}
          {unknownCount > 0 && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-200/80 text-slate-700 font-medium text-xs">
              <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
              {unknownCount} Pending
            </span>
          )}
        </div>
      </div>

      {/* Decision Basis Narrative */}
      {decisionBasis && (
        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1 text-xs">
          <span className="font-bold text-slate-700 block">Adjudication Chain Basis:</span>
          <p className="text-slate-600 leading-relaxed italic">{decisionBasis}</p>
        </div>
      )}
    </div>
  );
}
