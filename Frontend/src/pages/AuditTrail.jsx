import React, { useState, useEffect } from 'react';
import { getStoredPARequests } from '../utils/storage';
import { formatDateTime } from '../utils/formatters';
import DecisionBadge from '../components/common/DecisionBadge';
import {
  GitFork,
  FileCheck2,
  BookOpen,
  Scale,
  Cpu,
  CheckCircle2,
  ChevronRight,
  Shield,
  Layers,
  ArrowDown,
} from 'lucide-react';

export default function AuditTrail() {
  const [requests, setRequests] = useState([]);
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => {
    const loaded = getStoredPARequests();
    setRequests(loaded);
    if (loaded.length > 0) {
      setSelectedId(loaded[0].pa_request_id);
    }
  }, []);

  const activeRequest = requests.find((r) => r.pa_request_id === selectedId) || requests[0];
  const pa = activeRequest?.pa_requests ? activeRequest.pa_requests[0] : activeRequest;

  const getTimelineSteps = (record) => {
    if (!record) return [];
    const dateStr = record.request?.request_date || record.created_at || new Date().toISOString();

    return [
      {
        step: 1,
        title: 'Request Intake & Normalization',
        phase: 'Intake Pipeline',
        icon: FileCheck2,
        status: 'Completed',
        timestamp: dateStr,
        details: [
          `PA Request ID: ${record.pa_request_id}`,
          `Patient: ${record.patient?.patient_id} (Age ${record.patient?.age}, State ${record.patient?.state})`,
          `Procedure Code: ${record.service?.procedure_code || 'Mapping Required'} (${record.service?.procedure_code_system || 'HCPCS/CPT'})`,
          `Primary Diagnosis: ${record.diagnoses?.[0]?.source_code || 'Unspecified'} (${record.diagnoses?.[0]?.description || 'N/A'})`,
        ],
        explanation:
          'Input payload received, clinical codes normalized, and patient jurisdiction contextualized.',
      },
      {
        step: 2,
        title: 'CMS Coverage Evidence Resolution',
        phase: 'Policy Resolver',
        icon: BookOpen,
        status: record.policies?.length > 0 ? 'Policies Resolved' : 'No Direct Policy Match',
        timestamp: dateStr,
        details:
          record.policies?.length > 0
            ? record.policies.map(
                (p) => `${p.policy_type} ${p.policy_id}: ${p.title || 'Coverage Determination'}`
              )
            : ['No active LCD/NCD candidate referenced procedure directly.'],
        explanation:
          'Queried local CMS Medicare Coverage Database cache and resolved applicable Local and National determinations.',
      },
      {
        step: 3,
        title: 'Deterministic Code & Criteria Evaluation',
        phase: 'Evaluation Engine',
        icon: Scale,
        status: 'Evaluated',
        timestamp: dateStr,
        details: [
          `Deterministic Procedure Match: ${record.service?.procedure_code ? 'MATCHED' : 'UNMAPPED'}`,
          `Diagnosis Code Match: ${record.diagnoses?.[0]?.icd10_code || record.diagnoses?.[0]?.source_code}`,
          `Criteria Evaluated: ${record.criteria?.length || 0} policy conditions checked`,
        ],
        explanation:
          'Strict comparison of procedure and diagnosis codes against structured LCD/Article inclusion and exclusion lists.',
      },
      {
        step: 4,
        title: 'Evidence Fusion & Policy Precedence',
        phase: 'Evidence Fusion',
        icon: Layers,
        status: 'Fused',
        timestamp: dateStr,
        details: [
          `Intermediate Coverage State: ${record.evidence_fusion_result || (record.decision === 'APPROVED' ? 'COVERED' : 'NOT_ADDRESSED')}`,
          `Policy Jurisdiction: ${record.patient?.state || 'TX'} MAC Novitas J5 / National`,
          `Precedence: NCD > LCD > Billing & Coding Article`,
        ],
        explanation:
          'Aggregated deterministic SQL checks and semantic criteria into an intermediate coverage determination.',
      },
      {
        step: 5,
        title: 'Final Adjudication & Decision Recommendation',
        phase: 'Decision Engine',
        icon: Shield,
        status: 'Finalized',
        timestamp: dateStr,
        details: [
          `Public Decision: ${record.decision || 'PENDING_REVIEW'}`,
          `Evidence Score: ${Math.round((record.evidence_score || 0.8) * 100)}% Deterministic Completeness`,
          `Prior Auth Required: ${record.requires_prior_authorization ? 'Yes' : 'Determined by MAC'}`,
        ],
        explanation:
          record.decision_basis ||
          record.reason ||
          'Deterministic policy recommendation generated with complete audit trail.',
      },
    ];
  };

  const steps = getTimelineSteps(pa);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="pb-2 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Deterministic Decision Audit Trail
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Traceable step-by-step verification pipeline from intake to final coverage recommendation
          </p>
        </div>

        {/* Case selector dropdown */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-600">Select Case:</span>
          <select
            value={selectedId || ''}
            onChange={(e) => setSelectedId(e.target.value)}
            className="px-3 py-1.5 text-xs font-mono font-semibold rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500"
          >
            {requests.map((r) => {
              const paItem = r.pa_requests ? r.pa_requests[0] : r;
              return (
                <option key={paItem.pa_request_id} value={paItem.pa_request_id}>
                  {paItem.pa_request_id} - {paItem.patient?.patient_id} ({paItem.decision})
                </option>
              );
            })}
          </select>
        </div>
      </div>

      {/* Case Summary Bar */}
      {pa && (
        <div className="healthcare-card p-4 sm:p-5 bg-slate-900 text-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-md">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-sky-400 bg-sky-950 px-2 py-0.5 rounded border border-sky-800">
                {pa.pa_request_id}
              </span>
              <span className="text-xs text-slate-300">
                Patient {pa.patient?.patient_id} • {pa.patient?.state}
              </span>
            </div>
            <h3 className="text-sm font-semibold text-slate-100">
              {pa.service?.service_description || 'Prior Authorization Medical Review'}
            </h3>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <span className="text-[11px] text-slate-400 block">Decision Outcome</span>
              <span className="text-xs font-bold text-sky-300">{pa.decision}</span>
            </div>
            <DecisionBadge decision={pa.decision} size="md" />
          </div>
        </div>
      )}

      {/* Audit Pipeline Steps */}
      <div className="space-y-6 relative before:absolute before:inset-0 before:left-5 sm:before:left-6 before:w-0.5 before:bg-slate-200 before:z-0">
        {steps.map((item, index) => {
          const Icon = item.icon;
          return (
            <div key={item.step} className="relative z-10 flex items-start gap-4 sm:gap-6">
              {/* Step Circle */}
              <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-2xl bg-white border-2 border-sky-600 text-sky-700 flex items-center justify-center font-bold text-sm shadow-sm flex-shrink-0">
                <Icon className="w-5 h-5" />
              </div>

              {/* Step Card */}
              <div className="flex-1 healthcare-card p-5 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-sky-50 text-sky-700 border border-sky-200">
                      Step {item.step}: {item.phase}
                    </span>
                    <h4 className="text-sm font-bold text-slate-900">{item.title}</h4>
                  </div>
                  <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    {item.status}
                  </span>
                </div>

                {/* Details List */}
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 space-y-1 text-xs font-mono text-slate-700">
                  {item.details.map((detail, idx) => (
                    <div key={idx} className="flex items-start gap-1.5">
                      <ChevronRight className="w-3.5 h-3.5 text-sky-500 flex-shrink-0 mt-0.5" />
                      <span>{detail}</span>
                    </div>
                  ))}
                </div>

                {/* Explanation narrative */}
                <p className="text-xs text-slate-600 leading-relaxed">
                  <span className="font-semibold text-slate-800">Pipeline Rationale: </span>
                  {item.explanation}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
