import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FilePlus2,
  CheckCircle2,
  XCircle,
  Clock,
  HelpCircle,
  Files,
  ShieldCheck,
  Zap,
  Activity,
  Server,
} from 'lucide-react';
import StatCard from '../components/dashboard/StatCard';
import RecentRequestsTable from '../components/dashboard/RecentRequestsTable';
import { getStoredPARequests } from '../utils/storage';
import { checkHealth } from '../services/api';

export default function Dashboard() {
  const [requests, setRequests] = useState([]);
  const [apiStatus, setApiStatus] = useState({ online: false, checking: true });

  useEffect(() => {
    const loaded = getStoredPARequests();
    setRequests(loaded);

    checkHealth().then((status) => {
      setApiStatus({ online: status.online, checking: false, data: status.data });
    });
  }, []);

  // Compute metrics from decision values (3 canonical outcomes: APPROVE, DENY, NEED_MORE_INFORMATION)
  const totalRequests = requests.length;

  const approvedCount = requests.filter((r) => {
    const d = (r.decision || '').toUpperCase();
    return d === 'APPROVE' || d === 'APPROVED' || d.includes('APPROV');
  }).length;

  const deniedCount = requests.filter((r) => {
    const d = (r.decision || '').toUpperCase();
    return d === 'DENY' || d === 'DENIED' || d.includes('DENI') || d === 'POLICY_EXPIRED';
  }).length;

  const needInfoCount = requests.filter((r) => {
    const d = (r.decision || '').toUpperCase();
    return (
      d === 'NEED_MORE_INFORMATION' ||
      d === 'REQUEST_MORE_INFORMATION' ||
      d === 'PEND' ||
      d === 'PENDED' ||
      d.includes('MORE_INFO') ||
      d.includes('ADDITIONAL') ||
      d.includes('PEND')
    );
  }).length;

  return (
    <div className="space-y-6">
      {/* Top Hero Banner */}
      <div className="healthcare-card p-6 bg-gradient-to-r from-sky-900 via-slate-900 to-teal-950 text-white flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-slate-800 shadow-md">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-sky-500/20 text-sky-300 border border-sky-400/30">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>CMS Policy Companion & Decision Engine</span>
            </div>

            {/* Backend API Health Status Indicator */}
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
              <span className="relative flex h-2 w-2">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${apiStatus.online ? 'bg-emerald-400' : 'bg-amber-400'} opacity-75`}></span>
                <span className={`relative inline-flex rounded-full h-2 w-2 ${apiStatus.online ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
              </span>
              <span>{apiStatus.checking ? 'Checking API...' : apiStatus.online ? 'Backend API Connected' : 'API Standby'}</span>
            </div>
          </div>

          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
            Prior Authorization Triage Intelligence
          </h2>
          <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
            Automated Medicare prior authorization triage app combining deterministic SQL code matching, CMS LCD/NCD coverage policies, and agentic semantic evaluation.
          </p>
        </div>

        <Link
          to="/new-request"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs sm:text-sm rounded-xl transition-all shadow-sm hover:shadow-sky-500/20 whitespace-nowrap"
        >
          <FilePlus2 className="w-4 h-4 text-slate-950" />
          <span>New PA Evaluation</span>
        </Link>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Submissions"
          value={totalRequests}
          icon={Files}
          color="blue"
          subtitle="Processed authorization requests"
        />
        <StatCard
          title="Approved"
          value={approvedCount}
          icon={CheckCircle2}
          color="emerald"
          subtitle="All mandatory criteria satisfied"
        />
        <StatCard
          title="Denied"
          value={deniedCount}
          icon={XCircle}
          color="rose"
          subtitle="Mandatory criteria not met or excluded"
        />
        <StatCard
          title="Need More Information"
          value={needInfoCount}
          icon={HelpCircle}
          color="sky"
          subtitle="Missing clinical documentation or unlisted codes"
        />
      </div>

      {/* Recent Requests Table */}
      <RecentRequestsTable requests={requests} />
    </div>
  );
}
