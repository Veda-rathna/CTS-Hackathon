import React from 'react';
import { Search, Filter, RotateCcw, Building } from 'lucide-react';

export default function PolicySearchFilter({ filters, onChange, onReset, onSearch, loading }) {
  const update = (field, value) => {
    onChange({
      ...filters,
      [field]: value,
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch();
  };

  return (
    <form onSubmit={handleSubmit} className="healthcare-card p-5 space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-sky-600" />
          <h3 className="text-sm font-semibold text-slate-800">CMS Coverage Search Filters</h3>
        </div>

        <button
          type="button"
          onClick={onReset}
          className="text-xs text-slate-500 hover:text-slate-800 flex items-center gap-1 transition-colors"
        >
          <RotateCcw className="w-3 h-3" />
          <span>Reset Filters</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
        {/* Procedure Code */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            Procedure Code (HCPCS/CPT) <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            placeholder="e.g. 64483, 38240, 82105"
            value={filters.procedure_code || ''}
            onChange={(e) => update('procedure_code', e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 font-mono"
            required
          />
        </div>

        {/* Diagnosis Code */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">Diagnosis Code (ICD-10)</label>
          <input
            type="text"
            placeholder="e.g. M54.16, C92.00"
            value={filters.diagnosis_code || ''}
            onChange={(e) => update('diagnosis_code', e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 font-mono"
          />
        </div>

        {/* State / Jurisdiction */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">State / Jurisdiction</label>
          <input
            type="text"
            maxLength={2}
            placeholder="e.g. TX, CA, IL, MA"
            value={filters.state || ''}
            onChange={(e) => update('state', e.target.value.toUpperCase())}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 font-mono"
          />
        </div>

        {/* Policy Type */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">Policy Type</label>
          <select
            value={filters.policy_type || ''}
            onChange={(e) => update('policy_type', e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 bg-white"
          >
            <option value="">All Types (LCD / NCD / Article)</option>
            <option value="LCD">LCD (Local Coverage)</option>
            <option value="NCD">NCD (National Coverage)</option>
            <option value="ARTICLE">Article (Billing & Coding)</option>
          </select>
        </div>
      </div>

      <div className="flex justify-end pt-2">
        <button
          type="submit"
          disabled={loading || !filters.procedure_code?.trim()}
          className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-sky-600 hover:bg-sky-700 disabled:bg-sky-400 text-white font-semibold text-xs transition-all shadow-sm"
        >
          <Search className="w-3.5 h-3.5" />
          <span>{loading ? 'Searching...' : 'Search Policies'}</span>
        </button>
      </div>
    </form>
  );
}
