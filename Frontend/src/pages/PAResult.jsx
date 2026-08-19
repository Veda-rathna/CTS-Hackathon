import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getPARequestById } from '../utils/storage';
import {
  formatDate,
  getRequestPriority,
  categorizeNeedMoreInfo,
  deriveSuggestedNextStep,
  extractCriticValidation,
} from '../utils/formatters';
import DecisionBadge from '../components/common/DecisionBadge';
import PriorityBadge from '../components/common/PriorityBadge';
import EvidenceCard from '../components/evidence/EvidenceCard';
import PolicyPathDisplay from '../components/result/PolicyPathDisplay';
import RagEvidenceSection from '../components/result/RagEvidenceSection';
import EvidenceFusionPanel from '../components/result/EvidenceFusionPanel';
import AgentEvaluationPanel from '../components/result/AgentEvaluationPanel';
import ImpactMetricsSection from '../components/result/ImpactMetricsSection';
import PrintableClinicalReport from '../components/result/PrintableClinicalReport';
import { openPAReportPDF } from '../utils/pdfGenerator';
import {
  Activity,
  ArrowLeft,
  Printer,
  ExternalLink,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  Compass,
  AlertCircle,
  Check,
  X,
  Copy,
  CheckCircle2,
  Send,
  FileCheck2,
} from 'lucide-react';

