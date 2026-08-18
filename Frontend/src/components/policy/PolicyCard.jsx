import React from 'react';
import { formatDate } from '../../utils/formatters';
import { MapPin, Calendar, ArrowRight } from 'lucide-react';

export default function PolicyCard({ policy, onSelect }) {
  const {
    policy_type,
    policy_id,
    title,
    article_id,
    jurisdiction_id,
    effective_date,
    end_date,
    procedure_match,
    diagnosis_match,
    jurisdiction_match,
    effective,
  } = policy;

  const typeColor = {
    LCD: 'bg-sky-50 text-sky-800 border-sky-200',
    NCD: 'bg-indigo-50 text-indigo-800 border-indigo-200',
    ARTICLE: 'bg-teal-50 text-teal-800 border-teal-200',
  }[policy_type?.toUpperCase()] || 'bg-slate-100 text-slate-700 border-slate-200';

  return (
    <div className="healthcare-card p-4 sm:p-5 bg-white flex flex-col justify-between space-y-3.5">
      <div className="space-y-2.5">
        {/* Type & ID Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className={`px-2 py-0.5 rounded text-[11px] font-bold font-mono border ${typeColor}`}>
              {policy_type} {policy_id}
            </span>
            {jurisdiction_id && (
              <span className="px-1.5 py-0.5 rounded text-[11px] font-bold bg-slate-100 text-slate-700 border border-slate-200 flex items-center gap-1">
                <MapPin className="w-3 h-3 text-purple-600" />
                <span>{jurisdiction_id}</span>
              </span>
            )}
          </div>

          <span
            className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
              effective
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-slate-100 text-slate-600 border-slate-200'
            }`}
          >
            {effective ? 'Active Policy' : 'Expired'}
          </span>
        </div>

        {/* Title */}
        <h4 className="text-xs sm:text-sm font-bold text-slate-900 leading-snug">
          {title || 'CMS Medicare Coverage Policy Document'}
        </h4>

        {/* Association */}
        {article_id && (
          <div className="text-[11px] text-slate-500 flex items-center gap-1.5 font-mono">
            <span>Related Article:</span>
            <span className="font-bold text-sky-800 bg-sky-50 px-1.5 py-0.2 rounded border border-sky-200">
              {article_id}
            </span>
          </div>
        )}

        {/* Dates */}
        <div className="flex items-center gap-3 text-[11px] text-slate-500 pt-0.5">
          <div className="flex items-center gap-1">
            <Calendar className="w-3 h-3 text-slate-400" />
            <span>Effective: {formatDate(effective_date)}</span>
          </div>
          {end_date && (
            <div className="flex items-center gap-1 text-slate-400">
              <span>End: {formatDate(end_date)}</span>
            </div>
          )}
        </div>

        {/* Match indicators */}
        <div className="flex flex-wrap gap-1 pt-1.5 border-t border-slate-100 text-[10px]">
          {procedure_match && (
            <span className="px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold">
              ✓ Procedure Matched
            </span>
          )}
          {diagnosis_match && (
            <span className="px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold">
              ✓ Diagnosis Matched
            </span>
          )}
          {jurisdiction_match && (
            <span className="px-1.5 py-0.2 rounded bg-purple-50 text-purple-800 border border-purple-200 font-bold">
              ✓ Jurisdiction Valid
            </span>
          )}
        </div>
      </div>

      {/* Action button */}
      <div className="pt-2 border-t border-slate-100 flex justify-end">
        <button
          type="button"
          onClick={() => onSelect(policy)}
          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold text-sky-700 hover:text-sky-800 bg-sky-50 hover:bg-sky-100 rounded-lg border border-sky-200 transition-colors"
        >
          <span>Coverage Details</span>
          <ArrowRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}
