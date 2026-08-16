import React from 'react';
import StatusBadge from '../common/StatusBadge';
import { CheckCircle2, XCircle, HelpCircle, FileText } from 'lucide-react';

export default function CriteriaList({ criteria = [] }) {
  if (!criteria || criteria.length === 0) {
    return (
      <div className="p-6 text-center text-xs text-slate-400 bg-slate-50/50 rounded-xl border border-slate-200/60">
        No specific policy criteria evaluated for this request.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {criteria.map((crit, idx) => {
        const isSatisfied = crit.status === 'SATISFIED' || crit.status === 'MATCHED' || crit.status === 'COVERED';
        const isNotSatisfied = crit.status === 'NOT_SATISFIED' || crit.status === 'EXCLUDED' || crit.status === 'NOT_COVERED';
        const isUnknown = !isSatisfied && !isNotSatisfied;

        const requirementText = crit.requirement || crit.criterion;

        return (
          <div
            key={crit.criterion_id || idx}
            className={`p-4 rounded-xl border transition-all ${
              isSatisfied
                ? 'bg-emerald-50/30 border-emerald-200/80'
                : isNotSatisfied
                ? 'bg-rose-50/30 border-rose-200/80'
                : 'bg-amber-50/30 border-amber-200/80'
            }`}
          >
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-slate-200/60">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-slate-700 bg-white px-2 py-0.5 rounded border border-slate-200">
                  {crit.criterion_id || `REQ-${idx + 1}`}
                </span>
                <span className="text-xs font-semibold text-slate-800">
                  {crit.policy_type} {crit.policy_id}
                </span>
                {crit.mandatory && (
                  <span className="text-[10px] font-bold text-rose-600 bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                    Mandatory
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                {crit.evaluator && (
                  <span className="text-[10px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                    Evaluator: {crit.evaluator}
                  </span>
                )}
                <StatusBadge status={crit.status} size="xs" />
              </div>
            </div>

            {/* Requirement statement */}
            <p className="mt-2.5 text-xs font-semibold text-slate-900 leading-relaxed">
              {requirementText}
            </p>

            {/* Evidence comparison grid */}
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              {/* Clinical Evidence */}
              <div className="p-2.5 rounded-lg bg-white/90 border border-slate-200/80">
                <span className="text-[11px] font-bold text-slate-600 block mb-1">
                  Relevant Clinical Evidence
                </span>
                {crit.evidence && crit.evidence.length > 0 ? (
                  <ul className="space-y-1 text-slate-700">
                    {crit.evidence.map((ev, i) => (
                      <li key={i} className="text-[11px]">
                        <span className="font-medium text-slate-800">{ev.text}</span>
                        {ev.source && ev.source !== 'Patient Clinical Record' && (
                          <span className="text-[10px] text-slate-400 block">Source: {ev.source}</span>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : crit.patient_evidence && crit.patient_evidence.length > 0 ? (
                  <ul className="list-disc list-inside space-y-0.5 text-slate-700">
                    {crit.patient_evidence.map((pe, i) => (
                      <li key={i}>{pe}</li>
                    ))}
                  </ul>
                ) : (
                  <span className="text-slate-400 italic text-[11px]">
                    No relevant clinical documentation found in patient record
                  </span>
                )}
              </div>

              {/* Policy Rule */}
              <div className="p-2.5 rounded-lg bg-white/90 border border-slate-200/80">
                <span className="text-[11px] font-bold text-slate-600 block mb-1">
                  Policy Rule Specification
                </span>
                {crit.policy_evidence && crit.policy_evidence.length > 0 ? (
                  <ul className="list-disc list-inside space-y-0.5 text-slate-700">
                    {crit.policy_evidence.map((pe, i) => (
                      <li key={i}>{pe}</li>
                    ))}
                  </ul>
                ) : (
                  <span className="text-slate-400 italic text-[11px]">Standard Medicare coverage requirement</span>
                )}
              </div>
            </div>

            {/* Explanation */}
            {crit.explanation && (
              <div className="mt-2.5 text-[11px] text-slate-700 bg-slate-50 p-2.5 rounded-lg border border-slate-200/60">
                <span className="font-semibold text-slate-900">Clinical Evaluation: </span>
                <span>{crit.explanation}</span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

