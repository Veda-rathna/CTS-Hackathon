import React from 'react';
import { CheckCircle2, XCircle, Clock, AlertTriangle, AlertCircle } from 'lucide-react';

export default function DecisionBadge({ decision, size = 'md' }) {
  const norm = (decision || '').toUpperCase();

  let config = {
    label: 'Pending Review',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    text: 'text-amber-700',
    icon: Clock,
  };

  if (norm.includes('APPROV') || norm === 'LIKELY_COVERED' || norm === 'COVERED') {
    config = {
      label: 'Approved',
      bg: 'bg-emerald-50',
      border: 'border-emerald-200',
      text: 'text-emerald-700',
      icon: CheckCircle2,
    };
  } else if (norm.includes('DENY') || norm.includes('DENIED') || norm === 'EXCLUDED') {
    config = {
      label: 'Denied',
      bg: 'bg-rose-50',
      border: 'border-rose-200',
      text: 'text-rose-700',
      icon: XCircle,
    };
  } else if (norm.includes('ADDITIONAL') || norm.includes('MORE_INFO') || norm === 'REQUEST_MORE_INFORMATION') {
    config = {
      label: 'Additional Evidence Required',
      bg: 'bg-indigo-50',
      border: 'border-indigo-200',
      text: 'text-indigo-700',
      icon: AlertCircle,
    };
  } else if (norm.includes('EXPIRED') || norm === 'POLICY_EXPIRED') {
    config = {
      label: 'Policy Expired',
      bg: 'bg-slate-100',
      border: 'border-slate-300',
      text: 'text-slate-700',
      icon: AlertTriangle,
    };
  }

  const IconComponent = config.icon;

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs gap-1',
    md: 'px-2.5 py-1 text-xs font-medium gap-1.5',
    lg: 'px-4 py-2 text-sm font-semibold gap-2',
    xl: 'px-5 py-2.5 text-base font-bold gap-2.5 shadow-sm',
  }[size] || 'px-2.5 py-1 text-xs font-medium gap-1.5';

  return (
    <span
      className={`inline-flex items-center rounded-full border ${config.bg} ${config.border} ${config.text} ${sizeClasses}`}
    >
      <IconComponent className={size === 'xl' ? 'w-5 h-5' : size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />
      <span>{config.label}</span>
    </span>
  );
}
