import React, { useState, useEffect } from 'react';
import {
  X,
  BookOpen,
  Calendar,
  MapPin,
  FileCheck,
  CheckCircle,
  XCircle,
  Hash,
  Layers,
  ExternalLink,
} from 'lucide-react';
import { formatDate } from '../../utils/formatters';
import { getLcd, getNcd, getArticle, getArticleCoveredIcd10, getArticleHcpcs } from '../../services/api';

export default function PolicyDetailDrawer({ policy, onClose }) {
  const [loading, setLoading] = useState(false);
  const [details, setDetails] = useState(null);
  const [coveredCodes, setCoveredCodes] = useState([]);
  const [hcpcsCodes, setHcpcsCodes] = useState([]);

  useEffect(() => {
    if (!policy) return;
    let isMounted = true;
    setLoading(true);

    async function loadDetails() {
      try {
        const type = (policy.policy_type || '').toUpperCase();
        let mainData = null;
        let icdList = [];
        let hcpcsList = [];

        if (type === 'LCD') {
          mainData = await getLcd(policy.policy_id);
          if (policy.article_id) {
            try {
              const icdRes = await getArticleCoveredIcd10(policy.article_id);
              icdList = icdRes.codes || [];
              const hcpcsRes = await getArticleHcpcs(policy.article_id);
              hcpcsList = hcpcsRes.codes || [];
            } catch (e) {
              console.log('Article details not fetched:', e);
            }
          }
        } else if (type === 'NCD') {
          mainData = await getNcd(policy.policy_id);
        } else if (type === 'ARTICLE') {
          mainData = await getArticle(policy.policy_id);
          try {
            const icdRes = await getArticleCoveredIcd10(policy.policy_id);
            icdList = icdRes.codes || [];
            const hcpcsRes = await getArticleHcpcs(policy.policy_id);
            hcpcsList = hcpcsRes.codes || [];
          } catch (e) {
            console.log('Article details not fetched:', e);
          }
        }

        if (isMounted) {
          setDetails(mainData || policy);
          setCoveredCodes(icdList);
          setHcpcsCodes(hcpcsList);
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          setDetails(policy);
          // Fallback mock details for offline/development
          if (policy.policy_id === 'L39054') {
            setCoveredCodes([
              { code: 'M54.16', description: 'Radiculopathy, lumbar region' },
              { code: 'M54.17', description: 'Radiculopathy, lumbosacral region' },
              { code: 'M51.16', description: 'Intervertebral disc disorders with radiculopathy' },
            ]);
            setHcpcsCodes([
              { code: '64483', description: 'Inj transforaminal epidural lumbar/sacral 1 level' },
              { code: '64484', description: 'Inj transforaminal epidural addl level' },
            ]);
          }
          setLoading(false);
        }
      }
    }

    loadDetails();
    return () => {
      isMounted = false;
    };
  }, [policy]);

  if (!policy) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/50 backdrop-blur-xs flex justify-end animate-in fade-in duration-200">
      <div className="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col border-l border-slate-200 animate-in slide-in-from-right duration-300">
        {/* Drawer Header */}
        <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2.5">
            <span className="px-2.5 py-1 rounded text-xs font-bold font-mono bg-sky-100 text-sky-800 border border-sky-200">
              {policy.policy_type} {policy.policy_id}
            </span>
            <h3 className="text-sm font-semibold text-slate-800">Policy Specification</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drawer Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-xs text-slate-700">
          {/* Title & Overview */}
          <div className="space-y-2">
            <h2 className="text-base font-bold text-slate-900 leading-snug">
              {details?.title || policy.title || 'CMS Medicare Coverage Policy Document'}
            </h2>
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 pt-1">
              <div className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>Effective: {formatDate(details?.effective_date || policy.effective_date)}</span>
              </div>
              {policy.jurisdiction_id && (
                <div className="flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-slate-400" />
                  <span>MAC Jurisdiction: {policy.jurisdiction_id}</span>
                </div>
              )}
              {policy.article_id && (
                <div className="flex items-center gap-1 font-mono text-sky-700">
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>Article: {policy.article_id}</span>
                </div>
              )}
            </div>
          </div>

          {/* Description narrative */}
          {details?.description && (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
              <span className="font-semibold text-slate-800 block">Coverage Summary:</span>
              <p className="text-slate-600 leading-relaxed">{details.description}</p>
            </div>
          )}

          {/* Covered HCPCS Codes */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Hash className="w-4 h-4 text-sky-600" />
              <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                Covered CPT / HCPCS Procedures
              </h4>
            </div>

            {hcpcsCodes.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {hcpcsCodes.map((item, i) => (
                  <div key={i} className="p-2.5 rounded-lg bg-sky-50/60 border border-sky-100">
                    <span className="font-mono font-bold text-sky-800">{item.code || item}</span>
                    {item.description && (
                      <p className="text-[11px] text-slate-600 mt-0.5">{item.description}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-400 italic">
                {details?.hcpcs_codes
                  ? details.hcpcs_codes.join(', ')
                  : 'Applicable standard procedure code set.'}
              </p>
            )}
          </div>

          {/* Covered ICD-10 Diagnosis Codes */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-emerald-600" />
              <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                Covered ICD-10-CM Diagnoses
              </h4>
            </div>

            {coveredCodes.length > 0 ? (
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {coveredCodes.map((item, i) => (
                  <div
                    key={i}
                    className="p-2.5 rounded-lg bg-emerald-50/40 border border-emerald-100 flex items-start justify-between gap-2"
                  >
                    <div>
                      <span className="font-mono font-bold text-emerald-800">{item.code || item}</span>
                      {item.description && (
                        <p className="text-[11px] text-slate-600 mt-0.5">{item.description}</p>
                      )}
                    </div>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                      Covered
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-400 italic">
                Refer to associated Billing & Coding article for full tabular crosswalk.
              </p>
            )}
          </div>

          {/* CMS Source Disclaimer */}
          <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl text-[11px] text-slate-500 leading-relaxed">
            <span className="font-semibold text-slate-700 block mb-0.5">CMS Policy Notice:</span>
            Policy determinations are sourced from official CMS Medicare Coverage Database rules. Always verify contractor specific local variances prior to claim finalization.
          </div>
        </div>

        {/* Drawer Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-300 rounded-xl transition-colors"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
}
