import React, { useState } from 'react';
import {
  BookOpen,
  Sparkles,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  ListFilter,
  FileText,
  Layers,
  Info,
} from 'lucide-react';

// Decodes HTML entities and normalizes whitespace
function cleanHtmlText(str) {
  if (!str) return '';
  return str
    .replace(/&rsquo;/g, "'")
    .replace(/&lsquo;/g, "'")
    .replace(/&rdquo;/g, '"')
    .replace(/&ldquo;/g, '"')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&nbsp;/g, ' ')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

// Parses raw CMS document text into structured points and background sections
function parseRagPassage(rawText) {
  const clean = cleanHtmlText(rawText);
  if (!clean) return { points: [], background: '', raw: '' };

  const points = [];
  let backgroundText = '';

  // Check for "Covered Indications" or specific criteria markers
  const coveredIdx = clean.search(/Covered Indications|Indications and Limitations|Coverage Guidance|Medically reasonable and necessary/i);
  
  if (coveredIdx !== -1) {
    backgroundText = clean.slice(0, coveredIdx).trim();
    const criteriaSection = clean.slice(coveredIdx).trim();

    // Sentence/clause splitting for criteria
    // Matches sentences starting with "The patient...", "The clinical diagnosis...", "If appropriate...", "A repeat series...", etc.
    const criteriaRegex = /(?:The patient (?:is|has)|The clinical diagnosis is|If appropriate,|Conservative therapy is defined as|A repeat series|Symptoms have recurred|At least \d+ months|There was significant|Viscosupplementation therapy for the knee|Several synthetic preparations)[^.]*\./gi;
    
    let match;
    const extractedCriteria = [];
    while ((match = criteriaRegex.exec(criteriaSection)) !== null) {
      const item = match[0].trim();
      if (item.length > 20) {
        extractedCriteria.push(item);
      }
    }

    if (extractedCriteria.length > 0) {
      extractedCriteria.forEach(c => points.push(c));
    } else {
      // Split on sentence boundaries
      criteriaSection.split(/(?<=[.!?])\s+/).forEach(s => {
        const trimmed = s.trim();
        if (trimmed.length > 25) points.push(trimmed);
      });
    }
  } else {
    // If no distinct "Covered Indications" header, split sentences into logical bullet points
    const sentences = clean.split(/(?<=[.!?])\s+/);
    sentences.forEach(s => {
      const trimmed = s.trim();
      if (trimmed.length > 20) {
        points.push(trimmed);
      }
    });
  }

  // Clean background narrative
  if (backgroundText) {
    backgroundText = backgroundText
      .replace(/^Compliance with the provisions.*?audits\.\s*/i, '')
      .replace(/^History\/Background and\/or General Information\s*/i, '')
      .trim();
  }

  return {
    points: points.filter(p => p.length > 15),
    background: backgroundText,
    raw: clean,
  };
}

export default function RagEvidenceSection({ ragEvidence = [] }) {
  const [expandedAll, setExpandedAll] = useState(false);
  const [viewModes, setViewModes] = useState({}); // { [idx]: 'points' | 'raw' }

  if (!ragEvidence || ragEvidence.length === 0) {
    return null;
  }

  const displayed = expandedAll ? ragEvidence : ragEvidence.slice(0, 3);

  const toggleViewMode = (idx) => {
    setViewModes(prev => ({
      ...prev,
      [idx]: prev[idx] === 'raw' ? 'points' : 'raw'
    }));
  };

  return (
    <div className="healthcare-card p-5 space-y-4 bg-white">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-700">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Semantic & RAG Policy References ({ragEvidence.length})
            </h3>
            <p className="text-[11px] text-slate-500">
              Retrieved CMS coverage text passages formatted for clinical policy evaluation
            </p>
          </div>
        </div>

        {ragEvidence.length > 3 && (
          <button
            type="button"
            onClick={() => setExpandedAll(!expandedAll)}
            className="flex items-center gap-1 px-2.5 py-1 text-xs font-bold text-indigo-800 bg-indigo-50 hover:bg-indigo-100 rounded-lg border border-indigo-200 transition-colors"
          >
            <span>{expandedAll ? 'Show Less' : `View All (${ragEvidence.length})`}</span>
            {expandedAll ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        )}
      </div>

      <div className="space-y-4">
        {displayed.map((item, idx) => {
          const scorePercent = item.similarity_score != null ? Math.round(item.similarity_score * 100) : null;
          const parsed = parseRagPassage(item.text || item.chunk_text);
          const isRawMode = viewModes[idx] === 'raw';

          return (
            <div
              key={idx}
              className="p-4 sm:p-5 rounded-xl bg-slate-50/70 border border-slate-200/90 hover:border-slate-300 transition-colors space-y-3 text-xs"
            >
              {/* Reference Header */}
              <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-slate-200/80">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-indigo-900 bg-white px-2.5 py-0.5 rounded border border-indigo-200">
                    {item.policy_type} {item.policy_id}
                  </span>
                  {item.section && (
                    <span className="text-[11px] font-bold text-slate-700 bg-slate-200/70 px-2 py-0.5 rounded">
                      Section: {item.section}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {scorePercent != null && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-mono font-bold text-indigo-800 bg-white px-2 py-0.5 rounded border border-indigo-200">
                      <Sparkles className="w-3 h-3 text-indigo-600" />
                      Relevance: {scorePercent}%
                    </span>
                  )}

                  <button
                    type="button"
                    onClick={() => toggleViewMode(idx)}
                    className="text-[10px] font-bold text-slate-500 hover:text-slate-800 bg-white px-2 py-0.5 rounded border border-slate-200 transition-colors"
                  >
                    {isRawMode ? 'Show Points View' : 'Show Source Text'}
                  </button>
                </div>
              </div>

              {item.policy_title && (
                <h4 className="font-bold text-slate-900 text-sm leading-snug">
                  {item.policy_title}
                </h4>
              )}

              {/* View Mode: Structured Points (Default) */}
              {!isRawMode ? (
                <div className="space-y-3">
                  {/* Coverage Criteria Points */}
                  {parsed.points.length > 0 && (
                    <div className="p-3.5 rounded-lg bg-white border border-slate-200/90 space-y-2">
                      <div className="flex items-center gap-1.5 pb-1.5 border-b border-slate-100">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
                        <span className="font-bold text-slate-800 text-[11px] uppercase tracking-wider">
                          Key CMS Coverage Criteria & Indications ({parsed.points.length} Requirements)
                        </span>
                      </div>

                      <ul className="space-y-2 text-xs text-slate-800">
                        {parsed.points.map((pt, pIdx) => (
                          <li key={pIdx} className="flex items-start gap-2 leading-relaxed">
                            <span className="inline-block w-4 h-4 rounded-full bg-emerald-50 text-emerald-800 text-[10px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5 border border-emerald-200">
                              {pIdx + 1}
                            </span>
                            <span className="text-slate-800">{pt}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Background & Context Paragraph (if present) */}
                  {parsed.background && (
                    <div className="p-3 rounded-lg bg-indigo-50/40 border border-indigo-100/80 space-y-1">
                      <div className="flex items-center gap-1">
                        <Info className="w-3 h-3 text-indigo-600" />
                        <span className="font-bold text-indigo-950 text-[11px] uppercase tracking-wider">
                          Clinical Background & Treatment Scope
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-700 leading-relaxed">
                        {parsed.background}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                /* View Mode: Full Raw Source Quote */
                <p className="text-xs text-slate-700 leading-relaxed italic bg-white p-3.5 rounded-lg border border-slate-200/90">
                  "{parsed.raw}"
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
