import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { formatDate, getRequestPriority } from '../../utils/formatters';
import DecisionBadge from '../common/DecisionBadge';
import PriorityBadge from '../common/PriorityBadge';
import Pagination from '../common/Pagination';
import EmptyState from '../common/EmptyState';
import { Search, Filter, Eye, FileText, MapPin } from 'lucide-react';

export default function RecentRequestsTable({ requests = [] }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [decisionFilter, setDecisionFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 6;

  // Filter requests based on search term, decision status, and priority
  const filtered = requests.filter((req) => {
    const term = searchTerm.toLowerCase();
    const pa = req.pa_requests ? req.pa_requests[0] : req;
    
    const proc = pa.procedure_code || pa.service?.procedure_code || '';
    const diag = (pa.diagnosis_codes || pa.diagnoses?.map((d) => d.icd10_code || d.source_code) || []).join(' ');
    const state = pa.state || pa.patient?.state || '';
    const notes = pa.clinical_notes || pa.service?.service_description || '';
    const id = pa.pa_request_id || '';
    const priority = getRequestPriority(req);

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
      (decisionFilter === 'PEND' && (decision === 'PEND' || decision === 'PENDED' || decision === 'PENDING_REVIEW')) ||
      (decisionFilter === 'NEED_MORE_INFORMATION' && (decision === 'NEED_MORE_INFORMATION' || decision === 'REQUEST_MORE_INFORMATION' || decision.includes('MORE_INFO') || decision.includes('ADDITIONAL'))) ||
      (decisionFilter === 'REJECTED' && (decision === 'REJECTED' || decision === 'EXCLUDED' || decision === 'POLICY_EXCLUSION' || decision === 'NOT_COVERED' || decision === 'DENIED' || decision === 'DENY'));

    const matchesPriority =
      priorityFilter === 'ALL' || priority === priorityFilter;

    return matchesSearch && matchesDecision && matchesPriority;
  });

  const paginated = filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  return (
    <div className="healthcare-card overflow-hidden">
      {/* Table Top Controls */}
      <div className="p-3.5 sm:p-4 border-b border-slate-200/90 bg-white flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="p-1 rounded-md bg-sky-50 text-sky-700 border border-sky-100">
            <FileText className="w-3.5 h-3.5" />
          </div>
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Prior Authorization Clinical Worklist
          </h3>
          <span className="px-2 py-0.5 text-[11px] font-bold bg-slate-100 text-slate-600 rounded-full border border-slate-200">
            {filtered.length}
          </span>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
          {/* Search */}
          <div className="relative w-full sm:w-56">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search ID, CPT, ICD-10..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-8 pr-2.5 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 transition-all bg-slate-50/50"
            />
          </div>

          {/* Priority Filter */}
          <div className="flex items-center gap-1">
            <select
              value={priorityFilter}
              onChange={(e) => {
                setPriorityFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full sm:w-auto px-2.5 py-1.5 text-xs rounded-lg border border-slate-200 bg-slate-50/50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 font-semibold"
            >
              <option value="ALL">All Priorities</option>
              <option value="URGENT">Urgent (24h)</option>
              <option value="MEDIUM">Medium (72h)</option>
              <option value="LOW">Low (Standard)</option>
            </select>
          </div>

          {/* Decision Filter */}
          <div className="flex items-center gap-1">
            <select
              value={decisionFilter}
              onChange={(e) => {
                setDecisionFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full sm:w-auto px-2.5 py-1.5 text-xs rounded-lg border border-slate-200 bg-slate-50/50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 font-semibold"
            >
              <option value="ALL">All Determinations</option>
              <option value="APPROVE">Approved (APPROVE)</option>
              <option value="PEND">Pended for Review (PEND)</option>
              <option value="NEED_MORE_INFORMATION">Need More Information</option>
              <option value="REJECTED">Rejected / Excluded</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr>
              <th className="table-header">PA Request ID</th>
              <th className="table-header">Priority</th>
              <th className="table-header">Procedure Code</th>
              <th className="table-header">Diagnosis (ICD-10)</th>
              <th className="table-header">State</th>
              <th className="table-header">Date</th>
              <th className="table-header">Determination</th>
              <th className="table-header text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {paginated.length === 0 ? (
              <tr>
                <td colSpan="8" className="p-4">
                  <EmptyState
                    title="No matching prior authorization requests"
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
                    <td className="table-cell font-mono font-bold text-xs text-slate-900">
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
                        <MapPin className="w-3 h-3 text-purple-500" />
                        {state}
                      </span>
                    </td>
                    <td className="table-cell text-xs text-slate-500 font-medium">{formatDate(requestDate)}</td>
                    <td className="table-cell">
                      <DecisionBadge decision={decision} size="sm" />
                    </td>
                    <td className="table-cell text-right">
                      <Link
                        to={`/pa/${id}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold text-sky-700 bg-sky-50 hover:bg-sky-100 border border-sky-200 rounded-lg transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Review</span>
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
  );
}
