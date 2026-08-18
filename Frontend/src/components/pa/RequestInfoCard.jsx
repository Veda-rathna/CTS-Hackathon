import React from 'react';
import { FileText, Clock, AlertTriangle, ShieldAlert } from 'lucide-react';
import PriorityBadge from '../common/PriorityBadge';

export default function RequestInfoCard({ request, onChange, errors = {} }) {
  const updateField = (field, value) => {
    onChange({
      ...request,
      [field]: value,
    });
  };

  const currentPriority = request.review_type === 'URGENT' || (request.urgency_reason && request.urgency_reason.trim().length > 0) ? 'URGENT' : 'LOW';

  return (
    <div className="healthcare-card p-5 sm:p-6 space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-800">Request Information</h3>
            <p className="text-xs text-slate-500">Urgency level, review category, and authorization history</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-[11px] text-slate-400 font-bold uppercase">Priority:</span>
          <PriorityBadge priority={currentPriority} size="xs" />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-xs">
        {/* Request Date */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            Request Date <span className="text-rose-500">*</span>
          </label>
          <input
            type="date"
            value={request.request_date || ''}
            onChange={(e) => updateField('request_date', e.target.value)}
            className={`w-full px-3 py-2 rounded-lg border ${
              errors['request.request_date'] ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
            } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500`}
          />
          {errors['request.request_date'] && (
            <p className="text-[11px] text-rose-600 mt-1">{errors['request.request_date']}</p>
          )}
        </div>

        {/* Review Type */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            Review Type <span className="text-rose-500">*</span>
          </label>
          <select
            value={request.review_type || 'NON_URGENT'}
            onChange={(e) => updateField('review_type', e.target.value)}
            className={`w-full px-3 py-2 rounded-lg border ${
              errors['request.review_type'] ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
            } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 bg-white font-medium`}
          >
            <option value="URGENT">URGENT (Expedited 24h)</option>
            <option value="NON_URGENT">NON_URGENT (Standard 72h)</option>
            <option value="ROUTINE">ROUTINE (Standard 14d)</option>
          </select>
          {errors['request.review_type'] && (
            <p className="text-[11px] text-rose-600 mt-1">{errors['request.review_type']}</p>
          )}
        </div>

        {/* Request Type */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            Request Type <span className="text-rose-500">*</span>
          </label>
          <select
            value={request.request_type || 'INITIAL'}
            onChange={(e) => updateField('request_type', e.target.value)}
            className={`w-full px-3 py-2 rounded-lg border ${
              errors['request.request_type'] ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
            } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 bg-white font-medium`}
          >
            <option value="INITIAL">INITIAL</option>
            <option value="RENEWAL">RENEWAL</option>
          </select>
          {errors['request.request_type'] && (
            <p className="text-[11px] text-rose-600 mt-1">{errors['request.request_type']}</p>
          )}
        </div>

        {/* Urgency Reason (nullable) */}
        <div className="sm:col-span-2">
          <label className="block font-semibold text-slate-700 mb-1">
            Urgency Reason <span className="text-slate-400 font-normal">(Optional / Nullable)</span>
          </label>
          <input
            type="text"
            placeholder="Clinical justification if expedited review is requested..."
            value={request.urgency_reason || ''}
            onChange={(e) => updateField('urgency_reason', e.target.value ? e.target.value : null)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500"
          />
        </div>

        {/* Previous Authorization Number (nullable) */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            Previous Auth Number <span className="text-slate-400 font-normal">(Optional / Nullable)</span>
          </label>
          <input
            type="text"
            placeholder="e.g. AUTH-2025-998"
            value={request.previous_authorization_number || ''}
            onChange={(e) =>
              updateField('previous_authorization_number', e.target.value ? e.target.value : null)
            }
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500"
          />
        </div>
      </div>

      {/* Mock Request Field Switch */}
      <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold text-slate-800 block">Mock Request Flag</span>
          <span className="text-[11px] text-slate-500">
            Set mock_request_field boolean flag in payload
          </span>
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={!!request.mock_request_field}
            onChange={(e) => updateField('mock_request_field', e.target.checked)}
            className="sr-only peer"
          />
          <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-sky-600"></div>
        </label>
      </div>
    </div>
  );
}
