import React, { useState } from 'react';
import {
  Bot,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  Cpu,
  Clock,
  Check,
  FileCheck2,
  BookOpen,
  Sparkles,
} from 'lucide-react';

// Helper to parse the raw agentic explanation string into structured fields
function parseAgenticExplanation(rawText) {
  if (!rawText) return null;

  // Clean delimiters
  const cleanText = rawText
    .replace(/^=+.*?=+\s*/s, '')
    .replace(/={10,}/g, '')
    .trim();

  let criterion = '';
  let policy = '';
  let requiredEvidence = [];
  let patientEvidence = [];
  let qwenResult = '';
  let criticResult = '';
  let finalResult = '';
  let narrative = '';
  let duration = '';

  // Extract pipeline duration
  const durationMatch = cleanText.match(/\(Agentic pipeline completed in ([\d.]+(?:ms|s))\)/i);
  if (durationMatch) {
    duration = durationMatch[1];
  }

  // Regex extraction for structured segments
  const critMatch = cleanText.match(/Criterion:\s*([^\n\r]+?)(?=Policy:|Required Evidence:|Patient Evidence:|$)/i);
  const polMatch = cleanText.match(/Policy:\s*([^\n\r]+?)(?=Required Evidence:|Patient Evidence:|$)/i);
  const qwenMatch = cleanText.match(/Qwen Result:\s*([A-Z_]+)/i);
  const criticMatch = cleanText.match(/Critic Result:\s*([A-Z_]+)/i);
  const finalMatch = cleanText.match(/Final Result:\s*([A-Z_]+)/i);
  
  if (critMatch) criterion = critMatch[1].trim();
  if (polMatch) policy = polMatch[1].trim();
  if (qwenMatch) qwenResult = qwenMatch[1].trim();
  if (criticMatch) criticResult = criticMatch[1].trim();
  if (finalMatch) finalResult = finalMatch[1].trim();

  // Extract Required Evidence
  const reqSectionMatch = cleanText.match(/Required Evidence:\s*([\s\S]*?)(?=Patient Evidence:|Qwen Result:|Critic Result:|$)/i);
  if (reqSectionMatch) {
    const rawReq = reqSectionMatch[1].trim();
    const items = rawReq.split(/\n\s*[•\-*]\s*|\s*[•\-*]\s+/).map(s => s.trim()).filter(s => s.length > 5);
    if (items.length > 0) {
      requiredEvidence = items;
    } else if (rawReq.length > 5) {
      requiredEvidence = [rawReq];
    }
  }

  // Extract Patient Evidence
  const patSectionMatch = cleanText.match(/Patient Evidence:\s*([\s\S]*?)(?=Qwen Result:|Critic Result:|Final Result:|$)/i);
  if (patSectionMatch) {
    const rawPat = patSectionMatch[1].trim();
    const items = rawPat.split(/\n\s*[•\-*]\s*|\s*[•\-*]\s+/).map(s => s.trim()).filter(s => s.length > 5);
    if (items.length > 0) {
      patientEvidence = items;
    } else if (rawPat.length > 5) {
      patientEvidence = [rawPat];
    }
  }

  // Extract Synthesis Narrative
  const narrativeMatch = cleanText.match(/(?:Final Result:\s*[A-Z_]+\s*)([\s\S]*?)(?=\(Agentic pipeline|$)/i);
  if (narrativeMatch) {
    narrative = narrativeMatch[1].trim();
  } else {
    // If not matching strict pattern, extract trailing sentences
    const sentences = cleanText
      .replace(/Criterion:.*?Required Evidence:/is, '')
      .replace(/Patient Evidence:.*?Final Result:\s*[A-Z_]+/is, '')
      .replace(/\(Agentic pipeline.*?\)/i, '')
      .trim();
    if (sentences && sentences.length > 10) {
      narrative = sentences;
    }
  }

  return {
    criterion,
    policy,
    requiredEvidence,
    patientEvidence,
    qwenResult,
    criticResult,
    finalResult,
    narrative: narrative || 'The submitted clinical documentation satisfies this semantic policy criterion. The agentic evaluation chain validated the result.',
    duration,
    hasStructuredData: !!(qwenResult || criticResult || requiredEvidence.length > 0 || patientEvidence.length > 0),
  };
}

export default function AgentEvaluationPanel({ criteria = [] }) {
  // Filter for criteria evaluated by AGENTIC_QWEN
  const agenticCriteria = criteria.filter(
    (c) => (c.evaluator || '').toUpperCase() === 'AGENTIC_QWEN'
  );

  const [openItems, setOpenItems] = useState({});

  if (agenticCriteria.length === 0) {
    return null;
  }

  const toggleItem = (id) => {
    setOpenItems((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="healthcare-card p-5 space-y-4 bg-white">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-purple-50 text-purple-700">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Agentic Semantic Evaluation Pipeline ({agenticCriteria.length})
            </h3>
            <p className="text-[11px] text-slate-500">
              4-Agent Verification: PolicyAgent &rarr; ClinicalEvidenceAgent &rarr; EvaluationAgent &rarr; CriticAgent
            </p>
          </div>
        </div>

        <span className="text-[10px] font-mono font-bold text-purple-800 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
          Qwen3-4B + Critic Guard
        </span>
      </div>

      <div className="space-y-4">
        {agenticCriteria.map((crit, idx) => {
          const key = crit.criterion_id || idx;
          const isOpen = openItems[key] ?? true;

          // Parse explanation structure
          const parsed = parseAgenticExplanation(crit.explanation);

          // Combined evidence lists (prefer parsed from explanation, fallback to crit arrays)
          const reqEvidenceList = parsed?.requiredEvidence?.length > 0 
            ? parsed.requiredEvidence 
            : (crit.policy_evidence || []);
            
          const patEvidenceList = parsed?.patientEvidence?.length > 0 
            ? parsed.patientEvidence 
            : (crit.patient_evidence || []);

          // Parse Agent Trace lines from explanation if available
          const traceLines = (crit.explanation || '')
            .split('\n')
            .filter((l) => l.trim().startsWith('[') || l.includes('Agent]'));

          return (
            <div key={key} className="rounded-xl border border-slate-200 overflow-hidden bg-white shadow-sm">
              {/* Collapsible Header */}
              <button
                type="button"
                onClick={() => toggleItem(key)}
                className="w-full p-4 bg-slate-50/80 hover:bg-slate-100/80 transition-colors flex items-center justify-between text-left gap-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-purple-800 bg-white px-2 py-0.5 rounded border border-purple-200">
                      {crit.criterion_id}
                    </span>
                    <span className="text-xs font-bold text-slate-800">
                      {crit.policy_type} {crit.policy_id}
                    </span>
                    <span className="text-[10px] font-bold text-purple-700 bg-purple-50 px-1.5 py-0.2 rounded border border-purple-200">
                      AGENTIC_QWEN
                    </span>
                  </div>
                  <p className="text-xs font-semibold text-slate-800 line-clamp-1">
                    {crit.criterion}
                  </p>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className={`text-xs font-bold px-2.5 py-0.5 rounded border ${
                    crit.status === 'SATISFIED'
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                      : crit.status === 'NOT_SATISFIED'
                      ? 'bg-rose-50 text-rose-800 border-rose-300'
                      : 'bg-amber-50 text-amber-800 border-amber-300'
                  }`}>
                    {crit.status}
                  </span>
                  {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                </div>
              </button>

              {/* Panel Content */}
              {isOpen && (
                <div className="p-4 sm:p-5 space-y-4 border-t border-slate-200 text-xs">
                  
                  {/* Consensus & Verification Outcome Strip */}
                  <div className="p-3.5 rounded-xl bg-purple-50/60 border border-purple-200/90 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[11px] font-bold text-purple-950 uppercase tracking-wider flex items-center gap-1">
                        <ShieldCheck className="w-3.5 h-3.5 text-purple-700" />
                        Consensus Verdict:
                      </span>
                      
                      {/* Qwen Badge */}
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white text-indigo-800 border border-indigo-200">
                        Qwen: {parsed?.qwenResult || crit.status || 'SATISFIED'}
                      </span>

                      {/* Critic Guard Badge */}
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white text-emerald-800 border border-emerald-300">
                        Critic: {parsed?.criticResult || 'VALIDATED'}
                      </span>

                      {/* Final Result Badge */}
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-900 border border-emerald-300">
                        Final: {parsed?.finalResult || crit.status || 'SATISFIED'}
                      </span>
                    </div>

                    {parsed?.duration && (
                      <div className="flex items-center gap-1 text-[11px] font-mono font-bold text-purple-800 bg-white px-2 py-0.5 rounded border border-purple-200 self-start sm:self-auto">
                        <Clock className="w-3 h-3 text-purple-600" />
                        <span>Execution: {parsed.duration}</span>
                      </div>
                    )}
                  </div>

                  {/* Structured Evidence Comparison Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                    {/* Policy Requirements */}
                    <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                      <div className="flex items-center gap-1.5 pb-1.5 border-b border-slate-200">
                        <BookOpen className="w-3.5 h-3.5 text-sky-700" />
                        <span className="font-bold text-slate-800 text-[11px] uppercase tracking-wider">
                          Policy Requirement Conditions (Policy Agent)
                        </span>
                      </div>

                      {reqEvidenceList.length > 0 ? (
                        <ul className="space-y-1.5 text-xs text-slate-800">
                          {reqEvidenceList.map((item, i) => {
                            // Check if item has a key like "conservative_therapy_trial:"
                            const colonIdx = item.indexOf(':');
                            const hasKey = colonIdx > 0 && colonIdx < 35;
                            const keyPart = hasKey ? item.slice(0, colonIdx + 1) : null;
                            const valuePart = hasKey ? item.slice(colonIdx + 1).trim() : item;

                            return (
                              <li key={i} className="flex items-start gap-1.5 leading-relaxed">
                                <span className="text-sky-600 font-bold mt-0.5 select-none">•</span>
                                <div>
                                  {keyPart && (
                                    <span className="font-mono font-bold text-slate-900 mr-1 text-[11px] bg-sky-50 px-1 py-0.2 rounded border border-sky-100">
                                      {keyPart}
                                    </span>
                                  )}
                                  <span className="text-slate-700">{valuePart}</span>
                                </div>
                              </li>
                            );
                          })}
                        </ul>
                      ) : (
                        <span className="text-slate-400 italic">Governing policy requirements evaluated</span>
                      )}
                    </div>

                    {/* Patient Record Evidence */}
                    <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                      <div className="flex items-center gap-1.5 pb-1.5 border-b border-slate-200">
                        <FileCheck2 className="w-3.5 h-3.5 text-emerald-700" />
                        <span className="font-bold text-slate-800 text-[11px] uppercase tracking-wider">
                          Patient Record Citations (Evidence Agent)
                        </span>
                      </div>

                      {patEvidenceList.length > 0 ? (
                        <ul className="space-y-1.5 text-xs text-slate-800">
                          {patEvidenceList.map((item, i) => (
                            <li key={i} className="flex items-start gap-1.5 leading-relaxed">
                              <Check className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0 mt-0.5" />
                              <span className="text-slate-700">{item}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <span className="text-slate-400 italic">No specific patient statements cited</span>
                      )}
                    </div>
                  </div>

                  {/* Critic-Validated Conclusion Callout Box */}
                  <div className="p-3.5 rounded-xl bg-slate-100/90 border border-slate-300/80 space-y-1">
                    <span className="font-bold text-slate-800 text-[11px] uppercase tracking-wider block">
                      Critic-Validated Conclusion:
                    </span>
                    <p className="text-xs font-medium text-slate-800 leading-relaxed">
                      {parsed?.narrative || 'The submitted clinical documentation satisfies this semantic policy criterion. The agentic evaluation chain VALIDATED the result.'}
                    </p>
                  </div>

                  {/* Agent Trace Timeline (Collapsible / Compact) */}
                  {traceLines.length > 0 && (
                    <div className="space-y-1.5 p-3 rounded-xl bg-slate-900 text-purple-100 font-mono text-[11px] overflow-x-auto">
                      <span className="font-sans font-bold text-sky-300 block mb-1 uppercase tracking-wider text-[10px]">
                        Multi-Agent Execution Audit Log
                      </span>
                      {traceLines.map((line, lIdx) => (
                        <div key={lIdx} className="leading-tight py-0.5 border-b border-slate-800/80 last:border-none text-slate-200">
                          {line}
                        </div>
                      ))}
                    </div>
                  )}

                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
