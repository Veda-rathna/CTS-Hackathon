import React from 'react';
import { Inbox } from 'lucide-react';

export default function EmptyState({
  icon: Icon = Inbox,
  title = 'No records found',
  description = 'There are no items matching your criteria.',
  actionLabel,
  onAction,
  className = '',
}) {
  return (
    <div className={`p-8 sm:p-12 text-center space-y-3 bg-white rounded-xl border border-slate-200/80 ${className}`}>
      <div className="w-12 h-12 mx-auto rounded-xl bg-slate-100/80 border border-slate-200 flex items-center justify-center text-slate-400">
        <Icon className="w-6 h-6" />
      </div>
      <div className="space-y-1 max-w-sm mx-auto">
        <h4 className="text-sm font-semibold text-slate-800">{title}</h4>
        <p className="text-xs text-slate-500 leading-relaxed">{description}</p>
      </div>
      {actionLabel && onAction && (
        <div className="pt-2">
          <button
            type="button"
            onClick={onAction}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-sky-700 bg-sky-50 hover:bg-sky-100 border border-sky-200 rounded-lg transition-colors"
          >
            {actionLabel}
          </button>
        </div>
      )}
    </div>
  );
}
