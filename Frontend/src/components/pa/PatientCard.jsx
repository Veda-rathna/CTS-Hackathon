import React from 'react';
import { User, Calendar, MapPin, Building, Hash } from 'lucide-react';

export default function PatientCard({ patient, onChange, errors = {} }) {
  const updateField = (field, value) => {
    onChange({
      ...patient,
      [field]: value,
    });
  };

  return (
    <div className="healthcare-card p-5 sm:p-6 space-y-4">
      <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
        <div className="w-8 h-8 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center">
          <User className="w-4 h-4" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-800">Patient Information</h3>
          <p className="text-xs text-slate-500">Demographic details and payer assignment</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-xs">
        {/* Patient ID */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            Patient ID <span className="text-rose-500">*</span>
          </label>
          <div className="relative">
            <input
              type="text"
              placeholder="e.g. p001"
              value={patient.patient_id || ''}
              onChange={(e) => updateField('patient_id', e.target.value)}
              className={`w-full px-3 py-2 rounded-lg border ${
                errors['patient.patient_id'] ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
              } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500`}
            />
          </div>
          {errors['patient.patient_id'] && (
            <p className="text-[11px] text-rose-600 mt-1">{errors['patient.patient_id']}</p>
          )}
        </div>

        {/* Date of Birth */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            Date of Birth <span className="text-rose-500">*</span>
          </label>
          <input
            type="date"
            value={patient.date_of_birth || ''}
            onChange={(e) => {
              const dob = e.target.value;
              let calculatedAge = patient.age;
              if (dob) {
                const birthYear = new Date(dob).getFullYear();
                const currentYear = new Date().getFullYear();
                if (!isNaN(birthYear) && birthYear > 1900) {
                  calculatedAge = Math.max(0, currentYear - birthYear);
                }
              }
              onChange({
                ...patient,
                date_of_birth: dob,
                age: calculatedAge,
              });
            }}
            className={`w-full px-3 py-2 rounded-lg border ${
              errors['patient.date_of_birth'] ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
            } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500`}
          />
          {errors['patient.date_of_birth'] && (
            <p className="text-[11px] text-rose-600 mt-1">{errors['patient.date_of_birth']}</p>
          )}
        </div>

        {/* Age */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            Age (Years) <span className="text-rose-500">*</span>
          </label>
          <input
            type="number"
            min="0"
            max="130"
            placeholder="e.g. 47"
            value={patient.age !== undefined && patient.age !== null ? patient.age : ''}
            onChange={(e) => updateField('age', e.target.value === '' ? '' : Number(e.target.value))}
            className={`w-full px-3 py-2 rounded-lg border ${
              errors['patient.age'] ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
            } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500`}
          />
          {errors['patient.age'] && (
            <p className="text-[11px] text-rose-600 mt-1">{errors['patient.age']}</p>
          )}
        </div>

        {/* Gender */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            Gender <span className="text-rose-500">*</span>
          </label>
          <select
            value={patient.gender || ''}
            onChange={(e) => updateField('gender', e.target.value)}
            className={`w-full px-3 py-2 rounded-lg border ${
              errors['patient.gender'] ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
            } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 bg-white`}
          >
            <option value="">Select Gender</option>
            <option value="M">Male (M)</option>
            <option value="F">Female (F)</option>
            <option value="O">Other / Non-binary</option>
            <option value="U">Unknown</option>
          </select>
          {errors['patient.gender'] && (
            <p className="text-[11px] text-rose-600 mt-1">{errors['patient.gender']}</p>
          )}
        </div>

        {/* State */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            State / Jurisdiction <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            placeholder="e.g. Massachusetts or MA"
            value={patient.state || ''}
            onChange={(e) => updateField('state', e.target.value)}
            className={`w-full px-3 py-2 rounded-lg border ${
              errors['patient.state'] ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
            } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500`}
          />
          {errors['patient.state'] && (
            <p className="text-[11px] text-rose-600 mt-1">{errors['patient.state']}</p>
          )}
        </div>

        {/* Payer */}
        <div>
          <label className="block font-semibold text-slate-700 mb-1">
            Payer / Plan <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            placeholder="e.g. Medicare"
            value={patient.payer || ''}
            onChange={(e) => updateField('payer', e.target.value)}
            className={`w-full px-3 py-2 rounded-lg border ${
              errors['patient.payer'] ? 'border-rose-400 bg-rose-50/40' : 'border-slate-200'
            } text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500`}
          />
          {errors['patient.payer'] && (
            <p className="text-[11px] text-rose-600 mt-1">{errors['patient.payer']}</p>
          )}
        </div>
      </div>
    </div>
  );
}
