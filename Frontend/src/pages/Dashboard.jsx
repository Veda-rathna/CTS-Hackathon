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
  TrendingUp,
  FileCheck,
  Timer,
  FileSearch,
  Info,
  Layers,
  ArrowRight,
  RefreshCw,
  Activity,
} from 'lucide-react';
import StatCard from '../components/dashboard/StatCard';
import RecentRequestsTable from '../components/dashboard/RecentRequestsTable';
import PriorityBadge from '../components/common/PriorityBadge';
import { getStoredPARequests } from '../utils/storage';
import { getRequestPriority } from '../utils/formatters';
import { sortPriorityQueue, PROCESSING_STATUS } from '../utils/queueEngine';

const BATCH_QUEUE_STORAGE_KEY = 'pa_batch_work_queue_state_v1';

export default function Dashboard() {
  const [requests, setRequests] = useState([]);
  const [queueState, setQueueState] = useState({ batchId: null, items: [] });

  useEffect(() => {
    const loaded = getStoredPARequests();
    setRequests(loaded);

    try {
      const savedQueue = sessionStorage.getItem(BATCH_QUEUE_STORAGE_KEY);
      if (savedQueue) {
        const parsed = JSON.parse(savedQueue);
        if (Array.isArray(parsed.items) && parsed.items.length > 0) {
          setQueueState(parsed);
        }
      }
    } catch (e) {
      console.warn('Could not read queue state on dashboard:', e);
    }
  }, []);

  // Compute metrics from actual request data
  const totalRequests = requests.length;

  const approvedCount = requests.filter((r) => {
    const d = (r.decision || '').toUpperCase();
    return d === 'APPROVE' || d === 'APPROVED' || d.includes('APPROV');
  }).length;

  const rejectedCount = requests.filter((r) => {
    const d = (r.decision || '').toUpperCase();
    return (
      d === 'REJECTED' ||
      d === 'EXCLUDED' ||
      d === 'POLICY_EXCLUSION' ||
      d === 'NOT_COVERED' ||
      d === 'DENIED' ||
      d === 'DENY'
    );
  }).length;

  const pendedCount = requests.filter((r) => {
    const d = (r.decision || '').toUpperCase();
    return (
      d === 'PEND' ||
      d === 'PENDED' ||
      d === 'PENDING_REVIEW' ||
      d === 'REVIEW' ||
      d === 'POLICY_EXPIRED'
    );
  }).length;

  const needInfoCount = requests.filter((r) => {
    const d = (r.decision || '').toUpperCase();
    return (
      d === 'NEED_MORE_INFORMATION' ||
      d === 'REQUEST_MORE_INFORMATION' ||
      d === 'ADDITIONAL_EVIDENCE_REQUIRED' ||
      d.includes('MORE_INFO') ||
      d.includes('ADDITIONAL')
    );
  }).length;

  const urgentCount = requests.filter((r) => getRequestPriority(r) === 'URGENT').length;
  const mediumCount = requests.filter((r) => getRequestPriority(r) === 'MEDIUM').length;
  const lowCount = requests.filter((r) => getRequestPriority(r) === 'LOW').length;

  const approvedPct = totalRequests > 0 ? Math.round((approvedCount / totalRequests) * 100) : 0;
  const pendedPct = totalRequests > 0 ? Math.round((pendedCount / totalRequests) * 100) : 0;
  const needInfoPct = totalRequests > 0 ? Math.round((needInfoCount / totalRequests) * 100) : 0;
  const rejectedPct = totalRequests > 0 ? Math.round((rejectedCount / totalRequests) * 100) : 0;

  // Active queue overview
  const activeQueueItems = queueState.items || [];
  const currentlyProcessing = activeQueueItems.find((i) => i.processing_status === PROCESSING_STATUS.PROCESSING);
  const queuedItems = sortPriorityQueue(activeQueueItems.filter((i) => i.processing_status === PROCESSING_STATUS.QUEUED));
  const nextUrgent = queuedItems.find((i) => (i.priority || '').toUpperCase() === 'URGENT');
  const nextItem = queuedItems[0];

  return (
    <div className="space-y-5">
      {/* Executive Command Center Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200/90">
        <div>
          <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
            Prior Authorization Command Center
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Clinical policy evaluation and utilization management overview
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto">
          <Link
            to="/queue"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 font-bold text-xs rounded-lg shadow-sm transition-colors"
          >
            <Layers className="w-3.5 h-3.5 text-sky-700" />
            <span>Work Queue</span>
          </Link>

          <Link
            to="/new-request"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-sky-700 hover:bg-sky-800 text-white font-bold text-xs rounded-lg shadow-sm transition-colors"
          >
            <FilePlus2 className="w-3.5 h-3.5" />
            <span>New PA Evaluation</span>
          </Link>
        </div>
      </div>

      {/* Primary 5 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <StatCard
          title="Total Requests"
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
          subtitle="Criteria satisfied"
        />
        <StatCard
          title="Pended for Review"
          value={pendedCount}
          icon={Clock}
          color="purple"
          subtitle="Clinical boundary"
        />
        <StatCard
          title="Need More Information"
          value={needInfoCount}
          icon={HelpCircle}
          color="amber"
          subtitle="Missing / incomplete"
        />
        <StatCard
          title="Rejected"
          value={rejectedCount}
          icon={XCircle}
          color="rose"
          subtitle="Policy exclusion"
        />
      </div>

      {/* ACTIVE PA WORK QUEUE EXECUTIVE SECTION */}
      <div className="healthcare-card p-4 sm:p-5 bg-white border-slate-200/90 shadow-sm space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-sky-50 text-sky-700">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                ACTIVE PA WORK QUEUE
              </h3>
              <p className="text-[11px] text-slate-500">
                Deterministic priority orchestration overview
              </p>
            </div>
          </div>

          <Link
            to="/queue"
            className="inline-flex items-center gap-1 text-xs font-bold text-sky-700 hover:text-sky-800 transition-colors self-start sm:self-auto"
          >
            <span>Open Batch Work Queue</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Work Queue Summary Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          {/* Slot 1: Currently Processing */}
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
              Currently Processing
            </span>
            {currentlyProcessing ? (
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-sky-900">{currentlyProcessing.pa_request_id}</span>
                  <PriorityBadge priority={currentlyProcessing.priority} size="xs" />
                </div>
                <div className="flex items-center gap-1.5 text-[11px] text-sky-800 font-medium">
                  <RefreshCw className="w-3 h-3 animate-spin text-sky-600" />
                  <span>Evaluating with PA Engine...</span>
                </div>
              </div>
            ) : (
              <span className="text-slate-400 italic block py-1">No active request in engine</span>
            )}
          </div>

          {/* Slot 2: Next Urgent Request */}
          <div className="p-3 rounded-xl bg-rose-50/50 border border-rose-200/80 space-y-1">
            <span className="text-[10px] font-bold text-rose-800 uppercase tracking-wider block">
              Next Urgent Request
            </span>
            {nextUrgent ? (
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-rose-950">{nextUrgent.pa_request_id}</span>
                  <PriorityBadge priority="URGENT" size="xs" />
                </div>
                <span className="text-[11px] text-rose-700 block font-mono">
                  {nextUrgent.procedure_code} • {nextUrgent.state || 'TX'}
                </span>
              </div>
            ) : (
              <span className="text-slate-400 italic block py-1">No urgent requests waiting</span>
            )}
          </div>

          {/* Slot 3: Queued & Next in Sequence */}
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Waiting In Queue
              </span>
              <span className="font-mono font-bold text-xs text-slate-700">
                {queuedItems.length} Waiting
              </span>
            </div>
            {nextItem ? (
              <div className="flex items-center justify-between pt-1">
                <div className="leading-tight">
                  <span className="text-[10px] text-slate-500 block">Next in Line:</span>
                  <span className="font-mono font-bold text-slate-800 text-xs">{nextItem.pa_request_id}</span>
                </div>
                <PriorityBadge priority={nextItem.priority} size="xs" />
              </div>
            ) : (
              <span className="text-slate-400 italic block py-1">Queue is clear</span>
            )}
          </div>
        </div>
      </div>

      {/* Priority Summary & Outcome Distribution Strip */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5">
        {/* Priority Section (5 columns) */}
        <div className="lg:col-span-5 healthcare-card p-4 sm:p-5 flex flex-col justify-between space-y-3">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Priority Distribution
              </span>
              <span className="text-[11px] font-semibold text-slate-500">
                {totalRequests} Processed Cases
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2.5 pt-2.5">
              {/* Urgent Card */}
              <div className="p-2.5 rounded-lg bg-rose-50/60 border border-rose-200/80 text-center space-y-0.5">
                <div className="flex items-center justify-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                  <span className="text-[11px] font-bold text-rose-800 uppercase">Urgent</span>
                </div>
                <div className="text-xl font-extrabold text-rose-950">{urgentCount}</div>
                <span className="text-[10px] text-rose-700 font-medium">Expedited (24h)</span>
              </div>

              {/* Medium Card */}
              <div className="p-2.5 rounded-lg bg-amber-50/60 border border-amber-200/80 text-center space-y-0.5">
                <div className="flex items-center justify-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                  <span className="text-[11px] font-bold text-amber-800 uppercase">Medium</span>
                </div>
                <div className="text-xl font-extrabold text-amber-950">{mediumCount}</div>
                <span className="text-[10px] text-amber-700 font-medium">Standard (72h)</span>
              </div>

              {/* Low Card */}
              <div className="p-2.5 rounded-lg bg-sky-50/60 border border-sky-200/80 text-center space-y-0.5">
                <div className="flex items-center justify-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-sky-500" />
                  <span className="text-[11px] font-bold text-sky-800 uppercase">Low</span>
                </div>
                <div className="text-xl font-extrabold text-sky-950">{lowCount}</div>
                <span className="text-[10px] text-sky-700 font-medium">Routine</span>
              </div>
            </div>
          </div>

          <p className="text-[11px] text-slate-500 leading-normal">
            Priority routing ensures expedited clinical evaluation without altering deterministic coverage rules.
          </p>
        </div>

        {/* Status Distribution Meter (7 columns) */}
        <div className="lg:col-span-7 healthcare-card p-4 sm:p-5 space-y-3.5">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Status Distribution
            </span>
            <span className="text-[11px] text-slate-500 font-medium">
              Based on {totalRequests} Processed Cases
            </span>
          </div>

          {/* Multi-segment Progress Bar */}
          <div className="space-y-2">
            <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden flex">
              <div
                style={{ width: `${approvedPct}%` }}
                className="bg-emerald-500 h-full transition-all duration-300"
                title={`Approved: ${approvedPct}%`}
              />
              <div
                style={{ width: `${pendedPct}%` }}
                className="bg-purple-500 h-full transition-all duration-300"
                title={`Pended: ${pendedPct}%`}
              />
              <div
                style={{ width: `${needInfoPct}%` }}
                className="bg-amber-500 h-full transition-all duration-300"
                title={`Need More Info: ${needInfoPct}%`}
              />
              <div
                style={{ width: `${rejectedPct}%` }}
                className="bg-rose-500 h-full transition-all duration-300"
                title={`Rejected: ${rejectedPct}%`}
              />
            </div>

            {/* Legend with percentages */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-xs">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 flex-shrink-0" />
                <span className="text-slate-600 font-medium">Approved:</span>
                <span className="font-bold text-slate-900">{approvedPct}%</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-purple-500 flex-shrink-0" />
                <span className="text-slate-600 font-medium">Pended:</span>
                <span className="font-bold text-slate-900">{pendedPct}%</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-500 flex-shrink-0" />
                <span className="text-slate-600 font-medium">Need Info:</span>
                <span className="font-bold text-slate-900">{needInfoPct}%</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-rose-500 flex-shrink-0" />
                <span className="text-slate-600 font-medium">Rejected:</span>
                <span className="font-bold text-slate-900">{rejectedPct}%</span>
              </div>
            </div>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-center justify-between">
            <span className="font-medium">Negative case visibility:</span>
            <span className="font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200 text-[11px]">
              {rejectedCount} Excluded Case{rejectedCount === 1 ? '' : 's'}
            </span>
          </div>
        </div>
      </div>

      {/* AUTOMATION IMPACT BENCHMARKS SECTION */}
      <div className="healthcare-card p-4 sm:p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 pb-2.5 border-b border-slate-200/90">
          <div>
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-sky-700" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                AUTOMATION IMPACT BENCHMARKS
              </h3>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Benchmark targets based on mentor review; not controlled production measurements.
            </p>
          </div>

          <span className="text-[11px] font-semibold text-slate-600 bg-slate-100 px-2.5 py-1 rounded-md border border-slate-200 self-start sm:self-auto">
            Operational Benchmarks
          </span>
        </div>

        {/* 4 Impact Benchmark Comparison Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Metric 1: Policy Lookup */}
          <div className="p-3 rounded-lg bg-slate-50/70 border border-slate-200 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-600 font-bold">
              <span>Policy Lookup</span>
              <FileSearch className="w-3.5 h-3.5 text-sky-700" />
            </div>
            <div className="space-y-1">
              <div className="flex items-baseline justify-between text-xs text-slate-500">
                <span>Manual:</span>
                <span className="font-medium line-through">~30 min</span>
              </div>
              <div className="flex items-baseline justify-between text-emerald-800">
                <span className="text-xs font-bold">Automated Target:</span>
                <span className="text-sm font-extrabold">&lt;30 sec</span>
              </div>
            </div>
            <div className="pt-1.5 border-t border-slate-200 text-[10px] font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded text-center">
              ~60x Retrieval Speedup
            </div>
          </div>

          {/* Metric 2: Full Review Cycle */}
          <div className="p-3 rounded-lg bg-slate-50/70 border border-slate-200 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-600 font-bold">
              <span>Review Cycle</span>
              <Timer className="w-3.5 h-3.5 text-sky-700" />
            </div>
            <div className="space-y-1">
              <div className="flex items-baseline justify-between text-xs text-slate-500">
                <span>Manual:</span>
                <span className="font-medium line-through">1–2 days</span>
              </div>
              <div className="flex items-baseline justify-between text-sky-800">
                <span className="text-xs font-bold">Automated Target:</span>
                <span className="text-sm font-extrabold">&lt;45 min</span>
              </div>
            </div>
            <div className="pt-1.5 border-t border-slate-200 text-[10px] font-bold text-sky-800 bg-sky-50 px-2 py-0.5 rounded text-center">
              Same-Day Turnaround
            </div>
          </div>

          {/* Metric 3: Missing Documentation Rate */}
          <div className="p-3 rounded-lg bg-slate-50/70 border border-slate-200 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-600 font-bold">
              <span>Missing Documentation</span>
              <FileCheck className="w-3.5 h-3.5 text-amber-700" />
            </div>
            <div className="space-y-1">
              <div className="flex items-baseline justify-between text-xs text-slate-500">
                <span>Manual:</span>
                <span className="font-medium line-through">~30%</span>
              </div>
              <div className="flex items-baseline justify-between text-amber-800">
                <span className="text-xs font-bold">Automated Target:</span>
                <span className="text-sm font-extrabold">~5%</span>
              </div>
            </div>
            <div className="pt-1.5 border-t border-slate-200 text-[10px] font-bold text-amber-800 bg-amber-50 px-2 py-0.5 rounded text-center">
              Upfront Intake Check
            </div>
          </div>

          {/* Metric 4: Reviewer Productivity */}
          <div className="p-3 rounded-lg bg-slate-50/70 border border-slate-200 space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-600 font-bold">
              <span>Reviewer Productivity</span>
              <TrendingUp className="w-3.5 h-3.5 text-purple-700" />
            </div>
            <div className="space-y-1">
              <div className="flex items-baseline justify-between text-xs text-slate-500">
                <span>Manual:</span>
                <span className="font-medium">Baseline</span>
              </div>
              <div className="flex items-baseline justify-between text-purple-800">
                <span className="text-xs font-bold">Target Improvement:</span>
                <span className="text-sm font-extrabold">+40%</span>
              </div>
            </div>
            <div className="pt-1.5 border-t border-slate-200 text-[10px] font-bold text-purple-800 bg-purple-50 px-2 py-0.5 rounded text-center">
              Increased UM Caseload
            </div>
          </div>
        </div>

        {/* Disclaimer Footer */}
        <div className="flex items-start gap-2 p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-[11px] text-slate-500">
          <Info className="w-3.5 h-3.5 text-slate-400 flex-shrink-0 mt-0.5" />
          <p>
            <strong>Benchmark Disclaimer:</strong> Impact values are benchmark targets based on mentor review and are not controlled production measurements.
          </p>
        </div>
      </div>

      {/* Clinical Audit Worklist Table */}
      <RecentRequestsTable requests={requests} />
    </div>
  );
}
