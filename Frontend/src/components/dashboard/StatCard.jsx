import React from 'react';

export default function StatCard({ title, value, icon: Icon, color = 'blue', subtitle, onClick }) {
  const colorMap = {
    blue: {
      bg: 'bg-sky-50',
      text: 'text-sky-700',
      border: 'border-sky-200',
      dot: 'bg-sky-500',
    },
    emerald: {
      bg: 'bg-emerald-50',
      text: 'text-emerald-700',
      border: 'border-emerald-200',
      dot: 'bg-emerald-500',
    },
    amber: {
      bg: 'bg-amber-50',
      text: 'text-amber-700',
      border: 'border-amber-200',
      dot: 'bg-amber-500',
    },
    rose: {
      bg: 'bg-rose-50',
      text: 'text-rose-700',
      border: 'border-rose-200',
      dot: 'bg-rose-500',
    },
    purple: {
      bg: 'bg-purple-50',
      text: 'text-purple-700',
      border: 'border-purple-200',
      dot: 'bg-purple-500',
    },
  }[color] || {
    bg: 'bg-slate-50',
    text: 'text-slate-700',
    border: 'border-slate-200',
    dot: 'bg-slate-500',
  };

  return (
    <div
      onClick={onClick}
      className={`healthcare-card p-4 sm:p-5 bg-white border border-slate-200/90 rounded-xl transition-all ${
        onClick ? 'cursor-pointer hover:border-slate-300 hover:shadow-xs' : ''
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
          {title}
        </span>
        <div className={`w-8 h-8 rounded-lg ${colorMap.bg} ${colorMap.text} border ${colorMap.border} flex items-center justify-center flex-shrink-0`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>

      <div className="mt-2.5 flex items-baseline gap-2">
        <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          {value}
        </span>
      </div>

      {subtitle && (
        <div className="mt-1.5 flex items-center gap-1.5 text-[11px] text-slate-500 font-medium truncate">
          <span className={`w-1.5 h-1.5 rounded-full ${colorMap.dot} flex-shrink-0`} />
          <span className="truncate">{subtitle}</span>
        </div>
      )}
    </div>
  );
}
