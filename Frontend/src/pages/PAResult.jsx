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
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

export default function PAResult() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [record, setRecord] = useState(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

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

  // Strip backend technical codes like [ARTICLE_CRITERIA_SATISFIED] from the human-readable narrative.
  const cleanNarrative = (reasonText) => {
    if (!reasonText) return 'The submitted medical service has been evaluated against applicable Medicare policies.';
    return reasonText.replace(/\[[A-Z0-9_]+\]/g, '').trim();
  };

  const narrativeText = cleanNarrative(record.reason);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
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
              Clinical Evaluation Report
            </h2>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={handlePrint}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded-xl shadow-sm transition-colors"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print Report</span>
          </button>
        </div>
      </div>

      {/* 1. Primary Authorization Decision Card */}
      <div className="bg-white/90 backdrop-blur-xl border-2 border-slate-200/80 shadow-lg rounded-3xl p-6 sm:p-8 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
              Prior Authorization Decision
            </span>
            <div className="flex items-center gap-3 pt-1">
              <DecisionBadge decision={decision} size="xl" />
            </div>
          </div>

          {/* Criteria Evaluation Summary Badges */}
          <div className="flex items-center gap-2.5">
            <div className="px-3.5 py-2 rounded-2xl bg-emerald-50 border border-emerald-200 text-center">
              <span className="block text-xs font-bold text-emerald-800">
                {record.summary?.satisfied ?? (record.criteria?.filter(c => c.status === 'SATISFIED').length || 0)}
              </span>
              <span className="text-[10px] font-semibold text-emerald-600 uppercase tracking-wider">Satisfied</span>
            </div>
            <div className="px-3.5 py-2 rounded-2xl bg-rose-50 border border-rose-200 text-center">
              <span className="block text-xs font-bold text-rose-800">
                {record.summary?.not_satisfied ?? (record.criteria?.filter(c => c.status === 'NOT_SATISFIED').length || 0)}
              </span>
              <span className="text-[10px] font-semibold text-rose-600 uppercase tracking-wider">Not Satisfied</span>
            </div>
            <div className="px-3.5 py-2 rounded-2xl bg-amber-50 border border-amber-200 text-center">
              <span className="block text-xs font-bold text-amber-800">
                {record.summary?.unknown ?? (record.criteria?.filter(c => c.status === 'UNKNOWN').length || 0)}
              </span>
              <span className="text-[10px] font-semibold text-amber-600 uppercase tracking-wider">Unknown</span>
            </div>
          </div>
        </div>

        {/* Actionable Callouts */}
        {decision === 'APPROVE' && (
          <div className="p-4 rounded-2xl bg-emerald-50/80 border border-emerald-200 flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <span className="text-xs font-semibold text-emerald-900">
              All mandatory policy criteria and documentation requirements have been satisfied.
            </span>
          </div>
        )}

        {decision === 'DENY' && (
          <div className="p-4 rounded-2xl bg-rose-50/80 border border-rose-200 space-y-2">
            <div className="flex items-center gap-2 text-rose-800 font-bold text-xs uppercase tracking-wider">
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              <span>Failed Mandatory Requirements:</span>
            </div>
            <ul className="list-disc list-inside space-y-1 text-xs text-rose-900 font-medium ml-1">
              {(record.criteria || [])
                .filter(c => c.status === 'NOT_SATISFIED' && c.mandatory)
                .map((c, i) => (
                  <li key={i}>{c.requirement || c.criterion}</li>
                ))}
              {(!record.criteria || !record.criteria.some(c => c.status === 'NOT_SATISFIED')) && (
                <li>{record.reason}</li>
              )}
            </ul>
          </div>
        )}

        {(decision === 'NEED_MORE_INFORMATION' || (record.missing_information && record.missing_information.length > 0)) && (
          <div className="p-4 rounded-2xl bg-amber-50/80 border border-amber-200 space-y-2">
            <div className="flex items-center gap-2 text-amber-800 font-bold text-xs uppercase tracking-wider">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>Additional Documentation / Information Required:</span>
            </div>
            <ul className="list-disc list-inside space-y-1 text-xs text-amber-900 font-medium ml-1">
              {record.missing_information && record.missing_information.length > 0 ? (
                record.missing_information.map((item, i) => <li key={i}>{item}</li>)
              ) : (
                (record.criteria || [])
                  .filter(c => c.status === 'UNKNOWN' && c.mandatory)
                  .map((c, i) => <li key={i}>{c.requirement || c.criterion}</li>)
              )}
            </ul>
          </div>
        )}

        {/* Reason / Narrative */}
        <div className="space-y-2">
          <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            Clinical Explanation Narrative
          </h4>
          <p className="text-sm font-medium text-slate-700 leading-relaxed bg-slate-50 p-4 rounded-2xl border border-slate-200/60 shadow-inner">
            {narrativeText}
          </p>
        </div>
      </div>

      {/* 2. Policy Requirements & Clinical Evidence */}
      <div className="bg-white/90 backdrop-blur-xl border border-slate-200/80 shadow-sm rounded-3xl p-6 sm:p-8 space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <FileCheck2 className="w-5 h-5 text-indigo-600" />
            <h3 className="text-sm font-bold text-slate-800 tracking-tight">
              Policy Requirements & Clinical Evidence Evaluation
            </h3>
          </div>
          <span className="text-xs font-semibold text-slate-500">
            {(record.criteria || record.policy_requirements || []).length} Criteria Evaluated
          </span>
        </div>

        <CriteriaList criteria={record.criteria || record.policy_requirements} />
      </div>

      {/* 3. Submitted Request Summary Grid */}
      <div className="bg-white/80 backdrop-blur-xl border border-slate-200/80 shadow-sm rounded-3xl p-6 sm:p-8 space-y-5">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
          <FileText className="w-5 h-5 text-indigo-600" />
          <h3 className="text-sm font-bold text-slate-800 tracking-tight">
            Submitted Clinical Request Summary
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {/* Procedure */}
          <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-50 to-white border border-slate-200/60 shadow-sm space-y-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Procedure</span>
            <div className="font-mono font-bold text-sm text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-200 inline-block">
              {record.procedure_code || record.service?.procedure_code || 'N/A'}
            </div>
          </div>

          {/* Diagnosis Codes */}
          <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-50 to-white border border-slate-200/60 shadow-sm space-y-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Diagnoses</span>
            <div className="flex flex-wrap gap-1">
              {(record.diagnosis_codes || record.diagnoses?.map((d) => d.icd10_code || d.source_code) || ['N/A']).map((code, i) => (
                <span key={i} className="font-mono font-bold text-sm text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  {code}
                </span>
              ))}
            </div>
          </div>

          {/* State & Jurisdiction */}
          <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-50 to-white border border-slate-200/60 shadow-sm space-y-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Jurisdiction</span>
            <div className="flex items-center gap-1.5 font-bold text-slate-700 text-sm">
              <MapPin className="w-4 h-4 text-purple-600" />
              <span>{record.state || record.patient?.state || 'National'}</span>
            </div>
          </div>

          {/* Patient Context */}
          <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-50 to-white border border-slate-200/60 shadow-sm space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Patient Context</span>
            <div className="text-slate-600 text-xs space-y-0.5">
              <div>Age: <span className="font-bold text-slate-800">{record.patient_age || record.patient?.age || 'N/A'}</span></div>
              <div>Date: <span className="font-bold text-slate-800">{formatDate(record.service_date || record.created_at)}</span></div>
            </div>
          </div>
        </div>

        {/* Clinical Notes snippet if present */}
        {record.clinical_notes && (
          <div className="pt-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
              Submitted Medical Justification / Clinical Documentation
            </span>
            <p className="text-xs text-slate-600 bg-slate-50 p-4 rounded-2xl border border-slate-200/60 shadow-inner leading-relaxed italic">
              "{record.clinical_notes}"
            </p>
          </div>
        )}
      </div>

      {/* 4. Advanced Technical AI Adjudication Details (Collapsible) */}
      <div className="mt-8 relative">
        <div className="absolute inset-0 bg-gradient-to-r from-sky-400 to-indigo-500 blur-xl opacity-15 rounded-3xl"></div>
        <div className="relative bg-white/90 backdrop-blur-xl border-2 border-indigo-100/80 shadow-xl shadow-indigo-900/5 rounded-3xl overflow-hidden transition-all duration-300">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="w-full flex items-center justify-between p-6 sm:p-8 bg-gradient-to-r from-slate-50 to-white hover:from-indigo-50/50 hover:to-white transition-all group focus:outline-none focus:ring-4 focus:ring-indigo-500/10"
          >
            <div className="flex items-center gap-4 sm:gap-5">
              <div className="p-3.5 bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-2xl shadow-md group-hover:scale-110 group-hover:shadow-lg group-hover:shadow-indigo-500/30 transition-all duration-300">
                <Activity className="w-6 h-6" />
              </div>
              <div className="text-left">
                <h3 className="text-base sm:text-lg font-extrabold text-slate-800 group-hover:text-indigo-700 transition-colors">
                  View Detailed Technical Logs & Audit Trail
                </h3>
                <p className="text-[11px] sm:text-xs text-slate-500 mt-1 max-w-xl">
                  Expand to see the full Evidence Fusion matrix, RAG references, and CMS Policy Hierarchy paths.
                </p>
              </div>
            </div>
            <div className="w-10 h-10 rounded-full bg-indigo-50 flex items-center justify-center group-hover:bg-indigo-100 transition-colors flex-shrink-0">
              {showAdvanced ? (
                <ChevronUp className="w-5 h-5 text-indigo-600" />
              ) : (
                <ChevronDown className="w-5 h-5 text-indigo-600" />
              )}
            </div>
          </button>

        {showAdvanced && (
          <div className="p-6 sm:p-8 space-y-8 bg-white border-t border-slate-200/60 animate-in slide-in-from-top-4 fade-in duration-300">
            {/* Governing Policy Hierarchy Path */}
            <PolicyPathDisplay policyPath={record.policy_path} policies={record.policies} />

            {/* Evidence Fusion Breakdown */}
            <EvidenceFusionPanel
              fusionResult={record.evidence_fusion_result}
              criteria={record.criteria}
              decisionBasis={record.decision_basis}
            />

            {/* Matched Evidence Cards */}
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

            {/* Agentic Semantic Evaluation Visualization */}
            <AgentEvaluationPanel criteria={record.criteria} />

            {/* RAG Policy Passage References */}
            <RagEvidenceSection ragEvidence={record.rag_evidence} />
          </div>
        )}
      </div>
      </div>

    </div>
  );
}
