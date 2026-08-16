import React from 'react';
import { Activity, Calendar, MapPin, Layers } from 'lucide-react';

export default function ServiceCard({ service, onChange, errors = {} }) {
  const updateField = (field, value) => {
    onChange({
      ...service,
      [field]: value,
    });
  };

  return (
    <div className="healthcare-card p-5 sm:p-6 space-y-4">
      <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
        <div className="w-8 h-8 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center">
          <Activity className="w-4 h-4" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-800">Proposed Service & Procedure Details</h3>
          <p className="text-xs text-slate-500">Service description, billing codes, dates, and frequency</p>
        </div>
      </div>

      {/* Large Textarea for Service Description */}
      <div className="text-xs">
        <label className="block font-semibold text-slate-700 mb-1">
          Service Description <span className="text-rose-500">*</span>
        </label>
        <textarea
          rows={3}
          placeholder="Detailed clinical narrative of the requested medical/surgical procedure or service..."
          value={service.service_description || ''}
          onChange={(e) => updateField('service_description', e.target.value)}
          className={`w-full px-3 py-2 rounded-lg border ${
            errors['service.service_description']
              ? 'border-rose-400 bg-rose-50/40'
              : 'border-slate-200'
          } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 leading-relaxed`}
        />
        {errors['service.service_description'] && (
          <p className="text-[11px] text-rose-600 mt-1">{errors['service.service_description']}</p>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-xs">
        {/* Procedure Code (nullable) */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            Procedure Code <span className="text-slate-400 font-normal">(Optional / Nullable)</span>
          </label>
          <input
            type="text"
            placeholder="e.g. 64483 or leave empty"
            value={service.procedure_code || ''}
            onChange={(e) => updateField('procedure_code', e.target.value ? e.target.value.trim() : null)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 font-mono"
          />
          <p className="text-[10px] text-slate-400 mt-0.5">Leave empty if code mapping is required.</p>
        </div>

        {/* Procedure Code System */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            Procedure Code System <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            placeholder="e.g. HCPCS/CPT or CPT/HCPCS_MAPPING_REQUIRED"
            value={service.procedure_code_system || ''}
            onChange={(e) => updateField('procedure_code_system', e.target.value)}
            className={`w-full px-3 py-2 rounded-lg border ${
              errors['service.procedure_code_system']
                ? 'border-rose-400 bg-rose-50/40'
                : 'border-slate-200'
            } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500`}
          />
          {errors['service.procedure_code_system'] && (
            <p className="text-[11px] text-rose-600 mt-1">{errors['service.procedure_code_system']}</p>
          )}
        </div>

        {/* Place of Service */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">Place of Service</label>
          <input
            type="text"
            placeholder="e.g. Outpatient Surgical Suite"
            value={service.place_of_service || ''}
            onChange={(e) => updateField('place_of_service', e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500"
          />
        </div>

        {/* Start Date */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            Start Date <span className="text-rose-500">*</span>
          </label>
          <input
            type="date"
            value={service.start_date || ''}
            onChange={(e) => updateField('start_date', e.target.value)}
            className={`w-full px-3 py-2 rounded-lg border ${
              errors['service.start_date'] ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
            } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500`}
          />
          {errors['service.start_date'] && (
            <p className="text-[11px] text-rose-600 mt-1">{errors['service.start_date']}</p>
          )}
        </div>

        {/* End Date */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            End Date <span className="text-rose-500">*</span>
          </label>
          <input
            type="date"
            value={service.end_date || ''}
            onChange={(e) => updateField('end_date', e.target.value)}
            className={`w-full px-3 py-2 rounded-lg border ${
              errors['service.end_date'] ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
            } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500`}
          />
          {errors['service.end_date'] && (
            <p className="text-[11px] text-rose-600 mt-1">{errors['service.end_date']}</p>
          )}
        </div>

        {/* Number of Sessions */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">Number of Sessions</label>
          <input
            type="number"
            min="1"
            placeholder="1"
            value={service.number_of_sessions !== undefined ? service.number_of_sessions : 1}
            onChange={(e) =>
              updateField('number_of_sessions', e.target.value === '' ? '' : Number(e.target.value))
            }
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500"
          />
        </div>

        {/* Duration */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">Duration</label>
          <input
            type="text"
            placeholder="e.g. 1 day or 30 days"
            value={service.duration || ''}
            onChange={(e) => updateField('duration', e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500"
          />
        </div>

        {/* Frequency */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">Frequency</label>
          <input
            type="text"
            placeholder="e.g. Once or Weekly"
            value={service.frequency || ''}
            onChange={(e) => updateField('frequency', e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500"
          />
        </div>
      </div>
    </div>
  );
}
