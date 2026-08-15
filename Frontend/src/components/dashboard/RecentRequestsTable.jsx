import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { formatDate, truncateText } from '../../utils/formatters';
import DecisionBadge from '../common/DecisionBadge';
import Pagination from '../common/Pagination';
import { Search, Filter, ArrowUpRight, Eye, FileText } from 'lucide-react';

export default function RecentRequestsTable({ requests = [] }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [decisionFilter, setDecisionFilter] = useState('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 5;

  // Filter requests
  const filtered = requests.filter((req) => {
    const term = searchTerm.toLowerCase();
    const pa = req.pa_requests ? req.pa_requests[0] : req;
    const matchesSearch =
      (pa.pa_request_id || '').toLowerCase().includes(term) ||
      (pa.patient?.patient_id || '').toLowerCase().includes(term) ||
      (pa.provider?.organization_name || '').toLowerCase().includes(term) ||
      (pa.service?.service_description || '').toLowerCase().includes(term) ||
      (pa.service?.procedure_code || '').toLowerCase().includes(term);

    const matchesDecision =
      decisionFilter === 'ALL' ||
      (pa.decision || '').toUpperCase().includes(decisionFilter) ||
      (decisionFilter === 'PENDING' && (pa.decision || '').includes('PEND')) ||
      (decisionFilter === 'ADDITIONAL' && (pa.decision || '').includes('ADDITIONAL'));

    return matchesSearch && matchesDecision;
  });

  const paginated = filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  return (
    <div className="healthcare-card overflow-hidden">
      {/* Table Top Controls */}
      <div className="p-4 sm:p-5 border-b border-slate-200 bg-white flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-sky-600" />
          <h2 className="text-base font-semibold text-slate-800">Recent Prior Authorization Requests</h2>
          <span className="ml-2 px-2 py-0.5 text-xs font-semibold bg-slate-100 text-slate-600 rounded-full">
            {filtered.length}
          </span>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-2.5">
          {/* Search */}
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search ID, patient, code..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 transition-all bg-slate-50/50"
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
              className="w-full sm:w-auto px-2.5 py-1.5 text-xs rounded-lg border border-slate-200 bg-slate-50/50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 font-medium"
            >
              <option value="ALL">All Decisions</option>
              <option value="APPROV">Approved</option>
              <option value="PENDING">Pending Review</option>
              <option value="ADDITIONAL">Additional Evidence</option>
              <option value="DENY">Denied</option>
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
              <th className="table-header">Patient ID</th>
              <th className="table-header">Service & Code</th>
              <th className="table-header">Provider / Org</th>
              <th className="table-header">Request Date</th>
              <th className="table-header">Status</th>
              <th className="table-header">Decision</th>
              <th className="table-header text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {paginated.length === 0 ? (
              <tr>
                <td colSpan="8" className="py-8 text-center text-slate-400 text-sm">
                  No matching prior authorization requests found.
                </td>
              </tr>
            ) : (
              paginated.map((item) => {
                const pa = item.pa_requests ? item.pa_requests[0] : item;
                const id = pa.pa_request_id;
                const patientId = pa.patient?.patient_id || 'N/A';
                const serviceDesc = pa.service?.service_description || 'Standard Medical Service';
                const procedureCode = pa.service?.procedure_code;
                const providerOrg = pa.provider?.organization_name || pa.provider?.provider_id || 'N/A';
                const requestDate = pa.request?.request_date || pa.created_at;
                const status = pa.status || 'COMPLETED';
                const decision = pa.decision || 'PENDING_REVIEW';

                return (
                  <tr key={id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="table-cell font-mono font-semibold text-sky-700">
                      <Link to={`/pa/${id}`} className="hover:underline flex items-center gap-1">
                        {id}
                      </Link>
                    </td>
                    <td className="table-cell font-medium text-slate-800">{patientId}</td>
                    <td className="table-cell max-w-xs">
                      <div className="truncate font-medium text-slate-800" title={serviceDesc}>
                        {truncateText(serviceDesc, 36)}
                      </div>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        {procedureCode ? (
                          <span className="px-1.5 py-0.2 text-[10px] font-mono bg-sky-50 text-sky-700 border border-sky-200 rounded">
                            CPT {procedureCode}
                          </span>
                        ) : (
                          <span className="px-1.5 py-0.2 text-[10px] font-mono bg-amber-50 text-amber-700 border border-amber-200 rounded">
                            Code Required
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="table-cell text-xs text-slate-600 max-w-[160px] truncate" title={providerOrg}>
                      {providerOrg}
                    </td>
                    <td className="table-cell text-xs text-slate-600">{formatDate(requestDate)}</td>
                    <td className="table-cell">
                      <span className="px-2 py-0.5 text-xs font-semibold rounded bg-slate-100 text-slate-600">
                        {status}
                      </span>
                    </td>
                    <td className="table-cell">
                      <DecisionBadge decision={decision} size="sm" />
                    </td>
                    <td className="table-cell text-right">
                      <Link
                        to={`/pa/${id}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-sky-700 bg-sky-50 hover:bg-sky-100 border border-sky-200 rounded-lg transition-colors"
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
