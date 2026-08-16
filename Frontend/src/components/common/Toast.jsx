import React from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export default function Toast({ message, type = 'success', onClose }) {
  if (!message) return null;

  const typeConfig = {
    success: {
      bg: 'bg-emerald-900/90 text-white border-emerald-700',
      icon: CheckCircle2,
      iconColor: 'text-emerald-400',
    },
    error: {
      bg: 'bg-rose-900/90 text-white border-rose-700',
      icon: AlertCircle,
      iconColor: 'text-rose-400',
    },
    info: {
      bg: 'bg-slate-900/90 text-white border-slate-700',
      icon: Info,
      iconColor: 'text-sky-400',
    },
  }[type] || {
    bg: 'bg-slate-900 text-white border-slate-700',
    icon: Info,
    iconColor: 'text-sky-400',
  };

  const Icon = typeConfig.icon;

  return (
    <div className="fixed bottom-5 right-5 z-50 animate-in fade-in slide-in-from-bottom-5 duration-300">
      <div
        className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg border backdrop-blur-sm ${typeConfig.bg} text-sm max-w-md`}
      >
        <Icon className={`w-5 h-5 flex-shrink-0 ${typeConfig.iconColor}`} />
        <p className="flex-1 text-xs sm:text-sm font-medium">{message}</p>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="text-slate-300 hover:text-white p-1 rounded transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}
