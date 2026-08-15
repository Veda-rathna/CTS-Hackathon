import React from 'react';
import { Network, ArrowRight, CheckCircle2, XCircle, AlertCircle, HelpCircle } from 'lucide-react';

export default function PolicyPathDisplay({ policyPath, policies = [] }) {
  if (!policyPath && (!policies || policies.length === 0)) {
    return null;
  }

  // Calculate nodes from policy_path or fallback to policies list
  const ncdNode = policyPath?.ncd || policies.find((p) => (p.policy_type || '').toUpperCase() === 'NCD');
  const jurNode = policyPath?.jurisdiction;
  const lcdNode = policyPath?.lcd || policies.find((p) => (p.policy_type || '').toUpperCase() === 'LCD');
  const artNode = policyPath?.article || policies.find((p) => (p.policy_type || '').toUpperCase() === 'ARTICLE' || p.article_id);

  const getStatusBadge = (res) => {
    const val = (res || '').toUpperCase();
    if (val === 'COVERED' || val === 'MATCHED' || val === 'SATISFIED') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
          <CheckCircle2 className="w-3 h-3" /> COVERED
        </span>
      );
    }
    if (val === 'EXCLUDED' || val === 'NOT_SATISFIED') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
          <XCircle className="w-3 h-3" /> EXCLUDED
        </span>
      );
    }
    if (val === 'UNKNOWN' || val === 'NOT_ADDRESSED') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
          <HelpCircle className="w-3 h-3" /> NOT ADDRESSED
        </span>
      );
    }
    return null;
  };

  return (
    <div className="healthcare-card p-5 space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-sky-50 text-sky-600">
            <Network className="w-4 h-4" />
          </div>
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Governing CMS Policy Resolution Path
          </h3>
        </div>
        <span className="text-[11px] text-slate-400 font-medium">Policy Hierarchy Ladder</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        {/* NCD Node */}
        <div className={`p-3.5 rounded-xl border space-y-1.5 ${ncdNode ? 'bg-sky-50/40 border-sky-200' : 'bg-slate-50/50 border-slate-200/60 opacity-60'}`}>
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              National Policy (NCD)
            </span>
            {ncdNode && getStatusBadge(ncdNode.result)}
          </div>
          {ncdNode ? (
            <div>
              <span className="text-xs font-mono font-bold text-sky-800 block">
                {ncdNode.policy_id || ncdNode.id || 'NCD'}
              </span>
              <p className="text-[11px] text-slate-700 font-medium line-clamp-2 leading-snug">
                {ncdNode.title || ncdNode.name || 'National Coverage Determination'}
              </p>
            </div>
          ) : (
            <span className="text-xs text-slate-400 italic">No NCD matched</span>
          )}
        </div>

        {/* Jurisdiction Node */}
        <div className={`p-3.5 rounded-xl border space-y-1.5 ${jurNode ? 'bg-purple-50/40 border-purple-200' : 'bg-slate-50/50 border-slate-200/60 opacity-60'}`}>
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Jurisdiction (MAC)
            </span>
            {jurNode && getStatusBadge(jurNode.result)}
          </div>
          {jurNode ? (
            <div>
              <span className="text-xs font-mono font-bold text-purple-800 block">
                {jurNode.jurisdiction_id || jurNode.state || 'MAC'}
              </span>
              <p className="text-[11px] text-slate-700 font-medium line-clamp-2 leading-snug">
                {jurNode.contractor_name || `Jurisdiction ${jurNode.jurisdiction_id || ''}`}
              </p>
            </div>
          ) : (
            <span className="text-xs text-slate-400 italic">National scope</span>
          )}
        </div>

        {/* LCD Node */}
        <div className={`p-3.5 rounded-xl border space-y-1.5 ${lcdNode ? 'bg-teal-50/40 border-teal-200' : 'bg-slate-50/50 border-slate-200/60 opacity-60'}`}>
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Local Policy (LCD)
            </span>
            {lcdNode && getStatusBadge(lcdNode.result)}
          </div>
          {lcdNode ? (
            <div>
              <span className="text-xs font-mono font-bold text-teal-800 block">
                {lcdNode.policy_id || lcdNode.id || 'LCD'}
              </span>
              <p className="text-[11px] text-slate-700 font-medium line-clamp-2 leading-snug">
                {lcdNode.title || lcdNode.name || 'Local Coverage Determination'}
              </p>
            </div>
          ) : (
            <span className="text-xs text-slate-400 italic">No LCD matched</span>
          )}
        </div>

        {/* Article Node */}
        <div className={`p-3.5 rounded-xl border space-y-1.5 ${artNode ? 'bg-amber-50/40 border-amber-200' : 'bg-slate-50/50 border-slate-200/60 opacity-60'}`}>
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Policy Article
            </span>
            {artNode && getStatusBadge(artNode.result)}
          </div>
          {artNode ? (
            <div>
              <span className="text-xs font-mono font-bold text-amber-800 block">
                {artNode.article_id || artNode.policy_id || 'ARTICLE'}
              </span>
              <p className="text-[11px] text-slate-700 font-medium line-clamp-2 leading-snug">
                {artNode.title || 'Billing & Coding Article'}
              </p>
            </div>
          ) : (
            <span className="text-xs text-slate-400 italic">No Article attached</span>
          )}
        </div>
      </div>
    </div>
  );
}
