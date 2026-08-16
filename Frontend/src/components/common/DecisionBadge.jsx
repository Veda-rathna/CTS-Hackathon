import React from 'react';
import { CheckCircle2, XCircle, HelpCircle, Clock, AlertTriangle } from 'lucide-react';

export default function DecisionBadge({ decision, size = 'md' }) {
  const norm = (decision || '').toUpperCase().trim();

  // Default: Pending / unknown
  let config = {
    label: 'Pending Review',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    text: 'text-amber-700',
    icon: Clock,
  };

  if (norm === 'APPROVE' || norm === 'APPROVED') {
    config = {
      label: 'APPROVE',
      bg: 'bg-emerald-50',
      border: 'border-emerald-200',
      text: 'text-emerald-700',
      icon: CheckCircle2,
    };
  } else if (norm === 'DENY' || norm === 'DENIED') {
    config = {
      label: 'DENY',
      bg: 'bg-rose-50',
      border: 'border-rose-200',
      text: 'text-rose-700',
      icon: XCircle,
    };
  } else if (norm === 'NEED_MORE_INFORMATION' || norm === 'REQUEST_MORE_INFORMATION') {
    config = {
      label: 'NEED MORE INFORMATION',
      bg: 'bg-sky-50',
      border: 'border-sky-200',
      text: 'text-sky-700',
      icon: HelpCircle,
    };
  } else if (norm === 'PEND' || norm === 'PENDED') {
    config = {
      label: 'Pended — Manual Review',
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      text: 'text-amber-700',
      icon: Clock,
    };
  } else if (norm === 'POLICY_EXPIRED') {
    config = {
      label: 'DENY (Policy Expired)',
      bg: 'bg-rose-50',
      border: 'border-rose-200',
      text: 'text-rose-700',
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


