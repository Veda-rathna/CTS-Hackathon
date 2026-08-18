import React from 'react';

export default function SectionHeader({
  icon: Icon,
  title,
  subtitle,
  badge,
  action,
  className = '',
}) {
  return (
    <div className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200/80 ${className}`}>
      <div className="flex items-start sm:items-center gap-2.5">
        {Icon && (
          <div className="p-1.5 rounded-lg bg-sky-50 text-sky-700 border border-sky-100 flex-shrink-0 mt-0.5 sm:mt-0">
            <Icon className="w-4 h-4" />
          </div>
        )}
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">{title}</h3>
            {badge && <div>{badge}</div>}
          </div>
          {subtitle && (
            <p className="text-xs text-slate-500 mt-0.5 leading-normal">{subtitle}</p>
          )}
        </div>
      </div>
      {action && <div className="flex-shrink-0 self-start sm:self-auto">{action}</div>}
    </div>
  );
}
