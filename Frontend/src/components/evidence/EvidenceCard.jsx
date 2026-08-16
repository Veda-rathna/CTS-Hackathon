import React from 'react';
import StatusBadge from '../common/StatusBadge';
import { FileCheck, ShieldCheck, MapPin, Hash, BookOpen } from 'lucide-react';

export default function EvidenceCard({ evidence }) {
  const { type, identifier, code, state, result, explanation } = evidence;

  const getTypeIcon = () => {
    switch ((type || '').toUpperCase()) {
      case 'HCPCS':
      case 'CPT':
        return <Hash className="w-4 h-4 text-sky-600" />;
      case 'ICD10':
      case 'ICD-10':
        return <FileCheck className="w-4 h-4 text-emerald-600" />;
      case 'JURISDICTION':
        return <MapPin className="w-4 h-4 text-purple-600" />;
      case 'ARTICLE':
      case 'POLICY_DATE':
      default:
        return <BookOpen className="w-4 h-4 text-amber-600" />;
    }
  };

  return (
    <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-2xs hover:border-slate-300 transition-all space-y-2.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-slate-100">{getTypeIcon()}</div>
          <div>
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              {type || 'EVIDENCE'}
            </span>
            {identifier && (
              <span className="ml-2 text-[11px] font-mono font-medium text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                {identifier}
              </span>
            )}
          </div>
        </div>

        <StatusBadge status={result} size="sm" />
      </div>

      {/* Code / Context Display */}
      {(code || state) && (
        <div className="flex items-center gap-2 text-xs font-mono">
          {code && (
            <span className="px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-100 font-semibold">
              Code: {code}
            </span>
          )}
          {state && (
            <span className="px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-100 font-semibold">
              State: {state}
            </span>
          )}
        </div>
      )}

      {/* Explanation */}
      {explanation && (
        <p className="text-xs text-slate-600 leading-relaxed bg-slate-50/70 p-2.5 rounded-lg border border-slate-100">
          {explanation}
        </p>
      )}
    </div>
  );
}
