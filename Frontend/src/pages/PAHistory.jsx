import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { formatDate } from '../utils/formatters';
import { getStoredPARequests } from '../utils/storage';
import DecisionBadge from '../components/common/DecisionBadge';
import Pagination from '../components/common/Pagination';
import {
  Search,
  Filter,
  Eye,
  FilePlus2,
  ArrowUpDown,
  Download,
  MapPin,
  FileText,
} from 'lucide-react';

export default function PAHistory() {
  const [requests, setRequests] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [decisionFilter, setDecisionFilter] = useState('ALL');
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
      (decisionFilter === 'DENY' && (decision === 'DENY' || decision.includes('DENI') || decision === 'POLICY_EXPIRED')) ||
      (decisionFilter === 'NEED_MORE_INFORMATION' && (
        decision === 'NEED_MORE_INFORMATION' ||
        decision === 'REQUEST_MORE_INFORMATION' ||
        decision === 'PEND' ||
        decision.includes('MORE_INFO') ||
        decision.includes('ADDITIONAL') ||
        decision.includes('PEND')
      ));

    return matchesSearch && matchesDecision;
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

  const handleExportCSV = () => {
    const headers = ['PA ID', 'Procedure', 'Diagnoses', 'State', 'Patient Age', 'Date', 'Status', 'Decision'];
    const rows = filtered.map((req) => {
      const pa = req.pa_requests ? req.pa_requests[0] : req;
      return [
        pa.pa_request_id || '',
        pa.procedure_code || pa.service?.procedure_code || '',
        `"${(pa.diagnosis_codes || pa.diagnoses?.map((d) => d.icd10_code || d.source_code) || []).join('; ')}"`,
        pa.state || pa.patient?.state || '',
        pa.patient_age || pa.patient?.age || '',
        pa.service_date || pa.created_at || '',
        pa.status || 'COMPLETED',
        pa.decision || 'PENDING_REVIEW',
      ];
    });

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `prior_auth_history_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-200/80">
        <div>
          <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
            Prior Authorization Clinical Audit History
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Audit trail of all submitted prior authorization triage requests and decision determinations
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleExportCSV}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded-xl shadow-2xs transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Export CSV</span>
          </button>
          <Link
            to="/new-request"
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-sky-600 hover:bg-sky-700 rounded-xl shadow-sm transition-all"
          >
            <FilePlus2 className="w-4 h-4" />
            <span>New Evaluation</span>
          </Link>
        </div>
      </div>

      {/* Main Table Card */}
      <div className="healthcare-card overflow-hidden">
        {/* Filter Controls */}
        <div className="p-4 sm:p-5 border-b border-slate-200/80 bg-white grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Search */}
          <div className="relative sm:col-span-2">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by PA ID, procedure code, ICD-10 diagnosis, state..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-10 pr-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 bg-slate-50/50"
            />
          </div>

          {/* Decision Filter */}
          <div>
            <select
              value={decisionFilter}
              onChange={(e) => {
                setDecisionFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 bg-slate-50/50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 font-bold"
            >
              <option value="ALL">All Decision Statuses</option>
              <option value="APPROVE">Approved (APPROVE)</option>
              <option value="DENY">Denied (DENY)</option>
              <option value="NEED_MORE_INFORMATION">Need More Information (NEED_MORE_INFO)</option>
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
                <th className="table-header">Status</th>
                <th className="table-header">Decision</th>
                <th className="table-header text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {paginated.length === 0 ? (
                <tr>
                  <td colSpan="8" className="py-12 text-center text-slate-400 text-xs italic">
                    No prior authorization history records match your search criteria.
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
                      <td className="table-cell font-mono font-bold text-xs">
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
                          <MapPin className="w-3.5 h-3.5 text-purple-500" />
                          {state}
                        </span>
                      </td>
                      <td className="table-cell text-xs text-slate-500 font-medium">
                        {formatDate(requestDate)}
                      </td>
                      <td className="table-cell">
                        <span className="px-2.5 py-0.5 text-[11px] font-bold rounded-md bg-slate-100 text-slate-600">
                          {status}
                        </span>
                      </td>
                      <td className="table-cell">
                        <DecisionBadge decision={decision} size="sm" />
                      </td>
                      <td className="table-cell text-right">
                        <Link
                          to={`/pa/${id}`}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-bold text-sky-700 bg-sky-50 hover:bg-sky-100 border border-sky-200 rounded-xl transition-colors"
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
