import React from 'react';
import { formatDate } from '../../utils/formatters';
import { BookOpen, MapPin, Calendar, CheckCircle2, ArrowRight, ExternalLink } from 'lucide-react';

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
    LCD: 'bg-sky-50 text-sky-700 border-sky-200',
    NCD: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    ARTICLE: 'bg-teal-50 text-teal-700 border-teal-200',
  }[policy_type?.toUpperCase()] || 'bg-slate-100 text-slate-700 border-slate-200';

  return (
    <div className="healthcare-card p-5 healthcare-card-hover flex flex-col justify-between space-y-4">
      <div className="space-y-3">
        {/* Type & ID Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={`px-2.5 py-0.5 rounded-md text-xs font-bold font-mono border ${typeColor}`}>
              {policy_type} {policy_id}
            </span>
            {jurisdiction_id && (
              <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200 flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                <span>{jurisdiction_id}</span>
              </span>
            )}
          </div>

          <span
            className={`px-2 py-0.5 rounded-full text-[11px] font-semibold border ${
              effective
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-slate-100 text-slate-600 border-slate-200'
            }`}
          >
            {effective ? 'Active Policy' : 'Expired'}
          </span>
        </div>

        {/* Title */}
        <h4 className="text-sm font-semibold text-slate-900 leading-snug">
          {title || 'CMS Medicare Coverage Policy Document'}
        </h4>

        {/* Association */}
        {article_id && (
          <div className="text-xs text-slate-500 flex items-center gap-1.5 font-mono">
            <span>Related Article:</span>
            <span className="font-semibold text-sky-700 bg-sky-50 px-1.5 py-0.2 rounded border border-sky-200">
              {article_id}
            </span>
          </div>
        )}

        {/* Dates */}
        <div className="flex items-center gap-4 text-xs text-slate-500 pt-1">
          <div className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            <span>Effective: {formatDate(effective_date)}</span>
          </div>
          {end_date && (
            <div className="flex items-center gap-1 text-slate-400">
              <span>End: {formatDate(end_date)}</span>
            </div>
          )}
        </div>

        {/* Match indicators */}
        <div className="flex flex-wrap gap-1.5 pt-2 border-t border-slate-100 text-[11px]">
          {procedure_match && (
            <span className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium">
              ✓ Procedure Matched
            </span>
          )}
          {diagnosis_match && (
            <span className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium">
              ✓ Diagnosis Matched
            </span>
          )}
          {jurisdiction_match && (
            <span className="px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 font-medium">
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
          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-sky-700 hover:text-sky-800 bg-sky-50 hover:bg-sky-100 rounded-lg border border-sky-200 transition-colors"
        >
          <span>Inspect Coverage Details</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
