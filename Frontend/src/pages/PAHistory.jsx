import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { formatDate, getRequestPriority } from '../utils/formatters';
import { getStoredPARequests } from '../utils/storage';
import DecisionBadge from '../components/common/DecisionBadge';
import PriorityBadge from '../components/common/PriorityBadge';
import Pagination from '../components/common/Pagination';
import EmptyState from '../components/common/EmptyState';
import {
  Search,
  Filter,
  Eye,
  FilePlus2,
  ArrowUpDown,
  MapPin,
  History,
} from 'lucide-react';

export default function PAHistory() {
  const [requests, setRequests] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [decisionFilter, setDecisionFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [sortField, setSortField] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 8;

  useEffect(() => {
    const loaded = getStoredPARequests();
    setRequests(loaded);
  }, []);

  // Filter logic
  const filtered = requests.filter((item) => {
    const pa = item.pa_requests ? item.pa_requests[0] : item;
    const term = searchTerm.toLowerCase();

    const id = pa.pa_request_id || '';
    const proc = pa.procedure_code || pa.service?.procedure_code || '';
    const diag = (pa.diagnosis_codes || pa.diagnoses?.map((d) => d.icd10_code || d.source_code) || []).join(' ');
    const state = pa.state || pa.patient?.state || '';
    const notes = pa.clinical_notes || pa.service?.service_description || '';
    const priority = getRequestPriority(item);

    const matchesSearch =
      id.toLowerCase().includes(term) ||
      proc.toLowerCase().includes(term) ||
      diag.toLowerCase().includes(term) ||
      state.toLowerCase().includes(term) ||
      notes.toLowerCase().includes(term) ||
      priority.toLowerCase().includes(term);

    const decision = (pa.decision || '').toUpperCase();
    const matchesDecision =
      decisionFilter === 'ALL' ||
      (decisionFilter === 'APPROVE' && (decision === 'APPROVE' || decision.includes('APPROV'))) ||
      (decisionFilter === 'PEND' && (
        decision === 'PEND' ||
        decision === 'PENDED' ||
        decision === 'PENDING_REVIEW' ||
        decision === 'REVIEW' ||
        decision === 'POLICY_EXPIRED'
      )) ||
      (decisionFilter === 'NEED_MORE_INFORMATION' && (
        decision === 'NEED_MORE_INFORMATION' ||
        decision === 'REQUEST_MORE_INFORMATION' ||
        decision === 'ADDITIONAL_EVIDENCE_REQUIRED' ||
        decision.includes('MORE_INFO') ||
        decision.includes('ADDITIONAL')
      )) ||
      (decisionFilter === 'REJECTED' && (
        decision === 'REJECTED' ||
        decision === 'EXCLUDED' ||
        decision === 'POLICY_EXCLUSION' ||
        decision === 'NOT_COVERED' ||
        decision === 'DENIED' ||
        decision === 'DENY'
      ));

    const matchesPriority =
      priorityFilter === 'ALL' || priority === priorityFilter;

    return matchesSearch && matchesDecision && matchesPriority;
  });

  // Sort logic
  const sorted = [...filtered].sort((a, b) => {
    const paA = a.pa_requests ? a.pa_requests[0] : a;
    const paB = b.pa_requests ? b.pa_requests[0] : b;

    if (sortField === 'id') {
      return sortOrder === 'asc'
        ? (paA.pa_request_id || '').localeCompare(paB.pa_request_id || '')
        : (paB.pa_request_id || '').localeCompare(paA.pa_request_id || '');
    }

    if (sortField === 'priority') {
      const prioOrder = { URGENT: 3, MEDIUM: 2, LOW: 1 };
      const prioA = prioOrder[getRequestPriority(a)] || 0;
      const prioB = prioOrder[getRequestPriority(b)] || 0;
      return sortOrder === 'asc' ? prioA - prioB : prioB - prioA;
    }

    const dateA = new Date(paA.service_date || paA.request?.request_date || paA.created_at || 0).getTime();
    const dateB = new Date(paB.service_date || paB.request?.request_date || paB.created_at || 0).getTime();
    return sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
  });

  const paginated = sorted.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const toggleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  return (
    <div className="space-y-5">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200/90">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
              Prior Authorization History
            </h2>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
              Audit Log
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Operational search and audit history of all processed prior authorization triage records
          </p>
        </div>

        <Link
          to="/new-request"
          className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-sky-700 hover:bg-sky-800 rounded-lg shadow-sm transition-colors self-start sm:self-auto"
        >
          <FilePlus2 className="w-3.5 h-3.5" />
          <span>New Evaluation</span>
        </Link>
      </div>

      {/* Main Table Card */}
      <div className="healthcare-card overflow-hidden">
        {/* Filter Controls */}
        <div className="p-3.5 sm:p-4 border-b border-slate-200/90 bg-white grid grid-cols-1 sm:grid-cols-12 gap-2.5">
          {/* Search */}
          <div className="relative sm:col-span-6">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by PA ID, procedure code, ICD-10, state..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-600 bg-slate-50/50"
            />
          </div>

          {/* Priority Filter */}
          <div className="sm:col-span-3">
            <select
              value={priorityFilter}
              onChange={(e) => {
                setPriorityFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full px-2.5 py-1.5 text-xs rounded-lg border border-slate-200 bg-slate-50/50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-600 font-bold"
            >
              <option value="ALL">All Priorities</option>
              <option value="URGENT">Urgent Priority</option>
              <option value="MEDIUM">Medium Priority</option>
              <option value="LOW">Low Priority</option>
            </select>
          </div>

          {/* Decision Filter */}
          <div className="sm:col-span-3">
            <select
              value={decisionFilter}
              onChange={(e) => {
                setDecisionFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full px-2.5 py-1.5 text-xs rounded-lg border border-slate-200 bg-slate-50/50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-600 font-bold"
            >
              <option value="ALL">All Determinations</option>
              <option value="APPROVE">Approved (APPROVE)</option>
              <option value="PEND">Pended for Review (PEND)</option>
              <option value="NEED_MORE_INFORMATION">Need More Information</option>
              <option value="REJECTED">Rejected / Excluded</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr>
                <th
                  onClick={() => toggleSort('id')}
                  className="table-header cursor-pointer hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center gap-1">
                    <span>PA ID</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th
                  onClick={() => toggleSort('priority')}
                  className="table-header cursor-pointer hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center gap-1">
                    <span>Priority</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th className="table-header">Procedure Code</th>
                <th className="table-header">Diagnoses (ICD-10)</th>
                <th className="table-header">State</th>
                <th
                  onClick={() => toggleSort('date')}
                  className="table-header cursor-pointer hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center gap-1">
                    <span>Evaluation Date</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th className="table-header">Determination</th>
                <th className="table-header text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {paginated.length === 0 ? (
                <tr>
                  <td colSpan="8" className="p-6">
                    <EmptyState
                      title="No prior authorization records match criteria"
                      description="Try adjusting your search query, priority filter, or determination filter."
                    />
                  </td>
                </tr>
              ) : (
                paginated.map((item) => {
                  const pa = item.pa_requests ? item.pa_requests[0] : item;
                  const id = pa.pa_request_id || `PA-${Math.random().toString().slice(2, 6)}`;
                  const priority = getRequestPriority(item);
                  const procedureCode = pa.procedure_code || pa.service?.procedure_code || '64483';
                  const diagnosisCodes = pa.diagnosis_codes || pa.diagnoses?.map((d) => d.icd10_code || d.source_code) || ['M54.16'];
                  const state = pa.state || pa.patient?.state || 'TX';
                  const requestDate = pa.service_date || pa.request?.request_date || pa.created_at;
                  const decision = pa.decision || 'PENDING_REVIEW';

                  return (
                    <tr key={id} className="hover:bg-slate-50/75 transition-colors">
                      <td className="table-cell font-mono font-bold text-sky-800">
                        <Link to={`/pa/${id}`} className="hover:underline">
                          {id}
                        </Link>
                      </td>
                      <td className="table-cell">
                        <PriorityBadge priority={priority} size="xs" />
                      </td>
                      <td className="table-cell font-mono font-bold text-xs">
                        <span className="px-1.5 py-0.5 rounded bg-sky-50 text-sky-800 border border-sky-200">
                          {procedureCode}
                        </span>
                      </td>
                      <td className="table-cell">
                        <div className="flex flex-wrap gap-1">
                          {diagnosisCodes.map((d, i) => (
                            <span key={i} className="px-1.5 py-0.2 text-[11px] font-mono font-bold bg-slate-50 text-slate-700 border border-slate-200 rounded">
                              {d}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="table-cell text-xs font-semibold text-slate-700">
                        <span className="inline-flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-purple-500" />
                          {state}
                        </span>
                      </td>
                      <td className="table-cell text-xs text-slate-500 font-medium">
                        {formatDate(requestDate)}
                      </td>
                      <td className="table-cell">
                        <DecisionBadge decision={decision} size="sm" />
                      </td>
                      <td className="table-cell text-right">
                        <Link
                          to={`/pa/${id}`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold text-sky-700 bg-sky-50 hover:bg-sky-100 border border-sky-200 rounded-lg transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>View Details</span>
                        </Link>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <Pagination
          currentPage={currentPage}
          totalItems={filtered.length}
          pageSize={pageSize}
          onPageChange={setCurrentPage}
        />
      </div>
    </div>
  );
}
