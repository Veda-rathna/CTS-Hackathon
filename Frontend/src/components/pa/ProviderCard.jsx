import React from 'react';
import { Stethoscope, Building2 } from 'lucide-react';

export default function ProviderCard({ provider, onChange, errors = {} }) {
  const updateField = (field, value) => {
    onChange({
      ...provider,
      [field]: value,
    });
  };

  return (
    <div className="healthcare-card p-5 sm:p-6 space-y-4">
      <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
        <div className="w-8 h-8 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center">
          <Stethoscope className="w-4 h-4" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-800">Provider & Organization Information</h3>
          <p className="text-xs text-slate-500">Ordering clinician credentials and facility identifiers</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-xs">
        {/* Provider ID */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            Provider ID <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            placeholder="e.g. prov018"
            value={provider.provider_id || ''}
            onChange={(e) => updateField('provider_id', e.target.value)}
            className={`w-full px-3 py-2 rounded-lg border ${
              errors['provider.provider_id'] ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
            } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500`}
          />
          {errors['provider.provider_id'] && (
            <p className="text-[11px] text-rose-600 mt-1">{errors['provider.provider_id']}</p>
          )}
        </div>

        {/* Specialty */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            Specialty <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            placeholder="e.g. GENERAL PRACTICE or PAIN MEDICINE"
            value={provider.specialty || ''}
            onChange={(e) => updateField('specialty', e.target.value)}
            className={`w-full px-3 py-2 rounded-lg border ${
              errors['provider.specialty'] ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
            } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500`}
          />
          {errors['provider.specialty'] && (
            <p className="text-[11px] text-rose-600 mt-1">{errors['provider.specialty']}</p>
          )}
        </div>

        {/* State */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            Provider State <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            placeholder="e.g. MA or TX"
            maxLength={2}
            value={provider.state || ''}
            onChange={(e) => updateField('state', e.target.value.toUpperCase())}
            className={`w-full px-3 py-2 rounded-lg border ${
              errors['provider.state'] ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
            } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 font-mono`}
          />
          {errors['provider.state'] && (
            <p className="text-[11px] text-rose-600 mt-1">{errors['provider.state']}</p>
          )}
        </div>

        {/* Organization ID */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            Organization ID <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            placeholder="e.g. org018"
            value={provider.organization_id || ''}
            onChange={(e) => updateField('organization_id', e.target.value)}
            className={`w-full px-3 py-2 rounded-lg border ${
              errors['provider.organization_id'] ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
            } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500`}
          />
          {errors['provider.organization_id'] && (
            <p className="text-[11px] text-rose-600 mt-1">{errors['provider.organization_id']}</p>
          )}
        </div>

        {/* Organization Name */}
        <div className="sm:col-span-2">
          <label className="block font-semibold text-slate-700 mb-1">
            Organization Name <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            placeholder="e.g. FENWAY COMMUNITY HEALTH CENTER INC"
            value={provider.organization_name || ''}
            onChange={(e) => updateField('organization_name', e.target.value)}
            className={`w-full px-3 py-2 rounded-lg border ${
              errors['provider.organization_name'] ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
            } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500`}
          />
          {errors['provider.organization_name'] && (
            <p className="text-[11px] text-rose-600 mt-1">{errors['provider.organization_name']}</p>
          )}
        </div>
      </div>
    </div>
  );
}
