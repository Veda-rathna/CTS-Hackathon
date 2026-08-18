import React from 'react';
import { Zap, Clock, ShieldCheck, TrendingDown, ArrowRight, Sparkles } from 'lucide-react';

export default function ImpactMetricsSection({ compact = false }) {
  const metrics = [
    {
      id: 'policy_lookup',
      title: 'Policy Lookup & Synthesis',
      manual: '30 min',
      ai: '<30 sec',
      savings: '98% faster',
      icon: Zap,
      description: 'Automated Medicare LCD/NCD retrieval and criterion extraction vs. manual CMS manual lookup.',
    },
    {
      id: 'approval_cycle',
      title: 'Prior Auth Turnaround',
      manual: '1–2 days',
      ai: '<45 min',
      savings: '95% reduction',
      icon: Clock,
      description: 'End-to-end multi-agent clinical evaluation cycle vs. standard manual fax/review queues.',
    },
    {
      id: 'doc_defect_rate',
      title: 'Missing Documentation Rate',
      manual: '30%',
      ai: '5%',
      savings: '83% defect reduction',
      icon: TrendingDown,
      description: 'Instant missing item classification and prompt generation reduces provider rework cycles.',
    },
  ];

  return (
    <div className="healthcare-card p-4 sm:p-5 bg-white border border-slate-200/90 shadow-sm space-y-3.5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-slate-100">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-sky-50 text-sky-700 border border-sky-100">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
              Operational & Clinical Impact Metrics
            </h3>
            <p className="text-[11px] text-slate-500">
              Automated multi-agent efficiency vs. legacy manual prior authorization workflows
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 self-start sm:self-auto bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-700" />
          <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider">
            100% Policy Grounded
          </span>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {metrics.map((m) => {
          return (
            <div
              key={m.id}
              className="bg-slate-50/70 hover:bg-slate-50 border border-slate-200/90 rounded-xl p-3.5 flex flex-col justify-between space-y-2.5 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-800">{m.title}</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  {m.savings}
                </span>
              </div>

              {/* Before / After Bar */}
              <div className="flex items-center justify-between bg-white px-3 py-2 rounded-lg border border-slate-200/90 text-xs shadow-2xs">
                <div className="flex flex-col">
                  <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Manual</span>
                  <span className="font-mono font-medium text-slate-400 line-through text-[11px]">
                    {m.manual}
                  </span>
                </div>

                <ArrowRight className="w-3.5 h-3.5 text-sky-600 flex-shrink-0" />

                <div className="flex flex-col text-right">
                  <span className="text-[9px] font-bold text-sky-700 uppercase tracking-wider">AI Engine</span>
                  <span className="font-mono font-extrabold text-sky-900 text-xs">
                    {m.ai}
                  </span>
                </div>
              </div>

              {!compact && (
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  {m.description}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
