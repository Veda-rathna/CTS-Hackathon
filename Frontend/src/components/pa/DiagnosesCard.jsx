import React from 'react';
import { Stethoscope, Plus, Trash2, Tag, AlertCircle } from 'lucide-react';

export default function DiagnosesCard({ diagnoses = [], onChange, errors = {} }) {
  const handleAddDiagnosis = () => {
    const newDiag = {
      description: '',
      source_code: '',
      source_code_system: 'ICD-10-CM',
      icd10_code: null,
      icd10_mapping_required: false,
    };
    onChange([...diagnoses, newDiag]);
  };

  const handleRemoveDiagnosis = (index) => {
    if (diagnoses.length <= 1) return;
    const updated = diagnoses.filter((_, i) => i !== index);
    onChange(updated);
  };

  const handleUpdateField = (index, field, value) => {
    const updated = diagnoses.map((d, i) => {
      if (i === index) {
        return {
          ...d,
          [field]: value,
        };
      }
      return d;
    });
    onChange(updated);
  };

  return (
    <div className="healthcare-card p-5 sm:p-6 space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center">
            <Tag className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-800">Clinical Diagnoses</h3>
            <p className="text-xs text-slate-500">ICD-10-CM / SNOMED coding and clinical mappings</p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleAddDiagnosis}
          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-sky-700 bg-sky-50 hover:bg-sky-100 border border-sky-200 rounded-lg transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>+ Add Diagnosis</span>
        </button>
      </div>

      {errors.diagnoses && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errors.diagnoses}</span>
        </div>
      )}

      {/* Diagnosis List */}
      <div className="space-y-4">
        {diagnoses.map((diag, index) => {
          const descError = errors[`diagnoses.${index}.description`];
          const sourceCodeError = errors[`diagnoses.${index}.source_code`];
          const systemError = errors[`diagnoses.${index}.source_code_system`];

          return (
            <div
              key={index}
              className="p-4 rounded-xl bg-slate-50/70 border border-slate-200 relative group space-y-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Diagnosis #{index + 1}
                </span>
                {diagnoses.length > 1 && (
                  <button
                    type="button"
                    onClick={() => handleRemoveDiagnosis(index)}
                    className="text-slate-400 hover:text-rose-600 p-1 rounded-md transition-colors"
                    title="Remove Diagnosis"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* Description */}
              <div className="text-xs">
                <label className="block font-semibold text-slate-700 mb-1">
                  Diagnosis Description <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g. Lumbar radiculopathy, lumbosacral region or Gingival disease"
                  value={diag.description || ''}
                  onChange={(e) => handleUpdateField(index, 'description', e.target.value)}
                  className={`w-full px-3 py-2 rounded-lg border ${
                    descError ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
                  } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 bg-white`}
                />
                {descError && <p className="text-[11px] text-rose-600 mt-1">{descError}</p>}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                {/* Source Code */}
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Source Code <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. M54.16 or 18718003"
                    value={diag.source_code || ''}
                    onChange={(e) => {
                      const code = e.target.value;
                      handleUpdateField(index, 'source_code', code);
                      // If user provides standard ICD-10 and no explicit icd10_code is set
                      if (!diag.icd10_mapping_required && !diag.icd10_code) {
                        handleUpdateField(index, 'icd10_code', code);
                      }
                    }}
                    className={`w-full px-3 py-2 rounded-lg border ${
                      sourceCodeError ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
                    } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 font-mono bg-white`}
                  />
                  {sourceCodeError && (
                    <p className="text-[11px] text-rose-600 mt-1">{sourceCodeError}</p>
                  )}
                </div>

                {/* Source Code System */}
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Source Code System <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. ICD-10-CM or SNOMED-CT"
                    value={diag.source_code_system || ''}
                    onChange={(e) => handleUpdateField(index, 'source_code_system', e.target.value)}
                    className={`w-full px-3 py-2 rounded-lg border ${
                      systemError ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
                    } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 bg-white`}
                  />
                  {systemError && (
                    <p className="text-[11px] text-rose-600 mt-1">{systemError}</p>
                  )}
                </div>

                {/* ICD-10 Code (nullable) */}
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    ICD-10 Code <span className="text-slate-400 font-normal">(Optional / Nullable)</span>
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. M54.16 or null"
                    value={diag.icd10_code || ''}
                    onChange={(e) =>
                      handleUpdateField(
                        index,
                        'icd10_code',
                        e.target.value ? e.target.value.trim() : null
                      )
                    }
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 font-mono bg-white"
                  />
                </div>
              </div>

              {/* ICD10 Mapping Required Switch */}
              <div className="pt-2 flex items-center justify-between border-t border-slate-200/60">
                <span className="text-[11px] font-medium text-slate-600">
                  ICD-10 Mapping Required flag (`icd10_mapping_required`)
                </span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={!!diag.icd10_mapping_required}
                    onChange={(e) =>
                      handleUpdateField(index, 'icd10_mapping_required', e.target.checked)
                    }
                    className="sr-only peer"
                  />
                  <div className="w-8 h-4 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-amber-500"></div>
                </label>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
