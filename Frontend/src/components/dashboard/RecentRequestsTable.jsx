import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { formatDate, truncateText } from '../../utils/formatters';
import DecisionBadge from '../common/DecisionBadge';
import Pagination from '../common/Pagination';
import { Search, Filter, Eye, FileText, MapPin } from 'lucide-react';

export default function RecentRequestsTable({ requests = [] }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [decisionFilter, setDecisionFilter] = useState('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 6;

  // Filter requests
  const filtered = requests.filter((req) => {
    const term = searchTerm.toLowerCase();
    const pa = req.pa_requests ? req.pa_requests[0] : req;
    
    const proc = pa.procedure_code || pa.service?.procedure_code || '';
    const diag = (pa.diagnosis_codes || pa.diagnoses?.map((d) => d.icd10_code || d.source_code) || []).join(' ');
    const state = pa.state || pa.patient?.state || '';
    const notes = pa.clinical_notes || pa.service?.service_description || '';
    const id = pa.pa_request_id || '';

    const matchesSearch =
      id.toLowerCase().includes(term) ||
      proc.toLowerCase().includes(term) ||
      diag.toLowerCase().includes(term) ||
      state.toLowerCase().includes(term) ||
      notes.toLowerCase().includes(term);

    const decision = (pa.decision || '').toUpperCase();
    const matchesDecision =
      decisionFilter === 'ALL' ||
      (decisionFilter === 'APPROVE' && (decision === 'APPROVE' || decision.includes('APPROV'))) ||
      (decisionFilter === 'PEND' && (decision === 'PEND' || decision.includes('PEND'))) ||
      (decisionFilter === 'REQUEST_MORE_INFORMATION' && (decision === 'REQUEST_MORE_INFORMATION' || decision.includes('MORE_INFO') || decision.includes('ADDITIONAL')));

    return matchesSearch && matchesDecision;
  });

  const paginated = filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  return (
    <div className="healthcare-card overflow-hidden">
      {/* Table Top Controls */}
      <div className="p-4 sm:p-5 border-b border-slate-200 bg-white flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-sky-600" />
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
            Prior Authorization Clinical Audit Records
          </h2>
          <span className="ml-1 px-2.5 py-0.5 text-xs font-bold bg-slate-100 text-slate-700 rounded-full">
            {filtered.length}
          </span>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-2.5">
          {/* Search */}
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by PA ID, procedure, ICD-10..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 transition-all bg-slate-50/50"
            />
          </div>

          {/* Decision Filter */}
          <div className="flex items-center gap-1.5 w-full sm:w-auto">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={decisionFilter}
              onChange={(e) => {
                setDecisionFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full sm:w-auto px-3 py-1.5 text-xs rounded-xl border border-slate-200 bg-slate-50/50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 font-medium"
            >
              <option value="ALL">All Decisions</option>
              <option value="APPROVE">Approved (APPROVE)</option>
              <option value="PEND">Pended (PEND)</option>
              <option value="REQUEST_MORE_INFORMATION">Additional Info (RMI)</option>
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
              <th className="table-header">Procedure Code</th>
              <th className="table-header">Diagnosis (ICD-10)</th>
              <th className="table-header">State</th>
              <th className="table-header">Date</th>
              <th className="table-header">Status</th>
              <th className="table-header">Decision</th>
              <th className="table-header text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {paginated.length === 0 ? (
              <tr>
                <td colSpan="8" className="py-10 text-center text-slate-400 text-xs italic">
                  No matching prior authorization records found.
                </td>
              </tr>
            ) : (
              paginated.map((item) => {
                const pa = item.pa_requests ? item.pa_requests[0] : item;
                const id = pa.pa_request_id || `PA-${Math.random().toString().slice(2, 6)}`;
                const procedureCode = pa.procedure_code || pa.service?.procedure_code || '64483';
                const diagnosisCodes = pa.diagnosis_codes || pa.diagnoses?.map((d) => d.icd10_code || d.source_code) || ['M54.16'];
                const state = pa.state || pa.patient?.state || 'TX';
                const requestDate = pa.service_date || pa.request?.request_date || pa.created_at;
                const status = pa.status || 'COMPLETED';
                const decision = pa.decision || 'PENDING_REVIEW';

                return (
                  <tr key={id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="table-cell font-mono font-bold text-sky-700">
                      <Link to={`/pa/${id}`} className="hover:underline">
                        {id}
                      </Link>
                    </td>
                    <td className="table-cell font-mono font-bold text-xs text-slate-900">
                      <span className="px-2 py-0.5 rounded bg-sky-50 text-sky-800 border border-sky-200">
                        {procedureCode}
                      </span>
                    </td>
                    <td className="table-cell">
                      <div className="flex flex-wrap gap-1">
                        {diagnosisCodes.map((d, i) => (
                          <span key={i} className="px-1.5 py-0.2 text-[11px] font-mono font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 rounded">
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
                    <td className="table-cell text-xs text-slate-500">{formatDate(requestDate)}</td>
                    <td className="table-cell">
                      <span className="px-2 py-0.5 text-[11px] font-semibold rounded-md bg-slate-100 text-slate-600">
                        {status}
                      </span>
                    </td>
                    <td className="table-cell">
                      <DecisionBadge decision={decision} size="sm" />
                    </td>
                    <td className="table-cell text-right">
                      <Link
                        to={`/pa/${id}`}
                        className="inline-flex items-center gap-1 px-3 py-1 text-xs font-bold text-sky-700 bg-sky-50 hover:bg-sky-100 border border-sky-200 rounded-xl transition-colors"
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
