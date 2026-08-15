import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getPARequestById } from '../utils/storage';
import { formatDate, formatScorePercent } from '../utils/formatters';
import DecisionBadge from '../components/common/DecisionBadge';
import StatusBadge from '../components/common/StatusBadge';
import CodeChip from '../components/common/CodeChip';
import EvidenceCard from '../components/evidence/EvidenceCard';
import CriteriaList from '../components/evidence/CriteriaList';
import {
  ShieldCheck,
  User,
  Stethoscope,
  Activity,
  FileCheck2,
  BookOpen,
  ArrowLeft,
  Printer,
  RotateCcw,
  AlertTriangle,
  CheckCircle,
  FileText,
  Clock,
  Layers,
  Scale,
  Sparkles,
  Info,
} from 'lucide-react';

export default function PAResult() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [record, setRecord] = useState(null);

  useEffect(() => {
    if (id) {
      const found = getPARequestById(id);
      if (found) {
        setRecord(found);
      }
    }
  }, [id]);

  if (!record) {
    return (
      <div className="healthcare-card p-12 text-center space-y-4">
        <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto" />
        <h3 className="text-lg font-bold text-slate-800">Prior Authorization Record Not Found</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          No active prior authorization request found for ID: <span className="font-mono font-bold">{id}</span>.
        </p>
        <div className="pt-2">
          <Link
            to="/history"
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-sky-700 bg-sky-50 hover:bg-sky-100 rounded-xl border border-sky-200 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Return to PA History</span>
          </Link>
        </div>
      </div>
    );
  }

  const pa = record.pa_requests ? record.pa_requests[0] : record;
  const decision = pa.decision || 'PENDING_REVIEW';
  const evidenceScore = pa.evidence_score !== undefined ? pa.evidence_score : 0.85;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => navigate('/history')}
            className="p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            title="Back to History"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                {pa.pa_request_id}
              </span>
              <span className="text-xs text-slate-500">
                Submitted {formatDate(pa.request?.request_date || pa.created_at)}
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight mt-0.5">
              Prior Authorization Evaluation Result
            </h2>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={handlePrint}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded-xl shadow-2xs transition-colors"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print Report</span>
          </button>

          <Link
            to="/audit"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-sky-700 bg-sky-50 hover:bg-sky-100 border border-sky-200 rounded-xl transition-colors"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>View Audit Timeline</span>
          </Link>
        </div>
      </div>

      {/* 1. Large Authorization Decision Card */}
      <div className="healthcare-card p-6 sm:p-8 bg-white border-2 border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="space-y-1">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
              Authorization Coverage Decision
            </span>
            <div className="flex items-center gap-3">
              <DecisionBadge decision={decision} size="xl" />
            </div>
          </div>

          {/* Evidence Score Indicator */}
          <div className="flex items-center gap-4 bg-slate-50 p-3 rounded-xl border border-slate-200/80">
            <div>
              <span className="text-[11px] font-semibold text-slate-500 block">
                Evidence Completeness
              </span>
              <span className="text-lg font-bold text-slate-900 font-mono">
                {formatScorePercent(evidenceScore)}
              </span>
            </div>
            <div className="w-12 h-12 rounded-full bg-sky-100 flex items-center justify-center text-sky-700 font-bold text-xs border border-sky-200">
              <Scale className="w-6 h-6" />
            </div>
          </div>
        </div>

        {/* Reason / Decision Basis Statement */}
        <div className="space-y-2">
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Decision Explanation
          </h4>
          <p className="text-sm font-medium text-slate-800 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-200/80">
            {pa.reason || 'The submitted medical service has been evaluated against applicable Medicare policies.'}
          </p>
          {pa.decision_basis && (
            <p className="text-xs text-slate-600 leading-relaxed italic px-2">
              <span className="font-semibold text-slate-700">Adjudication Basis: </span>
              {pa.decision_basis}
            </p>
          )}
        </div>
      </div>

      {/* 2. Request Summary Grid */}
      <div className="healthcare-card p-6 space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
          <FileText className="w-5 h-5 text-sky-600" />
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
            Prior Authorization Request Summary
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          {/* Patient Details */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-2">
            <div className="flex items-center gap-1.5 font-bold text-slate-700">
              <User className="w-4 h-4 text-sky-600" />
              <span>Patient Profile</span>
            </div>
            <div className="space-y-1 text-slate-600">
              <div>
                <span className="text-slate-400 block">Patient ID:</span>
                <span className="font-semibold text-slate-800">{pa.patient?.patient_id}</span>
              </div>
              <div>
                <span className="text-slate-400 block">DOB / Age / Gender:</span>
                <span>
                  {formatDate(pa.patient?.date_of_birth)} • Age {pa.patient?.age} • {pa.patient?.gender}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block">State & Payer:</span>
                <span className="font-semibold text-slate-800">
                  {pa.patient?.state} • {pa.patient?.payer}
                </span>
              </div>
            </div>
          </div>

          {/* Provider Details */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-2">
            <div className="flex items-center gap-1.5 font-bold text-slate-700">
              <Stethoscope className="w-4 h-4 text-sky-600" />
              <span>Ordering Provider</span>
            </div>
            <div className="space-y-1 text-slate-600">
              <div>
                <span className="text-slate-400 block">Provider ID:</span>
                <span className="font-semibold text-slate-800">{pa.provider?.provider_id}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Specialty:</span>
                <span className="text-slate-800">{pa.provider?.specialty}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Organization:</span>
                <span className="font-semibold text-slate-800 leading-tight block truncate">
                  {pa.provider?.organization_name}
                </span>
              </div>
            </div>
          </div>

          {/* Service & Procedure */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-2 md:col-span-2">
            <div className="flex items-center gap-1.5 font-bold text-slate-700">
              <Activity className="w-4 h-4 text-sky-600" />
              <span>Requested Service & Procedure</span>
            </div>
            <p className="text-xs font-semibold text-slate-800 leading-relaxed">
              {pa.service?.service_description}
            </p>
            <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px] text-slate-600">
              <div>
                <span className="text-slate-400 mr-1">Code:</span>
                {pa.service?.procedure_code ? (
                  <span className="font-mono font-bold text-sky-700 bg-sky-50 px-1.5 py-0.2 rounded border border-sky-200">
                    CPT {pa.service.procedure_code}
                  </span>
                ) : (
                  <span className="font-mono font-semibold text-amber-700 bg-amber-50 px-1.5 py-0.2 rounded border border-amber-200">
                    Mapping Required
                  </span>
                )}
              </div>
              <div>
                <span className="text-slate-400 mr-1">Dates:</span>
                <span>{formatDate(pa.service?.start_date)}</span>
              </div>
              <div>
                <span className="text-slate-400 mr-1">Place:</span>
                <span>{pa.service?.place_of_service || 'Outpatient'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Code Validation & Clinical Diagnoses */}
      <div className="healthcare-card p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <FileCheck2 className="w-5 h-5 text-emerald-600" />
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
              Code Validation & Crosswalk Status
            </h3>
          </div>
          <span className="text-xs font-medium text-slate-500">
            {pa.diagnoses?.length || 0} Clinical Diagnosis Entries
          </span>
        </div>

        <div className="space-y-3">
          {pa.diagnoses && pa.diagnoses.length > 0 ? (
            pa.diagnoses.map((diag, index) => (
              <div
                key={index}
                className="p-4 rounded-xl bg-slate-50/70 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-800">{diag.description}</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-500 font-mono text-[11px]">
                    <span>Source: {diag.source_code} ({diag.source_code_system})</span>
                    {diag.icd10_code && (
                      <span className="text-emerald-700 font-semibold">
                        → ICD-10-CM: {diag.icd10_code}
                      </span>
                    )}
                  </div>
                </div>

                <div>
                  {diag.icd10_mapping_required ? (
                    <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                      Crosswalk Required
                    </span>
                  ) : (
                    <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      Validated ICD-10
                    </span>
                  )}
                </div>
              </div>
            ))
          ) : (
            <p className="text-xs text-slate-400 italic">No diagnoses registered on this record.</p>
          )}
        </div>
      </div>

      {/* 4. Policy Evidence & Matched Determinations */}
      <div className="healthcare-card p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-sky-600" />
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
              Governing Medicare Policy Evidence
            </h3>
          </div>
          <span className="text-xs font-medium text-slate-500">
            {pa.policies?.length || 0} Policies Matched
          </span>
        </div>

        {pa.policies && pa.policies.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {pa.policies.map((p, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl bg-sky-50/40 border border-sky-200 space-y-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-sky-800 bg-white px-2 py-0.5 rounded border border-sky-200">
                    {p.policy_type} {p.policy_id}
                  </span>
                  {p.article_id && (
                    <span className="font-mono text-slate-600 bg-white px-2 py-0.5 rounded border border-slate-200">
                      Article: {p.article_id}
                    </span>
                  )}
                </div>
                <h4 className="font-bold text-slate-900 text-sm leading-snug">{p.title}</h4>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-500 flex items-start gap-2">
            <Info className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
            <span>
              No Local or National Coverage Determination directly referenced the unmapped codes. Manual MAC contractor review recommended.
            </span>
          </div>
        )}
      </div>

      {/* 5. Clinical Evidence & Traceability Cards */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
          Evidence Traceability Items ({pa.evidence?.length || 0})
        </h3>
        {pa.evidence && pa.evidence.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {pa.evidence.map((ev, i) => (
              <EvidenceCard key={i} evidence={ev} />
            ))}
          </div>
        ) : (
          <div className="healthcare-card p-6 text-center text-xs text-slate-400">
            No itemized evidence pieces attached.
          </div>
        )}
      </div>

      {/* 6. Criteria Evaluation Breakdown */}
      <div className="healthcare-card p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
              Structured & Semantic Policy Criteria Evaluation
            </h3>
          </div>
        </div>

        <CriteriaList criteria={pa.criteria} />
      </div>

      {/* Missing Information / Warnings if present */}
      {pa.missing_information && pa.missing_information.length > 0 && (
        <div className="healthcare-card p-5 bg-amber-50/50 border border-amber-200 space-y-2">
          <div className="flex items-center gap-2 text-amber-800 font-bold text-xs uppercase tracking-wider">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>Missing Information Required:</span>
          </div>
          <ul className="list-disc list-inside space-y-1 text-xs text-amber-900 font-medium">
            {pa.missing_information.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
