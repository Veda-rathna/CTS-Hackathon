import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FilePlus2,
  CheckCircle2,
  Clock,
  XCircle,
  AlertCircle,
  Files,
  ShieldCheck,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';
import StatCard from '../components/dashboard/StatCard';
import RecentRequestsTable from '../components/dashboard/RecentRequestsTable';
import { getStoredPARequests } from '../utils/storage';

export default function Dashboard() {
  const [requests, setRequests] = useState([]);

  useEffect(() => {
    const loaded = getStoredPARequests();
    setRequests(loaded);
  }, []);

  // Compute actual metrics from data
  const totalRequests = requests.length;
  const approvedCount = requests.filter((r) => {
    const d = (r.decision || '').toUpperCase();
    return d.includes('APPROV') || d === 'LIKELY_COVERED' || d === 'COVERED';
  }).length;

  const pendingCount = requests.filter((r) => {
    const d = (r.decision || '').toUpperCase();
    return d.includes('PEND') || d === 'REVIEW';
  }).length;

  const deniedCount = requests.filter((r) => {
    const d = (r.decision || '').toUpperCase();
    return d.includes('DENY') || d.includes('DENIED') || d === 'EXCLUDED';
  }).length;

  const additionalEvidenceCount = requests.filter((r) => {
    const d = (r.decision || '').toUpperCase();
    return (
      d.includes('ADDITIONAL') ||
      d.includes('MORE_INFO') ||
      d === 'REQUEST_MORE_INFORMATION'
    );
  }).length;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="healthcare-card p-6 bg-gradient-to-r from-sky-900 via-slate-900 to-teal-950 text-white flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-slate-800 shadow-md">
        <div className="space-y-1.5">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-sky-500/20 text-sky-300 border border-sky-400/30">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Deterministic Triage Engine Active</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
            Prior Authorization Intelligence
          </h2>
          <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
            Automated Medicare coverage policy companion combining CPT/HCPCS and ICD-10 normalization, CMS LCD/NCD policy verification, and explainable decision support.
          </p>
        </div>

        <Link
          to="/new-request"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs sm:text-sm rounded-xl transition-all shadow-sm hover:shadow-sky-500/20 whitespace-nowrap"
        >
          <FilePlus2 className="w-4 h-4 text-slate-950" />
          <span>Create PA Request</span>
        </Link>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title="Total PA Requests"
          value={totalRequests}
          icon={Files}
          color="blue"
          subtitle="Processed cases"
        />
        <StatCard
          title="Approved"
          value={approvedCount}
          icon={CheckCircle2}
          color="emerald"
          subtitle="Policy criteria satisfied"
        />
        <StatCard
          title="Pending Review"
          value={pendingCount}
          icon={Clock}
          color="amber"
          subtitle="Manual clinician review"
        />
        <StatCard
          title="Additional Evidence"
          value={additionalEvidenceCount}
          icon={AlertCircle}
          color="purple"
          subtitle="Code/document required"
        />
        <StatCard
          title="Denied"
          value={deniedCount}
          icon={XCircle}
          color="rose"
          subtitle="Policy exclusion"
        />
      </div>

      {/* Recent Requests Table */}
      <RecentRequestsTable requests={requests} />
    </div>
  );
}
