import React from 'react';
import { Zap, Clock, ShieldCheck, TrendingDown, ArrowRight, CheckCircle2, Sparkles } from 'lucide-react';

export default function ImpactMetricsSection({ compact = false }) {
  const metrics = [
    {
      id: 'policy_lookup',
      title: 'Policy Lookup & Synthesis',
      manual: '30 min',
      ai: '<30 sec',
      savings: '98% faster',
      icon: Zap,
      color: 'sky',
      description: 'Automated Medicare LCD/NCD retrieval and criterion extraction vs. manual CMS manual lookup.',
    },
    {
      id: 'approval_cycle',
      title: 'Prior Auth Turnaround',
      manual: '1–2 days',
      ai: '<45 min',
      savings: '95% reduction',
      icon: Clock,
      color: 'emerald',
      description: 'End-to-end multi-agent clinical evaluation cycle vs. standard manual fax/review queues.',
    },
    {
      id: 'doc_defect_rate',
      title: 'Missing Documentation Rate',
      manual: '30%',
      ai: '5%',
      savings: '83% defect reduction',
      icon: TrendingDown,
      color: 'indigo',
      description: 'Instant missing item classification and prompt generation reduces provider rework cycles.',
    },
  ];

  return (
    <div className="healthcare-card p-4 sm:p-5 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white shadow-md border-slate-700 overflow-hidden relative">
      {/* Background ambient lighting */}
      <div className="absolute -top-12 -right-12 w-48 h-48 bg-sky-500/10 rounded-full blur-2xl pointer-events-none" />
      <div className="absolute -bottom-12 -left-12 w-48 h-48 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-700/80 relative z-10">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-sky-500/20 text-sky-400 border border-sky-500/30">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-extrabold uppercase tracking-wider text-slate-200">
              Operational & Clinical Impact Metrics
            </h3>
            <p className="text-[11px] text-slate-400">
              Automated multi-agent efficiency vs. legacy manual prior authorization workflows
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 self-start sm:self-auto bg-slate-800/80 px-2.5 py-1 rounded-full border border-slate-700">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-[10px] font-bold text-slate-300 uppercase tracking-wider">
            100% Policy Grounded
          </span>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-3.5 relative z-10">
        {metrics.map((m) => {
          const Icon = m.icon;
          return (
            <div
              key={m.id}
              className="bg-slate-800/90 hover:bg-slate-800 border border-slate-700/90 rounded-xl p-3.5 flex flex-col justify-between space-y-2.5 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-300">{m.title}</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                  {m.savings}
                </span>
              </div>

              {/* Before / After Bar */}
              <div className="flex items-center justify-between bg-slate-900/90 px-3 py-2 rounded-lg border border-slate-700/60 text-xs">
                <div className="flex flex-col">
                  <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">Manual</span>
                  <span className="font-mono font-semibold text-slate-400 line-through text-[11px]">
                    {m.manual}
                  </span>
                </div>

                <ArrowRight className="w-3.5 h-3.5 text-sky-400 flex-shrink-0" />

                <div className="flex flex-col text-right">
                  <span className="text-[9px] font-bold text-sky-400 uppercase tracking-wider">AI Engine</span>
                  <span className="font-mono font-extrabold text-sky-300 text-xs">
                    {m.ai}
                  </span>
                </div>
              </div>

              {!compact && (
                <p className="text-[10px] text-slate-400 leading-relaxed">
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
