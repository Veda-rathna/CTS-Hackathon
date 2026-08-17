import React from 'react';
import { CheckCircle2, Clock, HelpCircle, AlertTriangle, XCircle } from 'lucide-react';

export default function DecisionBadge({ decision, size = 'md' }) {
  const norm = (decision || '').toUpperCase().trim();

  let config = {
    label: 'NEED MORE INFORMATION',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    text: 'text-amber-800',
    icon: HelpCircle,
  };

  if (norm === 'APPROVE' || norm === 'APPROVED' || norm.includes('APPROV')) {
    config = {
      label: 'APPROVE',
      bg: 'bg-emerald-50',
      border: 'border-emerald-200',
      text: 'text-emerald-700',
      icon: CheckCircle2,
    };
  } else if (
    norm === 'REJECTED' ||
    norm === 'EXCLUDED' ||
    norm === 'POLICY_EXCLUSION' ||
    norm === 'NOT_COVERED' ||
    norm === 'DENIED' ||
    norm === 'DENY'
  ) {
    config = {
      label: 'REJECTED / EXCLUDED',
      bg: 'bg-rose-50',
      border: 'border-rose-200',
      text: 'text-rose-700',
      icon: XCircle,
    };
  } else if (
    norm === 'PEND' ||
    norm === 'PENDED' ||
    norm === 'PENDING_REVIEW' ||
    norm === 'REVIEW'
  ) {
    config = {
      label: 'PEND',
      bg: 'bg-purple-50',
      border: 'border-purple-200',
      text: 'text-purple-700',
      icon: AlertTriangle,
    };
  } else if (
    norm === 'NEED_MORE_INFORMATION' ||
    norm === 'REQUEST_MORE_INFORMATION' ||
    norm === 'ADDITIONAL_EVIDENCE_REQUIRED' ||
    norm.includes('MORE_INFO')
  ) {
    config = {
      label: 'NEED MORE INFORMATION',
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      text: 'text-amber-800',
      icon: HelpCircle,
    };
  }

  const IconComponent = config.icon;

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs gap-1 font-semibold',
    md: 'px-2.5 py-1 text-xs font-bold gap-1.5',
    lg: 'px-4 py-2 text-sm font-bold gap-2',
    xl: 'px-5 py-2.5 text-base font-extrabold gap-2.5 shadow-sm',
  }[size] || 'px-2.5 py-1 text-xs font-bold gap-1.5';

  return (
    <span
      className={`inline-flex items-center rounded-full border ${config.bg} ${config.border} ${config.text} ${sizeClasses}`}
    >
      <IconComponent className="w-3.5 h-3.5 flex-shrink-0" />
      <span>{config.label}</span>
    </span>
  );
}
