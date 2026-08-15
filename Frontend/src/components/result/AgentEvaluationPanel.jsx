import React, { useState } from 'react';
import { Bot, ChevronDown, ChevronUp, CheckCircle2, AlertTriangle, ShieldCheck, Cpu } from 'lucide-react';

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
    <div className="healthcare-card p-5 space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-purple-50 text-purple-600">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Agentic Semantic Evaluation Pipeline ({agenticCriteria.length})
            </h3>
            <p className="text-[11px] text-slate-500">
              4-Agent Orchestration: PolicyAgent &rarr; ClinicalEvidenceAgent &rarr; EvaluationAgent &rarr; Qwen &rarr; CriticAgent
            </p>
          </div>
        </div>

        <span className="text-[10px] font-mono font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
          Qwen3-4B + Critic Guard
        </span>
      </div>

      <div className="space-y-3">
        {agenticCriteria.map((crit, idx) => {
          const key = crit.criterion_id || idx;
          const isOpen = openItems[key] ?? true;

          // Parse Agent Trace lines from explanation if available
          const traceLines = (crit.explanation || '')
            .split('\n')
            .filter((l) => l.trim().startsWith('[') || l.includes('Agent]'));

          return (
            <div key={key} className="rounded-xl border border-purple-200/80 overflow-hidden bg-white">
              {/* Collapsible Header */}
              <button
                type="button"
                onClick={() => toggleItem(key)}
                className="w-full p-4 bg-purple-50/40 hover:bg-purple-50/70 transition-colors flex items-center justify-between text-left gap-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-purple-800 bg-white px-2 py-0.5 rounded border border-purple-200">
                      {crit.criterion_id}
                    </span>
                    <span className="text-xs font-semibold text-slate-800">
                      {crit.policy_type} {crit.policy_id}
                    </span>
                    <span className="text-[10px] font-bold text-purple-700 bg-purple-100/70 px-2 py-0.5 rounded">
                      AGENTIC_QWEN
                    </span>
                  </div>
                  <p className="text-xs font-medium text-slate-700 line-clamp-1">
                    {crit.criterion}
                  </p>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                    crit.status === 'SATISFIED'
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : crit.status === 'NOT_SATISFIED'
                      ? 'bg-rose-50 text-rose-700 border border-rose-200'
                      : 'bg-slate-100 text-slate-600'
                  }`}>
                    {crit.status}
                  </span>
                  {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                </div>
              </button>

              {/* Panel Content */}
              {isOpen && (
                <div className="p-4 space-y-4 border-t border-purple-100 text-xs">
                  {/* Evidence Comparison Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {/* Patient Evidence */}
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                      <span className="font-bold text-slate-700 block text-[11px] uppercase tracking-wider">
                        Patient Record Evidence (Clinical Evidence Agent)
                      </span>
                      {crit.patient_evidence && crit.patient_evidence.length > 0 ? (
                        <ul className="list-disc list-inside space-y-1 text-slate-700">
                          {crit.patient_evidence.map((pe, i) => (
                            <li key={i}>{pe}</li>
                          ))}
                        </ul>
                      ) : (
                        <span className="text-slate-400 italic">No specific patient statements cited</span>
                      )}
                    </div>

                    {/* Policy Evidence */}
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                      <span className="font-bold text-slate-700 block text-[11px] uppercase tracking-wider">
                        Policy Requirements (Policy Agent)
                      </span>
                      {crit.policy_evidence && crit.policy_evidence.length > 0 ? (
                        <ul className="list-disc list-inside space-y-1 text-slate-700">
                          {crit.policy_evidence.map((pe, i) => (
                            <li key={i}>{pe}</li>
                          ))}
                        </ul>
                      ) : (
                        <span className="text-slate-400 italic">Standard policy requirement</span>
                      )}
                    </div>
                  </div>

                  {/* Agent Trace Timeline */}
                  {traceLines.length > 0 && (
                    <div className="space-y-1.5 p-3 rounded-lg bg-purple-950 text-purple-100 font-mono text-[11px] overflow-x-auto">
                      <span className="font-sans font-bold text-purple-300 block mb-1 uppercase tracking-wider text-[10px]">
                        Agent Execution Audit Log
                      </span>
                      {traceLines.map((line, lIdx) => (
                        <div key={lIdx} className="leading-tight py-0.5 border-b border-purple-800/40 last:border-none">
                          {line}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Explanation Narrative */}
                  {crit.explanation && (
                    <div className="p-3 rounded-lg bg-slate-100 text-slate-700 space-y-1">
                      <span className="font-bold text-slate-800 block text-[11px]">
                        Critic-Validated Conclusion:
                      </span>
                      <p className="leading-relaxed">{crit.explanation.split('Agent Trace:')[0]}</p>
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
