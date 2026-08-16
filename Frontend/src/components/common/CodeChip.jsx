import React from 'react';

export default function CodeChip({ code, type = 'CPT', description, mappingRequired = false }) {
  if (!code && !mappingRequired) {
    return <span className="text-slate-400 italic text-xs">Unspecified</span>;
  }

  const typeStyles = {
    CPT: 'bg-sky-50 text-sky-700 border-sky-200',
    HCPCS: 'bg-cyan-50 text-cyan-700 border-cyan-200',
    'ICD-10': 'bg-emerald-50 text-emerald-700 border-emerald-200',
    'ICD-10-CM': 'bg-emerald-50 text-emerald-700 border-emerald-200',
    'SNOMED-CT': 'bg-purple-50 text-purple-700 border-purple-200',
    MAPPING_REQUIRED: 'bg-amber-50 text-amber-700 border-amber-200',
  }[type] || 'bg-slate-100 text-slate-700 border-slate-200';

  if (mappingRequired || !code) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-medium bg-amber-50 text-amber-700 border border-amber-200">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
        Mapping Required
      </span>
    );
  }

  return (
    <div className="inline-flex items-center gap-1.5" title={description || `${type}: ${code}`}>
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-semibold border ${typeStyles}`}
      >
        {code}
      </span>
      {description && (
        <span className="text-xs text-slate-500 truncate max-w-[200px]" title={description}>
          {description}
        </span>
      )}
    </div>
  );
}
