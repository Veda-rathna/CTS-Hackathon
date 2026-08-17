import React from 'react';
import { AlertCircle, AlertTriangle, Clock, ArrowDown } from 'lucide-react';

export default function PriorityBadge({ priority = 'LOW', size = 'sm' }) {
  const norm = (priority || 'LOW').toUpperCase().trim();

  let config = {
    label: 'Low Priority',
    shortLabel: 'LOW',
    bg: 'bg-slate-100',
    border: 'border-slate-200',
    text: 'text-slate-700',
    dot: 'bg-slate-400',
    icon: ArrowDown,
  };

  if (norm === 'URGENT' || norm === 'HIGH' || norm === 'EXPEDITED') {
    config = {
      label: 'Urgent Priority',
      shortLabel: 'URGENT',
      bg: 'bg-rose-50',
      border: 'border-rose-200',
      text: 'text-rose-700',
      dot: 'bg-rose-500 animate-pulse',
      icon: AlertCircle,
    };
  } else if (norm === 'MEDIUM' || norm === 'MODERATE' || norm === 'STANDARD') {
    config = {
      label: 'Medium Priority',
      shortLabel: 'MEDIUM',
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      text: 'text-amber-800',
      dot: 'bg-amber-500',
      icon: Clock,
    };
  } else if (norm === 'LOW') {
    config = {
      label: 'Low Priority',
      shortLabel: 'LOW',
      bg: 'bg-sky-50',
      border: 'border-sky-200',
      text: 'text-sky-700',
      dot: 'bg-sky-400',
      icon: ArrowDown,
    };
  }

  const IconComponent = config.icon;

  const sizeClasses = {
    xs: 'px-1.5 py-0.5 text-[10px] gap-1 font-semibold',
    sm: 'px-2 py-0.5 text-xs gap-1.5 font-bold',
    md: 'px-2.5 py-1 text-xs gap-1.5 font-bold',
    lg: 'px-3.5 py-1.5 text-sm gap-2 font-bold',
  }[size] || 'px-2 py-0.5 text-xs gap-1.5 font-bold';

  return (
    <span
      className={`inline-flex items-center rounded-full border ${config.bg} ${config.border} ${config.text} ${sizeClasses} select-none`}
      title={config.label}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot} flex-shrink-0`} />
      <span>{config.shortLabel}</span>
    </span>
  );
}