export default function PAResult() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [record, setRecord] = useState(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [copiedPrompt, setCopiedPrompt] = useState(false);

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
      <div className="healthcare-card p-10 text-center space-y-3 bg-white">
        <AlertTriangle className="w-10 h-10 text-amber-500 mx-auto" />
        <h3 className="text-sm font-bold text-slate-800">Prior Authorization Record Not Found</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          No prior authorization evaluation record found for ID: <span className="font-mono font-bold text-slate-700">{id}</span>.
        </p>
        <div className="pt-2">
          <Link
            to="/history"
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-sky-800 bg-sky-50 hover:bg-sky-100 rounded-lg border border-sky-200 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to History</span>
          </Link>
        </div>
      </div>
    );
  }

  const handlePrint = () => {
    window.print();
  };

  const handleCopyPrompt = () => {
    if (needInfoDiag?.promptTemplate) {
      navigator.clipboard.writeText(needInfoDiag.promptTemplate);
      setCopiedPrompt(true);
      setTimeout(() => setCopiedPrompt(false), 2500);
    }
  };

  const priority = getRequestPriority(record);
  const needInfoDiag = categorizeNeedMoreInfo(record);
  const suggestedNextStep = deriveSuggestedNextStep(record);
  const criticValidation = extractCriticValidation(record);

  // 1. Normalized Final Decision (Mapped for presentation)
  const rawDecision = (record.decision || 'NEED_MORE_INFORMATION').toUpperCase();
  const reasonCodes = record.reason_codes || [];
  const hasExclusion =
    reasonCodes.includes('NCD_EXCLUDES_PROCEDURE') ||
    reasonCodes.includes('LCD_EXCLUDES_PROCEDURE') ||
    reasonCodes.includes('ARTICLE_EXCLUDES_PROCEDURE') ||
    reasonCodes.includes('MANDATORY_CRITERIA_NOT_SATISFIED') ||
    record.evidence_fusion_result === 'EXCLUDED';

  let normalizedDecision = 'NEED_MORE_INFORMATION';
  let decisionDisplayTitle = 'NEED MORE INFORMATION';

  if (rawDecision.includes('APPROV') || rawDecision === 'APPROVE') {
    normalizedDecision = 'APPROVE';
    decisionDisplayTitle = 'APPROVE';
  } else if (
    rawDecision === 'REJECTED' ||
    rawDecision === 'REJECT' ||
    rawDecision === 'EXCLUDED' ||
    rawDecision === 'POLICY_EXCLUSION' ||
    rawDecision === 'NOT_COVERED' ||
    rawDecision === 'DENIED' ||
    rawDecision === 'DENY' ||
    hasExclusion
  ) {
    normalizedDecision = 'REJECTED';
    decisionDisplayTitle = 'REJECTED';
  } else if (
    rawDecision === 'PEND' ||
    rawDecision === 'PENDED' ||
    rawDecision === 'PENDING_REVIEW' ||
    rawDecision === 'REVIEW' ||
    rawDecision === 'POLICY_EXPIRED'
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
    if (proc === 'J1561') return 'NCD 158 — Intravenous Immune Globulin for Autoimmune Blistering Diseases';
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
          cleanText = `Procedure ${procCode} is covered under applicable policy.`;
        } else if (isNotSatisfied) {
          cleanText = `Requested procedure conflicts with policy coverage exclusions.`;
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
        requirements.push({ symbol: '✓', type: 'satisfied', text: `Procedure ${procCode} is covered under applicable policy.` });
        requirements.push({ symbol: '✓', type: 'satisfied', text: `Diagnosis ${diagCodes} is an eligible indication.` });
        requirements.push({ symbol: '✓', type: 'satisfied', text: 'All required clinical documentation criteria are satisfied.' });
      } else if (normalizedDecision === 'REJECTED') {
        requirements.push({ symbol: '✓', type: 'satisfied', text: 'Requested procedure was evaluated against applicable policy.' });
        requirements.push({ symbol: '✗', type: 'failed', text: 'Requested service or indication is excluded from Medicare coverage.' });
      } else if (normalizedDecision === 'PEND') {
        requirements.push({ symbol: '✓', type: 'satisfied', text: 'Requested procedure was evaluated against policy criteria.' });
        requirements.push({ symbol: '⚠', type: 'incomplete', text: 'Clinical documentation requires nurse utilization review.' });
      } else {
        requirements.push({ symbol: '✓', type: 'satisfied', text: `Procedure ${procCode} was evaluated against policy requirements.` });
        requirements.push({ symbol: '⚠', type: 'incomplete', text: 'Required clinical documentation is incomplete.' });
      }
    }

    return requirements;
  };

  const nurseRequirements = getNurseRequirements();

  // 4. Clinical Evidence Breakdown (Supporting, Contradicting, Missing)
  const getSupportingEvidence = () => {
    const list = [];
    const seen = new Set();

    const isBoilerplate = (txt) => {
      if (!txt || txt.length < 5) return true;
      const upper = txt.toUpperCase();
      return (
        upper.includes('PRIOR AUTHORIZATION CLINICAL') ||
        upper.includes('CLINICAL INTAKE PACKET') ||
        upper.includes('ORDERING PROVIDER INFORMATION') ||
        upper.includes('REQUESTED SERVICE & CLINICAL CODING') ||
        upper.includes('DOCUMENT: CLINICAL REVIEW') ||
        upper.includes('PHYSICIAN SIGNATURE') ||
        upper.includes('ELECTRONICALLY SIGNED') ||
        upper.includes('PATIENT NAME:') ||
        upper.includes('PATIENT STATE:') ||
        upper.includes('NPI:') ||
        upper.includes('======') ||
        upper.includes('------')
      );
    };

    const add = (item) => {
      if (!item || isBoilerplate(item)) return;
      let clean = item
        .trim()
        .replace(/^(?:[-*•]\s*|Submitted HCPCS:\s*|Submitted ICD-10:\s*|Patient Ev\.\s*:\s*|Evidence\s*:\s*)/i, '')
        .replace(/^[=\-_#*]{3,}\s*/, '')
        .trim();
      if (clean.length > 5 && !isBoilerplate(clean) && !seen.has(clean.toLowerCase())) {
        seen.add(clean.toLowerCase());
        if (!clean.endsWith('.')) clean += '.';
        list.push(clean);
      }
    };

    (record.criteria || record.policy_requirements || []).forEach(c => {
      (c.patient_evidence || []).forEach(pe => add(pe));
      (c.evidence || []).forEach(ev => add(ev.text || ev.explanation));
    });

    const notes = record.clinical_notes || record.service?.service_description || '';
    if (notes) {
      notes.split(/(?<=[.!?])\s+/).forEach(s => {
        const trimmed = s.trim();
        if (trimmed.length > 12 && !isBoilerplate(trimmed) && !trimmed.toLowerCase().includes('refuses') && !trimmed.toLowerCase().includes('has not attempted')) {
          add(trimmed);
        }
      });
    }

    if (list.length === 0) {
      if (record.procedure_code || record.service?.procedure_code) {
        add(`Requested procedure: ${record.procedure_code || record.service?.procedure_code}`);
      }
      if (record.diagnosis_codes || record.diagnoses) {
        const dx = (record.diagnosis_codes || record.diagnoses?.map(d => d.icd10_code || d.source_code) || []).join(', ');
        if (dx) add(`Submitted diagnosis: ${dx}`);
      }
    }

    return list.slice(0, 6);
  };

  const getContradictingEvidence = () => {
    const list = [];
    const seen = new Set();

    (record.criteria || record.policy_requirements || []).forEach(c => {
      (c.contradicting_evidence || []).forEach(ce => {
        if (ce && !seen.has(ce.toLowerCase())) {
          seen.add(ce.toLowerCase());
          list.push(ce.trim());
        }
      });
    });

    const notes = (record.clinical_notes || record.service?.service_description || '').toLowerCase();
    if (notes.includes('refuses conservative') || notes.includes('has not attempted')) {
      list.push('Clinical notes indicate conservative therapy trial was not attempted or refused.');
    }

    return list;
  };

  const getMissingEvidence = () => {
    const list = [];
    const seen = new Set();

    const add = (item) => {
      if (!item) return;
      let clean = item.trim().replace(/^(?:[-*•]\s*|Missing:\s*)/i, '').trim();
      if (clean.length > 5 && !seen.has(clean.toLowerCase())) {
        seen.add(clean.toLowerCase());
        if (!clean.endsWith('.')) clean += '.';
        list.push(clean);
      }
    };

    if (record.missing_information && Array.isArray(record.missing_information)) {
      record.missing_information.forEach(m => {
        if (typeof m === 'string') m.split(';').forEach(sub => add(sub));
      });
    }

    (record.criteria || record.policy_requirements || []).forEach(c => {
      if (c.status === 'UNKNOWN' && c.mandatory) {
        add(c.requirement || c.criterion || 'Clinical documentation for required criterion');
      }
    });

    return list;
  };

  const supportingEvidenceList = getSupportingEvidence();
  const contradictingEvidenceList = getContradictingEvidence();
  const missingEvidenceList = getMissingEvidence();

  // 5. Evaluation Narrative from existing backend response
  const getNurseEvaluation = () => {
    let raw = record.decision_basis || record.reason || record.explanation || '';
    if (normalizedDecision === 'REJECTED') {
      if (raw && (raw.includes('pended for nurse/UM review') || raw.includes('human adjudication'))) {
        raw = raw.replace('The case has been pended for nurse/UM review.', 'Coverage is rejected under governing policy.')
                 .replace('The case requires nurse/UM review to determine the appropriate disposition.', 'Coverage cannot be authorized.');
      }
      if (raw) return raw;
      return "The requested service or diagnosis conflicts with an applicable Medicare policy exclusion or non-covered indication. Coverage cannot be authorized under the governing policy.";
    }
    if (raw) return raw;

    if (normalizedDecision === 'APPROVE') {
      return "The submitted documentation supports the applicable coverage requirements. The requested service is supported by the documented diagnosis, clinical symptoms, and documented trial of prerequisite conservative therapy.";
    }
    if (normalizedDecision === 'PEND') {
      return "The requested service was evaluated against the governing policy. The case requires nurse/UM clinical review to determine the appropriate authorization disposition.";
    }
    return "The request appears potentially eligible for coverage, but the submitted documentation does not establish all required clinical criteria.";
  };

  const nurseEvaluation = getNurseEvaluation();

  // Parse synthesized narrative into structured points
  const parseEvaluationNarrative = (rawText) => {
    if (!rawText) return { intro: '', items: [] };

    let cleanedText = rawText;
    if (normalizedDecision === 'REJECTED' && cleanedText.includes('pended for nurse/UM review')) {
      cleanedText = cleanedText.replace('The case has been pended for nurse/UM review.', 'Coverage is rejected under governing policy.');
    }

    const parts = cleanedText
      .split(/(?:•|\n-|\n\*|\n•|\r?\n)/)
      .map((s) => s.trim())
      .filter(Boolean);

    if (parts.length <= 1 && !cleanedText.includes('•')) {
      return { intro: cleanedText, items: [] };
    }

    let intro = '';
    const items = [];

    parts.forEach((part, index) => {
      // Check if the first part is an introductory summary sentence
      const isFirstAndIntro =
        index === 0 &&
        !part.match(/:\s*(?:SATISFIED|NOT_SATISFIED|UNKNOWN|MATCHED|NOT_MATCHED|MET|UNMET|COVERED|EXCLUDED|PENDING)/i) &&
        !part.includes('—') &&
        !part.includes('--');

      if (isFirstAndIntro) {
        intro = part;
        return;
      }

      // Try parsing: "<ID>: <STATUS> — <Description>" or "<STATUS> — <Description>"
      const match = part.match(
        /^(?:([^:]+):\s*)?(SATISFIED|NOT_SATISFIED|UNKNOWN|MATCHED|NOT_MATCHED|MET|UNMET|COVERED|EXCLUDED|PENDING|APPROVED|DENIED|PENDED)\s*(?:[—–-]+\s*(.*))?$/i
      );

      if (match && (match[1] || match[3])) {
        items.push({
          id: match[1]?.trim() || null,
          status: match[2]?.trim().toUpperCase(),
          text: match[3]?.trim() || '',
        });
      } else {
        // General bullet point
        items.push({
          id: null,
          status: null,
          text: part.replace(/^[•\-*]\s*/, '').trim(),
        });
      }
    });

    return { intro, items };
  };

  const parsedNarrative = parseEvaluationNarrative(nurseEvaluation);

  return (
    <div className="space-y-5 max-w-4xl mx-auto pb-10">
      {/* Navigation & Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2.5 border-b border-slate-200/90">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => navigate('/history')}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            title="Back to History"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono font-bold text-sky-800 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                {record.pa_request_id}
              </span>
              <PriorityBadge priority={priority} size="xs" />
              <span className="text-xs text-slate-500 font-medium">
                Evaluated {formatDate(record.created_at || record.service_date)}
              </span>
            </div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight mt-0.5">
              Prior Authorization Clinical Summary
            </h2>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => openPAReportPDF(record)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-white bg-sky-700 hover:bg-sky-800 rounded-lg shadow-sm transition-colors"
            title="Open generated CMS-0057-F PDF Prior Authorization Report in a new browser tab"
          >
            <ExternalLink className="w-3.5 h-3.5 text-white" />
            <span>Open PDF Report</span>
          </button>

          <button
            type="button"
            onClick={handlePrint}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded-lg shadow-2xs transition-colors"
            title="Open standard browser print dialog"
          >
            <Printer className="w-3.5 h-3.5 text-slate-500" />
            <span>Print</span>
          </button>
        </div>
      </div>

      {/* PRIMARY CLINICAL DECISION CARD */}
      <div className="healthcare-card p-5 sm:p-6 space-y-6 bg-white print:border-slate-300">
        
        {/* Header Label & Priority Indicator */}
        <div className="pb-2.5 border-b border-slate-100 flex items-center justify-between">
          <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">
            Prior Authorization Decision Summary
          </span>
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] text-slate-400 font-bold uppercase tracking-wider">Priority:</span>
            <PriorityBadge priority={priority} size="xs" />
          </div>
        </div>

        {/* 1. FINAL DETERMINATION */}
        <div className="space-y-1">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Final Determination
          </span>
          <div>
            <span className={`inline-block px-3.5 py-1.5 rounded-lg text-sm font-extrabold tracking-wide border ${
              normalizedDecision === 'APPROVE'
                ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                : normalizedDecision === 'REJECTED'
                ? 'bg-rose-50 text-rose-800 border-rose-300'
                : normalizedDecision === 'PEND'
                ? 'bg-purple-50 text-purple-800 border-purple-300'
                : 'bg-amber-50 text-amber-900 border-amber-300'
            }`}>
              {decisionDisplayTitle}
            </span>
          </div>
        </div>

        {/* 2. APPLICABLE POLICY */}
        <div className="space-y-1">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Applicable Policy
          </span>
          <p className="text-sm font-bold text-slate-900 leading-snug">
            {applicablePolicy}
          </p>
        </div>

        {/* 3. POLICY REQUIREMENTS */}
        <div className="space-y-2">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Policy Requirements Checklist
          </span>
          <div className="space-y-1.5">
            {nurseRequirements.map((req, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2 text-xs leading-relaxed"
              >
                <span className={`font-bold text-xs flex-shrink-0 select-none ${
                  req.type === 'satisfied'
                    ? 'text-emerald-700'
                    : req.type === 'failed'
                    ? 'text-rose-700'
                    : 'text-amber-700'
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

        {/* 4. CLINICAL EVIDENCE (Separated Supporting, Contradicting, Missing) */}
        <div className="space-y-2.5">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Clinical Evidence Summary
          </span>

          {/* Supporting Evidence */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-1">
            <span className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider block">
              Supporting Evidence ({supportingEvidenceList.length})
            </span>
            <ul className="space-y-1 text-xs text-slate-800">
              {supportingEvidenceList.map((ev, idx) => (
                <li key={idx} className="flex items-start gap-1.5 leading-relaxed">
                  <Check className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>{ev}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Contradicting Evidence (prominently surfaced if present) */}
          {contradictingEvidenceList.length > 0 && (
            <div className="p-3 rounded-lg bg-rose-50/70 border border-rose-200 space-y-1">
              <span className="text-[11px] font-bold text-rose-800 uppercase tracking-wider block">
                Contradicting Evidence ({contradictingEvidenceList.length})
              </span>
              <ul className="space-y-1 text-xs text-rose-900">
                {contradictingEvidenceList.map((ev, idx) => (
                  <li key={idx} className="flex items-start gap-1.5 leading-relaxed">
                    <X className="w-3.5 h-3.5 text-rose-600 flex-shrink-0 mt-0.5" />
                    <span>{ev}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Missing Evidence (prominently surfaced if present) */}
          {missingEvidenceList.length > 0 && (
            <div className="p-3 rounded-lg bg-amber-50/70 border border-amber-200 space-y-1">
              <span className="text-[11px] font-bold text-amber-800 uppercase tracking-wider block">
                Missing Evidence Items ({missingEvidenceList.length})
              </span>
              <ul className="space-y-1 text-xs text-amber-950 font-medium">
                {missingEvidenceList.map((ev, idx) => (
                  <li key={idx} className="flex items-start gap-1.5 leading-relaxed">
                    <span className="text-amber-700 font-bold select-none">•</span>
                    <span>{ev}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* 5. NEED MORE INFORMATION / EVIDENCE ISSUE DIAGNOSTIC PANEL */}
        {needInfoDiag.category !== 'NO_ADDITIONAL_INFORMATION_REQUIRED' && normalizedDecision !== 'APPROVE' && (
          <div className={`p-4 rounded-xl border space-y-3 ${
            needInfoDiag.subCategory === 'CONFLICTING_CLINICAL_EVIDENCE'
              ? 'bg-rose-50/60 border-rose-200'
              : needInfoDiag.subCategory === 'MISSING_CLINICAL_INFORMATION'
              ? 'bg-sky-50/60 border-sky-200'
              : 'bg-amber-50/60 border-amber-200'
          }`}>
            {/* Header with Sub-Category Classification */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-200/80">
              <div className="flex items-center gap-2">
                <AlertCircle className={`w-4 h-4 ${
                  needInfoDiag.subCategory === 'CONFLICTING_CLINICAL_EVIDENCE'
                    ? 'text-rose-700'
                    : needInfoDiag.subCategory === 'MISSING_CLINICAL_INFORMATION'
                    ? 'text-sky-700'
                    : 'text-amber-700'
                }`} />
                <div>
                  <h4 className={`text-xs font-extrabold uppercase tracking-wider ${
                    needInfoDiag.subCategory === 'CONFLICTING_CLINICAL_EVIDENCE'
                      ? 'text-rose-950'
                      : needInfoDiag.subCategory === 'MISSING_CLINICAL_INFORMATION'
                      ? 'text-sky-950'
                      : 'text-amber-950'
                  }`}>
                    Issue Diagnostic & Sub-Category Classification
                  </h4>
                  <span className="text-[11px] font-semibold text-slate-600 block">
                    {needInfoDiag.title}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-1.5 self-start sm:self-auto">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Sub-Category:</span>
                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold tracking-wide border ${
                  needInfoDiag.subCategory === 'CONFLICTING_CLINICAL_EVIDENCE'
                    ? 'bg-rose-100 text-rose-800 border-rose-300'
                    : needInfoDiag.subCategory === 'MISSING_CLINICAL_INFORMATION'
                    ? 'bg-sky-100 text-sky-800 border-sky-300'
                    : 'bg-amber-100 text-amber-900 border-amber-300'
                }`}>
                  {needInfoDiag.badgeLabel || needInfoDiag.category}
                </span>
              </div>
            </div>

            {/* Diagnostic Details */}
            <div className="space-y-2 text-xs">
              <div>
                <span className="font-bold text-slate-900 block">Root Cause / Clinical Finding:</span>
                <p className="text-slate-800 leading-relaxed mt-0.5">{needInfoDiag.description}</p>
              </div>

              {needInfoDiag.items.length > 0 && (
                <div className="p-3 rounded-lg bg-white/90 border border-slate-200/80">
                  <span className="font-bold text-slate-900 text-xs block mb-1">
                    {needInfoDiag.subCategory === 'CONFLICTING_CLINICAL_EVIDENCE'
                      ? 'Reconciliation Items / Documented Discrepancies:'
                      : 'Specific Missing Documentation Required:'}
                  </span>
                  <ul className="space-y-1 text-slate-800 text-xs list-disc list-inside">
                    {needInfoDiag.items.map((item, i) => (
                      <li key={i} className="leading-relaxed">{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {needInfoDiag.providerAction && (
                <div className="p-2.5 rounded-lg bg-white/90 border border-slate-200/80 text-xs">
                  <span className="font-bold text-slate-900 block">Utilization Management Action:</span>
                  <p className="text-slate-700 mt-0.5 leading-relaxed">{needInfoDiag.providerAction}</p>
                </div>
              )}

              {/* Standardized Provider Prompt Template & 1-Click Copy */}
              {needInfoDiag.promptTemplate && (
                <div className="mt-2 p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-sky-800">
                      <Send className="w-3.5 h-3.5 text-sky-700" />
                      <span className="text-[11px] font-bold uppercase tracking-wider">
                        Standardized Provider Request Prompt
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={handleCopyPrompt}
                      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-bold transition-all ${
                        copiedPrompt
                          ? 'bg-emerald-600 text-white'
                          : 'bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 shadow-2xs'
                      }`}
                      title="Copy provider prompt to clipboard"
                    >
                      {copiedPrompt ? (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5 text-white" />
                          <span>Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5 text-slate-500" />
                          <span>Copy Provider Prompt</span>
                        </>
                      )}
                    </button>
                  </div>

                  <pre className="text-[11px] font-mono text-slate-800 bg-white p-3 rounded-lg overflow-x-auto whitespace-pre-wrap leading-relaxed border border-slate-200 shadow-2xs">
                    {needInfoDiag.promptTemplate}
                  </pre>
                  <p className="text-[10.5px] text-slate-500 italic">
                    Nurses and UM coordinators can copy this standardized communication directly to request missing documentation from the clinic.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 6. SUGGESTED NEXT STEP (Workflow Guidance, NOT Medical Advice) */}
        <div className="p-4 rounded-xl bg-sky-50/70 border border-sky-200 text-sky-950 space-y-1.5 shadow-2xs">
          <div className="flex items-center gap-1.5">
            <Compass className="w-4 h-4 text-sky-700" />
            <h4 className="text-xs font-bold text-sky-900 uppercase tracking-wider">
              Suggested Next Step (Workflow Guidance)
            </h4>
          </div>
          <p className="text-xs font-semibold text-slate-800 leading-relaxed">
            {suggestedNextStep}
          </p>
          <span className="text-[10px] text-slate-500 block pt-1 border-t border-sky-200/80">
            Administrative workflow guidance for utilization management personnel; not a clinical medical recommendation.
          </span>
        </div>

        {/* 7. EVALUATION NARRATIVE */}
        <div className="space-y-2 pt-2 border-t border-slate-100">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Synthesized Clinical Evaluation Narrative
          </span>

          {parsedNarrative.intro && (
            <p className="text-xs font-semibold text-slate-800 leading-relaxed bg-slate-50/80 p-2.5 rounded-lg border border-slate-200/70">
              {parsedNarrative.intro}
            </p>
          )}

          {parsedNarrative.items.length > 0 ? (
            <div className="space-y-1.5 pt-0.5">
              {parsedNarrative.items.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2.5 p-2 rounded-lg bg-slate-50/50 hover:bg-slate-50 border border-slate-200/60 text-xs transition-colors"
                >
                  {item.status ? (
                    <span
                      className={`px-1.5 py-0.5 text-[10px] font-bold rounded flex-shrink-0 mt-0.5 border ${
                        item.status === 'SATISFIED' || item.status === 'MATCHED' || item.status === 'MET' || item.status === 'COVERED' || item.status === 'APPROVED'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : item.status === 'NOT_SATISFIED' || item.status === 'EXCLUDED' || item.status === 'DENIED' || item.status === 'UNMET'
                          ? 'bg-rose-50 text-rose-700 border-rose-200'
                          : 'bg-amber-50 text-amber-700 border-amber-200'
                      }`}
                    >
                      {item.status === 'SATISFIED' || item.status === 'MET' || item.status === 'COVERED'
                        ? '✓ ' + item.status
                        : item.status === 'NOT_SATISFIED' || item.status === 'EXCLUDED'
                        ? '✗ ' + item.status
                        : '⚠ ' + item.status}
                    </span>
                  ) : (
                    <span className="text-sky-600 font-bold select-none mt-0.5">•</span>
                  )}

                  <div className="flex-1 space-y-0.5 min-w-0">
                    {item.id && (
                      <span className="inline-block text-[10px] font-mono font-semibold text-slate-600 bg-white px-1.5 py-0.2 rounded border border-slate-200 mr-1.5">
                        {item.id}
                      </span>
                    )}
                    <span className="text-slate-700 leading-relaxed font-medium">
                      {item.text || item.id}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            !parsedNarrative.intro && (
              <p className="text-xs font-medium text-slate-700 leading-relaxed">
                {nurseEvaluation}
              </p>
            )
          )}
        </div>

      </div>

      {/* OPERATIONAL IMPACT METRICS SECTION */}
      <div className="print:hidden">
        <ImpactMetricsSection compact={false} record={record} />
      </div>

      {/* SECONDARY VIEW: Detailed Technical Evaluation Trace (Collapsible) */}
      <div className="relative print:hidden">
        <div className="healthcare-card overflow-hidden bg-white">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="w-full flex items-center justify-between p-4 bg-slate-50/70 hover:bg-slate-100 transition-colors group focus:outline-none"
          >
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 bg-slate-200 text-slate-700 rounded-md group-hover:bg-sky-700 group-hover:text-white transition-colors">
                <Activity className="w-4 h-4" />
              </div>
              <div className="text-left">
                <h4 className="text-xs font-bold text-slate-800 group-hover:text-sky-800 transition-colors">
                  Technical Evaluation Trace & Audit Logs
                </h4>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Inspect the Evidence Fusion matrix, RAG references, policy hierarchy, and multi-agent audit data.
                </p>
              </div>
            </div>
            <div className="w-6 h-6 rounded-full bg-white border border-slate-200 flex items-center justify-center flex-shrink-0">
              {showAdvanced ? (
                <ChevronUp className="w-3.5 h-3.5 text-slate-600" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5 text-slate-600" />
              )}
            </div>
          </button>

          {showAdvanced && (
            <div className="p-5 sm:p-6 space-y-6 bg-white border-t border-slate-200">
              {/* AI Validation / Critic Multi-Agent Audit */}
              <div className="p-3.5 rounded-lg bg-purple-50/50 border border-purple-200 space-y-2.5">
                <div className="flex items-center justify-between pb-1.5 border-b border-purple-200/80">
                  <div className="flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-purple-700" />
                    <h4 className="text-xs font-bold text-purple-950 uppercase tracking-wider">
                      AI Validation & Grounding Audit
                    </h4>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                    criticValidation.verdict === 'VALIDATED' || criticValidation.verdict === 'DETERMINISTIC_EVALUATION'
                      ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                      : 'bg-amber-100 text-amber-800 border-amber-300'
                  }`}>
                    Critic: {criticValidation.verdictLabel || criticValidation.verdict}
                  </span>
                </div>

                <p className="text-xs text-purple-900 font-medium">
                  {criticValidation.summary}
                </p>

                {/* Individual Grounded Checks */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-0.5">
                  {criticValidation.checks.map((chk, i) => (
                    <div key={i} className="p-2 rounded-lg bg-white border border-purple-100 text-xs space-y-0.5">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-800">{chk.name}</span>
                        <span className={`px-1.5 py-0.2 text-[10px] font-bold rounded ${
                          chk.status === 'PASSED'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : chk.status === 'WARNING'
                            ? 'bg-amber-50 text-amber-700 border border-amber-200'
                            : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}>
                          {chk.status}
                        </span>
                      </div>
                      {chk.detail && (
                        <p className="text-[10px] text-slate-500 line-clamp-2">{chk.detail}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>

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
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    Deterministic Code & Jurisdiction Evidence ({record.evidence.length})
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
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

      {/* PRINT-ONLY COMPREHENSIVE MEDICAL DETERMINATION REPORT */}
      <PrintableClinicalReport
        record={record}
        nurseRequirements={nurseRequirements}
        supportingEvidence={supportingEvidenceList}
        contradictingEvidence={contradictingEvidenceList}
        missingEvidence={missingEvidenceList}
      />

    </div>
  );
}
