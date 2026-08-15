import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getPARequestById } from '../utils/storage';
import { formatDate } from '../utils/formatters';
import DecisionBadge from '../components/common/DecisionBadge';
import CriteriaList from '../components/evidence/CriteriaList';
import EvidenceCard from '../components/evidence/EvidenceCard';
import PolicyPathDisplay from '../components/result/PolicyPathDisplay';
import RagEvidenceSection from '../components/result/RagEvidenceSection';
import EvidenceFusionPanel from '../components/result/EvidenceFusionPanel';
import AgentEvaluationPanel from '../components/result/AgentEvaluationPanel';
import {
  ShieldCheck,
  User,
  Stethoscope,
  Activity,
  FileCheck2,
  BookOpen,
  ArrowLeft,
  Printer,
  AlertTriangle,
  FileText,
  Clock,
  Scale,
  Sparkles,
  Info,
  MapPin,
  Calendar,
  CheckCircle2,
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
          No active prior authorization evaluation record found for ID: <span className="font-mono font-bold">{id}</span>.
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

  const decision = record.decision || 'PENDING_REVIEW';
  const evidenceScore = record.evidence_score !== undefined && record.evidence_score !== null ? record.evidence_score : 0.85;

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
                {record.pa_request_id}
              </span>
              <span className="text-xs text-slate-500">
                Evaluated {formatDate(record.created_at || record.service_date)}
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight mt-0.5">
              Prior Authorization Clinical Evaluation Report
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
        </div>
      </div>

      {/* 1. Primary Authorization Decision Card */}
      <div className="healthcare-card p-6 sm:p-8 bg-white border-2 border-slate-200 shadow-sm space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="space-y-1">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
              Authorization Coverage Decision
            </span>
            <div className="flex items-center gap-3 pt-1">
              <DecisionBadge decision={decision} size="xl" />
            </div>
          </div>

          {/* Evidence Score Indicator */}
          {evidenceScore != null && (
            <div className="flex items-center gap-4 bg-slate-50 p-3.5 rounded-2xl border border-slate-200/80">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 block">
                  Policy Evidence Score
                </span>
                <span className="text-xl font-bold text-slate-900 font-mono">
                  {Math.round(evidenceScore * 100)}%
                </span>
              </div>
              <div className="w-11 h-11 rounded-xl bg-sky-100 flex items-center justify-center text-sky-700 font-bold border border-sky-200">
                <Scale className="w-5 h-5" />
              </div>
            </div>
          )}
        </div>

        {/* Reason / Narrative */}
        <div className="space-y-2">
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Clinical Explanation Narrative
          </h4>
          <p className="text-sm font-medium text-slate-800 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-200/80">
            {record.reason || 'The submitted medical service has been evaluated against applicable Medicare policies.'}
          </p>
        </div>
      </div>

      {/* 2. Triage Request Summary Grid */}
      <div className="healthcare-card p-6 space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
          <FileText className="w-5 h-5 text-sky-600" />
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Submitted Clinical Request Summary
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          {/* Procedure */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-1.5">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Requested Procedure
            </span>
            <div className="font-mono font-bold text-sm text-sky-700 bg-white px-2.5 py-1 rounded border border-sky-200 inline-block">
              CPT/HCPCS {record.procedure_code || record.service?.procedure_code || 'N/A'}
            </div>
            {record.service?.service_description && (
              <p className="text-slate-600 text-[11px] leading-snug pt-1">
                {record.service.service_description}
              </p>
            )}
          </div>

          {/* Diagnosis Codes */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-1.5">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Primary ICD-10 Diagnoses
            </span>
            <div className="flex flex-wrap gap-1">
              {(record.diagnosis_codes || record.diagnoses?.map((d) => d.icd10_code || d.source_code) || ['N/A']).map((code, i) => (
                <span key={i} className="font-mono font-bold text-xs text-emerald-800 bg-white px-2 py-0.5 rounded border border-emerald-200">
                  {code}
                </span>
              ))}
            </div>
          </div>

          {/* State & Jurisdiction */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-1.5">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              State & Jurisdiction
            </span>
            <div className="flex items-center gap-1.5 font-bold text-slate-800 text-sm">
              <MapPin className="w-4 h-4 text-purple-600" />
              <span>State: {record.state || record.patient?.state || 'National Scope'}</span>
            </div>
          </div>

          {/* Patient Context */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-1.5">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Patient Context & Date
            </span>
            <div className="text-slate-700 space-y-0.5">
              <div>
                Age: <span className="font-semibold text-slate-900">{record.patient_age || record.patient?.age || 'N/A'}</span>
              </div>
              <div>
                Service Date: <span className="font-semibold text-slate-900">{formatDate(record.service_date || record.created_at)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Clinical Notes snippet if present */}
        {record.clinical_notes && (
          <div className="pt-2">
            <span className="text-[11px] font-bold text-slate-500 block mb-1">
              Submitted Medical Justification / Clinical Documentation:
            </span>
            <p className="text-xs text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-200/60 leading-relaxed italic">
              "{record.clinical_notes}"
            </p>
          </div>
        )}
      </div>

      {/* 3. Governing Policy Hierarchy Path */}
      <PolicyPathDisplay policyPath={record.policy_path} policies={record.policies} />

      {/* 4. Evidence Fusion Breakdown */}
      <EvidenceFusionPanel
        fusionResult={record.evidence_fusion_result}
        criteria={record.criteria}
        decisionBasis={record.decision_basis}
      />

      {/* 5. Matched Evidence Cards */}
      {record.evidence && record.evidence.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Deterministic Code & Jurisdiction Evidence ({record.evidence.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {record.evidence.map((ev, i) => (
              <EvidenceCard key={i} evidence={ev} />
            ))}
          </div>
        </div>
      )}

      {/* 6. Agentic Semantic Evaluation Visualization */}
      <AgentEvaluationPanel criteria={record.criteria} />

      {/* 7. RAG Policy Passage References */}
      <RagEvidenceSection ragEvidence={record.rag_evidence} />

      {/* 8. Full Policy Criteria List */}
      <div className="healthcare-card p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              All Evaluated Policy Criteria Rules ({record.criteria?.length || 0})
            </h3>
          </div>
        </div>

        <CriteriaList criteria={record.criteria} />
      </div>

      {/* 9. Missing Information Required */}
      {record.missing_information && record.missing_information.length > 0 && (
        <div className="healthcare-card p-5 bg-amber-50/50 border border-amber-200 space-y-2">
          <div className="flex items-center gap-2 text-amber-800 font-bold text-xs uppercase tracking-wider">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>Missing Information Required:</span>
          </div>
          <ul className="list-disc list-inside space-y-1 text-xs text-amber-900 font-medium">
            {record.missing_information.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
