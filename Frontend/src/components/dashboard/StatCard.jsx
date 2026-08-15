import React from 'react';

export default function StatCard({ title, value, icon: Icon, color = 'blue', subtitle, onClick }) {
  const colorMap = {
    blue: {
      bg: 'bg-sky-50',
      text: 'text-sky-600',
      border: 'border-sky-200',
      dot: 'bg-sky-500',
    },
    emerald: {
      bg: 'bg-emerald-50',
      text: 'text-emerald-600',
      border: 'border-emerald-200',
      dot: 'bg-emerald-500',
    },
    amber: {
      bg: 'bg-amber-50',
      text: 'text-amber-600',
      border: 'border-amber-200',
      dot: 'bg-amber-500',
    },
    rose: {
      bg: 'bg-rose-50',
      text: 'text-rose-600',
      border: 'border-rose-200',
      dot: 'bg-rose-500',
    },
    purple: {
      bg: 'bg-purple-50',
      text: 'text-purple-600',
      border: 'border-purple-200',
      dot: 'bg-purple-500',
    },
  }[color] || {
    bg: 'bg-slate-50',
    text: 'text-slate-600',
    border: 'border-slate-200',
    dot: 'bg-slate-500',
  };

  return (
    <div
      onClick={onClick}
      className={`healthcare-card p-5 cursor-pointer ${
        onClick ? 'healthcare-card-hover' : ''
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          {title}
        </span>
        <div className={`w-9 h-9 rounded-lg ${colorMap.bg} ${colorMap.text} flex items-center justify-center`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
          {value}
        </span>
      </div>

      {subtitle && (
        <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-500">
          <span className={`w-1.5 h-1.5 rounded-full ${colorMap.dot}`}></span>
          <span>{subtitle}</span>
        </div>
      )}
    </div>
  );
}
