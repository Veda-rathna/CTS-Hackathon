import React, { useState } from 'react';
import { BookOpen, Sparkles, ChevronDown, ChevronUp, FileText } from 'lucide-react';

export default function RagEvidenceSection({ ragEvidence = [] }) {
  const [expanded, setExpanded] = useState(false);

  if (!ragEvidence || ragEvidence.length === 0) {
    return null;
  }

  const displayed = expanded ? ragEvidence : ragEvidence.slice(0, 3);

  return (
    <div className="healthcare-card p-5 space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Semantic & RAG Policy References ({ragEvidence.length})
            </h3>
            <p className="text-[11px] text-slate-500">
              Retrieved CMS text passages evaluated against patient record
            </p>
          </div>
        </div>

        {ragEvidence.length > 3 && (
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors"
          >
            <span>{expanded ? 'Show Less' : `View All (${ragEvidence.length})`}</span>
            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        )}
      </div>

      <div className="space-y-3">
        {displayed.map((item, idx) => {
          const scorePercent = item.similarity_score != null ? Math.round(item.similarity_score * 100) : null;

          return (
            <div
              key={idx}
              className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/80 hover:border-slate-300 transition-colors space-y-2 text-xs"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-indigo-800 bg-white px-2 py-0.5 rounded border border-indigo-200">
                    {item.policy_type} {item.policy_id}
                  </span>
                  {item.section && (
                    <span className="text-[11px] font-semibold text-slate-600">
                      Section: {item.section}
                    </span>
                  )}
                </div>

                {scorePercent != null && (
                  <span className="inline-flex items-center gap-1 text-[10px] font-mono font-bold text-indigo-700 bg-white px-2 py-0.5 rounded border border-indigo-200">
                    <Sparkles className="w-3 h-3 text-indigo-500" />
                    Relevance: {scorePercent}%
                  </span>
                )}
              </div>

              {item.policy_title && (
                <h4 className="font-bold text-slate-900 text-xs">{item.policy_title}</h4>
              )}

              <p className="text-slate-700 leading-relaxed italic bg-white p-3 rounded-lg border border-slate-200/60">
                "{item.text || item.chunk_text}"
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
