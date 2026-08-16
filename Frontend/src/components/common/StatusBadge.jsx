import React from 'react';
import { Check, X, AlertCircle, HelpCircle, MinusCircle } from 'lucide-react';

export default function StatusBadge({ status, size = 'sm' }) {
  const norm = (status || '').toUpperCase();

  let config = {
    label: norm || 'UNKNOWN',
    bg: 'bg-slate-100',
    border: 'border-slate-200',
    text: 'text-slate-700',
    icon: HelpCircle,
  };

  switch (norm) {
    case 'MATCHED':
    case 'COVERED':
    case 'SATISFIED':
    case 'ACTIVE':
      config = {
        label: 'Matched',
        bg: 'bg-emerald-50',
        border: 'border-emerald-200',
        text: 'text-emerald-700',
        icon: Check,
      };
      break;
    case 'NOT MATCHED':
    case 'NOT_MATCHED':
    case 'NOT_COVERED':
    case 'NOT_SATISFIED':
    case 'EXCLUDED':
      config = {
        label: 'Not Matched',
        bg: 'bg-rose-50',
        border: 'border-rose-200',
        text: 'text-rose-700',
        icon: X,
      };
      break;
    case 'REVIEW':
    case 'PENDING':
    case 'PEND':
    case 'UNKNOWN':
      config = {
        label: 'Review Required',
        bg: 'bg-amber-50',
        border: 'border-amber-200',
        text: 'text-amber-700',
        icon: AlertCircle,
      };
      break;
    case 'MISSING':
    case 'NOT_FOUND':
      config = {
        label: 'Missing Evidence',
        bg: 'bg-red-50',
        border: 'border-red-200',
        text: 'text-red-700',
        icon: MinusCircle,
      };
      break;
    case 'NOT APPLICABLE':
    case 'NOT_APPLICABLE':
    case 'NOT_ADDRESSED':
      config = {
        label: 'Not Applicable',
        bg: 'bg-slate-100',
        border: 'border-slate-200',
        text: 'text-slate-600',
        icon: HelpCircle,
      };
      break;
    default:
      config.label = status || 'Unknown';
      break;
  }

  const IconComp = config.icon;

  const sizeClasses = {
    xs: 'px-1.5 py-0.5 text-[10px] gap-1 font-medium',
    sm: 'px-2 py-0.5 text-xs gap-1 font-medium',
    md: 'px-2.5 py-1 text-xs gap-1.5 font-semibold',
  }[size] || 'px-2 py-0.5 text-xs gap-1 font-medium';

  return (
    <span
      className={`inline-flex items-center rounded-md border ${config.bg} ${config.border} ${config.text} ${sizeClasses}`}
    >
      <IconComp className={size === 'xs' ? 'w-2.5 h-2.5' : 'w-3 h-3'} />
      <span>{config.label}</span>
    </span>
  );
}
