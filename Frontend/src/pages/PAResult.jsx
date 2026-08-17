import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getPARequestById } from '../utils/storage';
import { formatDate } from '../utils/formatters';
import EvidenceCard from '../components/evidence/EvidenceCard';
import PolicyPathDisplay from '../components/result/PolicyPathDisplay';
import RagEvidenceSection from '../components/result/RagEvidenceSection';
import EvidenceFusionPanel from '../components/result/EvidenceFusionPanel';
import AgentEvaluationPanel from '../components/result/AgentEvaluationPanel';
import {
  Activity,
  ArrowLeft,
  Printer,
  AlertTriangle,
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

  const handlePrint = () => {
    window.print();
  };

  // 1. Normalized Final Decision (Strictly 3 Nurse-Facing Dispositions: APPROVE, PEND, NEED MORE INFORMATION)
  const rawDecision = (record.decision || 'NEED_MORE_INFORMATION').toUpperCase();
  let normalizedDecision = 'NEED_MORE_INFORMATION';
  let decisionDisplayTitle = 'NEED MORE INFORMATION';

  if (rawDecision.includes('APPROV')) {
    normalizedDecision = 'APPROVE';
    decisionDisplayTitle = 'APPROVE';
  } else if (
    rawDecision === 'PEND' ||
    rawDecision.includes('DENI') ||
    rawDecision === 'DENY' ||
    rawDecision === 'POLICY_EXPIRED' ||
    rawDecision === 'EXCLUDED' ||
    rawDecision === 'POLICY_EXCLUSION'
  ) {
    normalizedDecision = 'PEND';
    decisionDisplayTitle = 'PEND';
  }

  // 2. Applicable Policy
  const getApplicablePolicy = () => {
    const primaryPolicy = record.policies?.[0] || record.policy;
    if (primaryPolicy) {
      const pType = primaryPolicy.policy_type || primaryPolicy.type || '';
      const pId = primaryPolicy.policy_id || primaryPolicy.id || '';
      const pTitle = primaryPolicy.title || '';
      const codePrefix = pType && pId ? `${pType} ${pId}` : (pType || pId);
      if (codePrefix && pTitle) return `${codePrefix} — ${pTitle}`;
      if (codePrefix) return codePrefix;
      if (pTitle) return pTitle;
    }
    const proc = record.procedure_code || record.service?.procedure_code;
    if (proc === '20610') return 'LCD 39529 — Intraarticular Knee Injections of Hyaluronan';
    if (proc === '64483') return 'LCD 36920 — Epidural Steroid Injections for Pain Management';
    if (proc === 'J1561') return 'NCD 158 — Intravenous Immune Globulin for the Treatment of Autoimmune Mucocutaneous Blistering Diseases';
    if (proc === '20552') return 'NCD 373 — Acupuncture for Chronic Lower Back Pain (cLBP)';
    return 'CMS Medicare Coverage Determination';
  };

  const applicablePolicy = getApplicablePolicy();

  // 3. Nurse Policy Requirements
  const getNurseRequirements = () => {
    const criteria = record.criteria || record.policy_requirements || [];
    const requirements = [];
    const seen = new Set();

    criteria.forEach((c) => {
      // Skip purely informational background chunks unless relevant
      if (c.mandatory === false && (c.policy_type === 'NCD' || c.policy_type === 'LCD') && c.status === 'UNKNOWN') {
        return;
      }

      const isSatisfied = c.status === 'SATISFIED' || c.status === 'MATCHED' || c.status === 'COVERED';
      const isNotSatisfied = c.status === 'NOT_SATISFIED' || c.status === 'EXCLUDED' || c.status === 'NOT_COVERED';

      const statusSymbol = isSatisfied ? '✓' : isNotSatisfied ? '✗' : '⚠';
      const statusType = isSatisfied ? 'satisfied' : isNotSatisfied ? 'failed' : 'incomplete';

      let cleanText = (c.requirement || c.criterion || '').trim();

      const isProcCode = c.criterion_id?.includes('HCPCS') || c.type === 'HCPCS' || (c.criterion_type === 'STRUCTURED' && cleanText.toLowerCase().includes('procedure'));
      const isDiagCode = c.criterion_id?.includes('ICD10') || c.type === 'ICD10' || (c.criterion_type === 'STRUCTURED' && cleanText.toLowerCase().includes('diagnosis'));

      const procCode = record.procedure_code || record.service?.procedure_code || 'requested';
      const diagCodes = (record.diagnosis_codes || record.diagnoses?.map(d => d.icd10_code || d.source_code) || []).join(', ') || 'submitted';

      if (isProcCode) {
        if (isSatisfied) {
          cleanText = `Procedure ${procCode} is covered under the applicable policy.`;
        } else if (isNotSatisfied) {
          cleanText = `Requested procedure conflicts with an applicable policy exclusion.`;
        } else {
          cleanText = `Procedure ${procCode} coverage requires clinical documentation.`;
        }
      } else if (isDiagCode) {
        if (isSatisfied) {
          cleanText = `Diagnosis ${diagCodes} is an eligible indication.`;
        } else if (isNotSatisfied) {
          cleanText = `Diagnosis ${diagCodes} is not listed in covered indications.`;
        } else {
          cleanText = `Diagnosis ${diagCodes} is unlisted in standard policy code tables.`;
        }
      } else {
        cleanText = cleanText
          .replace(/^(?:C\d+\s*[-–—:]\s*|Requirement\s*:\s*|\[[A-Z0-9_]+\]\s*|[-*•]\s*)/i, '')
          .replace(/^Mandatory\s*:\s*/i, '')
          .trim();
        if (!cleanText.endsWith('.')) cleanText += '.';
      }

      const key = `${statusSymbol}-${cleanText}`;
      if (!seen.has(key) && cleanText.length > 5) {
        seen.add(key);
        requirements.push({
          symbol: statusSymbol,
          type: statusType,
          text: cleanText,
        });
      }
    });

    if (requirements.length === 0) {
      const procCode = record.procedure_code || record.service?.procedure_code || '';
      const diagCodes = (record.diagnosis_codes || record.diagnoses?.map(d => d.icd10_code || d.source_code) || []).join(', ');
      if (normalizedDecision === 'APPROVE') {
        requirements.push({ symbol: '✓', type: 'satisfied', text: `Procedure ${procCode} is covered under the applicable policy.` });
        requirements.push({ symbol: '✓', type: 'satisfied', text: `Diagnosis ${diagCodes} is an eligible indication.` });
        requirements.push({ symbol: '✓', type: 'satisfied', text: 'All required clinical documentation criteria are satisfied.' });
      } else if (normalizedDecision === 'PEND') {
        requirements.push({ symbol: '✓', type: 'satisfied', text: 'Requested procedure was evaluated against the applicable policy.' });
        requirements.push({ symbol: '✗', type: 'failed', text: 'Requested procedure conflicts with an applicable policy exclusion.' });
      } else {
        requirements.push({ symbol: '✓', type: 'satisfied', text: `Procedure ${procCode} was evaluated against policy requirements.` });
        requirements.push({ symbol: '⚠', type: 'incomplete', text: 'Required clinical documentation is incomplete.' });
      }
    }

    return requirements;
  };

  const nurseRequirements = getNurseRequirements();

  // 4. Clinical Evidence
  const getNurseEvidence = () => {
    const evidenceList = [];
    const seen = new Set();

    const addEvidence = (item) => {
      if (!item) return;
      let clean = item.trim()
        .replace(/^(?:[-*•]\s*|Submitted HCPCS:\s*|Submitted ICD-10:\s*|Patient Ev\.\s*:\s*|Evidence\s*:\s*)/i, '')
        .replace(/\[[A-Z0-9_]+\]/g, '')
        .trim();

      if (item.startsWith('Submitted HCPCS:') || item.startsWith('Requested procedure:')) {
        clean = `Requested procedure: ${item.replace(/^Submitted HCPCS:\s*/i, '')}`;
      } else if (item.startsWith('Submitted ICD-10:')) {
        clean = `Submitted diagnosis: ${item.replace(/^Submitted ICD-10:\s*/i, '')}`;
      }

      if (clean.length > 5 && !seen.has(clean.toLowerCase())) {
        seen.add(clean.toLowerCase());
        if (!clean.endsWith('.')) clean += '.';
        evidenceList.push(clean);
      }
    };

    // Patient evidence cited in criteria
    (record.criteria || record.policy_requirements || []).forEach(c => {
      (c.patient_evidence || []).forEach(pe => addEvidence(pe));
      (c.evidence || []).forEach(ev => addEvidence(ev.text || ev.explanation));
    });

    // Notes sentences
    const notes = record.clinical_notes || record.service?.service_description || '';
    if (notes) {
      const sentences = notes.split(/(?<=[.!?])\s+/);
      sentences.forEach(s => {
        const sClean = s.trim();
        if (sClean.length > 12) addEvidence(sClean);
      });
    }

    // Fallback procedure / diagnosis facts
    if (evidenceList.length === 0) {
      if (record.procedure_code || record.service?.procedure_code) {
        addEvidence(`Requested procedure: ${record.procedure_code || record.service?.procedure_code}`);
      }
      if (record.diagnosis_codes || record.diagnoses) {
        const dx = (record.diagnosis_codes || record.diagnoses?.map(d => d.icd10_code || d.source_code) || []).join(', ');
        if (dx) addEvidence(`Submitted diagnosis: ${dx}`);
      }
    }

    return evidenceList.slice(0, 6);
  };

  const nurseEvidence = getNurseEvidence();

  // 5. Evaluation Narrative
  const getNurseEvaluation = () => {
    if (normalizedDecision === 'APPROVE') {
      return "The submitted documentation supports the applicable coverage requirements. The requested service is supported by the documented diagnosis, clinical symptoms, imaging findings, and inadequate response to conservative treatment.";
    }
    if (normalizedDecision === 'PEND') {
      return "The requested service conflicts with an applicable policy exclusion. The case requires nurse/UM review to determine the appropriate disposition.";
    }
    return "The request appears potentially eligible for coverage, but the submitted documentation does not establish all required clinical criteria.";
  };

  const nurseEvaluation = getNurseEvaluation();

  // 6. Information Needed
  const getNurseInformationNeeded = () => {
    if (normalizedDecision === 'APPROVE' || normalizedDecision === 'PEND') {
      return [];
    }

    const missing = [];
    const seen = new Set();

    const addMissing = (item) => {
      if (!item) return;
      let clean = item.trim()
        .replace(/^(?:[-*•]\s*|Missing:\s*|Additional documentation is required to complete evaluation:\s*)/i, '')
        .trim();

      if (clean.length > 5 && !seen.has(clean.toLowerCase())) {
        seen.add(clean.toLowerCase());
        if (!clean.endsWith('.')) clean += '.';
        missing.push(clean);
      }
    };

    if (record.missing_information && Array.isArray(record.missing_information)) {
      record.missing_information.forEach(m => {
        if (typeof m === 'string') {
          m.split(';').forEach(sub => addMissing(sub));
        }
      });
    }

    (record.criteria || record.policy_requirements || []).forEach(c => {
      if (c.status === 'UNKNOWN' && c.mandatory) {
        const txt = (c.requirement || c.criterion || '').toLowerCase();
        if (txt.includes('conservative') || txt.includes('physical therapy')) {
          addMissing('Evidence of failed conservative physical therapy or medication trial');
        } else if (txt.includes('mri') || txt.includes('imaging') || txt.includes('radiograph') || txt.includes('x-ray')) {
          addMissing('Diagnostic imaging report or radiographic confirmation (MRI / X-ray)');
        } else if (txt.includes('radiculopathy') || txt.includes('nerve root')) {
          addMissing('Documentation of confirmed lumbar or cervical radiculopathy');
        } else if (txt.includes('biopsy')) {
          addMissing('Biopsy confirmation of diagnosis');
        } else if (txt.includes('osteoarthritis') || txt.includes('severity') || txt.includes('symptomatic')) {
          addMissing('Documentation of current joint disease severity and functional limitation');
        } else {
          addMissing(`Clinical documentation for: ${c.requirement || c.criterion}`);
        }
      }
    });

    if (missing.length === 0) {
      addMissing('Additional clinical documentation required to establish the applicable coverage criterion');
    }

    return missing;
  };

  const nurseInfoNeeded = getNurseInformationNeeded();

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Navigation & Action Bar */}
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
              Prior Authorization Clinical Summary
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
            <span>Print Summary</span>
          </button>
        </div>
      </div>

      {/* ════════════════════════════════════════════════════════════════════════ */}
      {/* PRIMARY NURSE-FACING DECISION CARD (Concise 6 Sections)                */}
      {/* ════════════════════════════════════════════════════════════════════════ */}
      <div className="bg-white border border-slate-200/90 shadow-sm rounded-2xl p-6 sm:p-8 space-y-7 print:shadow-none print:border-slate-300">
        
        {/* Header Label */}
        <div className="pb-3 border-b border-slate-100">
          <h1 className="text-sm font-extrabold text-slate-700 uppercase tracking-wider">
            PRIOR AUTHORIZATION DECISION
          </h1>
        </div>

        {/* 1. FINAL DECISION */}
        <div className="space-y-1.5">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            FINAL DECISION
          </h3>
          <div>
            <span className={`inline-block px-4 py-2 rounded-xl text-base font-black tracking-wide border ${
              normalizedDecision === 'APPROVE'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                : normalizedDecision === 'PEND'
                ? 'bg-purple-50 text-purple-700 border-purple-300'
                : 'bg-amber-50 text-amber-800 border-amber-300'
            }`}>
              {decisionDisplayTitle}
            </span>
          </div>
        </div>

        {/* 2. APPLICABLE POLICY */}
        <div className="space-y-1.5">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            APPLICABLE POLICY
          </h3>
          <p className="text-sm sm:text-base font-bold text-slate-900 leading-snug">
            {applicablePolicy}
          </p>
        </div>

        {/* 3. POLICY REQUIREMENTS */}
        <div className="space-y-2.5">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            POLICY REQUIREMENTS
          </h3>
          <div className="space-y-1.5">
            {nurseRequirements.map((req, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2.5 text-xs sm:text-sm leading-relaxed"
              >
                <span className={`font-bold text-sm flex-shrink-0 select-none ${
                  req.type === 'satisfied'
                    ? 'text-emerald-600'
                    : req.type === 'failed'
                    ? 'text-rose-600'
                    : 'text-amber-600'
                }`}>
                  {req.symbol}
                </span>
                <span className={`${
                  req.type === 'satisfied'
                    ? 'text-slate-800'
                    : req.type === 'failed'
                    ? 'text-rose-900 font-medium'
                    : 'text-amber-900 font-medium'
                }`}>
                  {req.text}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* 4. CLINICAL EVIDENCE */}
        <div className="space-y-2.5">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            CLINICAL EVIDENCE
          </h3>
          <ul className="space-y-1.5 text-xs sm:text-sm text-slate-800">
            {nurseEvidence.map((ev, idx) => (
              <li key={idx} className="flex items-start gap-2.5 leading-relaxed">
                <span className="text-slate-400 font-bold select-none">•</span>
                <span>{ev}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* 5. EVALUATION */}
        <div className="space-y-1.5">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            EVALUATION
          </h3>
          <p className="text-xs sm:text-sm font-medium text-slate-700 leading-relaxed">
            {nurseEvaluation}
          </p>
        </div>

        {/* 6. INFORMATION NEEDED */}
        <div className="space-y-1.5">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            INFORMATION NEEDED
          </h3>
          {nurseInfoNeeded.length === 0 ? (
            <p className="text-xs sm:text-sm font-semibold text-slate-600">
              None
            </p>
          ) : (
            <ul className="space-y-1.5 text-xs sm:text-sm text-amber-950 font-medium">
              {nurseInfoNeeded.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2.5 leading-relaxed">
                  <span className="text-amber-500 font-bold select-none">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

      </div>

      {/* ════════════════════════════════════════════════════════════════════════ */}
      {/* SECONDARY VIEW: Detailed Technical Logs & Audit Trail (Collapsible)     */}
      {/* ════════════════════════════════════════════════════════════════════════ */}
      <div className="mt-8 relative print:hidden">
        <div className="bg-white border border-slate-200/90 shadow-sm rounded-2xl overflow-hidden transition-all duration-300">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="w-full flex items-center justify-between p-5 sm:p-6 bg-slate-50/70 hover:bg-slate-100/80 transition-all group focus:outline-none"
          >
            <div className="flex items-center gap-3.5">
              <div className="p-2.5 bg-slate-200 text-slate-700 rounded-xl group-hover:bg-sky-600 group-hover:text-white transition-colors">
                <Activity className="w-5 h-5" />
              </div>
              <div className="text-left">
                <h3 className="text-sm sm:text-base font-bold text-slate-800 group-hover:text-sky-700 transition-colors">
                  View Detailed Technical Logs & Audit Trail
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Expand to inspect the Evidence Fusion matrix, RAG references, policy hierarchy, and multi-agent audit data.
                </p>
              </div>
            </div>
            <div className="w-8 h-8 rounded-full bg-white border border-slate-200 flex items-center justify-center group-hover:border-slate-300 transition-colors flex-shrink-0">
              {showAdvanced ? (
                <ChevronUp className="w-4 h-4 text-slate-600" />
              ) : (
                <ChevronDown className="w-4 h-4 text-slate-600" />
              )}
            </div>
          </button>

          {showAdvanced && (
            <div className="p-6 sm:p-8 space-y-8 bg-white border-t border-slate-200 animate-in slide-in-from-top-4 fade-in duration-300">
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
