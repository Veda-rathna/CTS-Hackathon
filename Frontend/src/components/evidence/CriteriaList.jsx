import React from 'react';
import StatusBadge from '../common/StatusBadge';
import { CheckCircle, AlertTriangle, Shield, Check, X } from 'lucide-react';

export default function CriteriaList({ criteria = [] }) {
  if (!criteria || criteria.length === 0) {
    return (
      <div className="p-6 text-center text-xs text-slate-400 bg-slate-50/50 rounded-xl border border-slate-200/60">
        No specific policy criteria rules evaluated for this case.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {criteria.map((crit, idx) => {
        const isSatisfied =
          crit.status === 'SATISFIED' ||
          crit.status === 'MATCHED' ||
          crit.status === 'COVERED';

        return (
          <div
            key={crit.criterion_id || idx}
            className={`p-4 rounded-xl border transition-all ${
              isSatisfied
                ? 'bg-emerald-50/30 border-emerald-200/70'
                : 'bg-amber-50/30 border-amber-200/70'
            }`}
          >
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-slate-200/60">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-slate-700 bg-white px-2 py-0.5 rounded border border-slate-200">
                  {crit.criterion_id || `CRIT-${idx + 1}`}
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

            {/* Criterion statement */}
            <p className="mt-2.5 text-xs font-medium text-slate-800 leading-relaxed">
              {crit.criterion}
            </p>

            {/* Evidence comparison grid */}
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              {/* Patient Evidence */}
              <div className="p-2.5 rounded-lg bg-white/80 border border-slate-200/80">
                <span className="text-[11px] font-semibold text-slate-500 block mb-1">
                  Patient Clinical Evidence
                </span>
                {crit.patient_evidence && crit.patient_evidence.length > 0 ? (
                  <ul className="list-disc list-inside space-y-0.5 text-slate-700">
                    {crit.patient_evidence.map((pe, i) => (
                      <li key={i}>{pe}</li>
                    ))}
                  </ul>
                ) : (
                  <span className="text-slate-400 italic">No direct patient records referenced</span>
                )}
              </div>

              {/* Policy Evidence */}
              <div className="p-2.5 rounded-lg bg-white/80 border border-slate-200/80">
                <span className="text-[11px] font-semibold text-slate-500 block mb-1">
                  Policy Requirement Rule
                </span>
                {crit.policy_evidence && crit.policy_evidence.length > 0 ? (
                  <ul className="list-disc list-inside space-y-0.5 text-slate-700">
                    {crit.policy_evidence.map((pe, i) => (
                      <li key={i}>{pe}</li>
                    ))}
                  </ul>
                ) : (
                  <span className="text-slate-400 italic">Standard policy criteria</span>
                )}
              </div>
            </div>

            {/* Explanation */}
            {crit.explanation && (
              <p className="mt-2 text-[11px] text-slate-600 bg-slate-100/70 p-2 rounded border border-slate-200/40">
                <span className="font-semibold text-slate-700">Engine Evaluation: </span>
                {crit.explanation}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
