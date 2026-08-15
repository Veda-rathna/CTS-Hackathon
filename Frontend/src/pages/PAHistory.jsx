import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { formatDate, truncateText } from '../utils/formatters';
import { getStoredPARequests } from '../utils/storage';
import DecisionBadge from '../components/common/DecisionBadge';
import Pagination from '../components/common/Pagination';
import {
  History,
  Search,
  Filter,
  Eye,
  Calendar,
  FilePlus2,
  ArrowUpDown,
  Download,
} from 'lucide-react';

export default function PAHistory() {
  const [requests, setRequests] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [decisionFilter, setDecisionFilter] = useState('ALL');
  const [payerFilter, setPayerFilter] = useState('ALL');
  const [sortField, setSortField] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 8;

  useEffect(() => {
    const loaded = getStoredPARequests();
    setRequests(loaded);
  }, []);

  // Filter
  const filtered = requests.filter((item) => {
    const pa = item.pa_requests ? item.pa_requests[0] : item;
    const term = searchTerm.toLowerCase();
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

    const matchesPayer =
      payerFilter === 'ALL' ||
      (pa.patient?.payer || '').toLowerCase().includes(payerFilter.toLowerCase());

    return matchesSearch && matchesDecision && matchesPayer;
  });

  // Sort
  const sorted = [...filtered].sort((a, b) => {
    const paA = a.pa_requests ? a.pa_requests[0] : a;
    const paB = b.pa_requests ? b.pa_requests[0] : b;

    if (sortField === 'id') {
      return sortOrder === 'asc'
        ? (paA.pa_request_id || '').localeCompare(paB.pa_request_id || '')
        : (paB.pa_request_id || '').localeCompare(paA.pa_request_id || '');
    }
    if (sortField === 'patient') {
      return sortOrder === 'asc'
        ? (paA.patient?.patient_id || '').localeCompare(paB.patient?.patient_id || '')
        : (paB.patient?.patient_id || '').localeCompare(paA.patient?.patient_id || '');
    }

    // Default by date
    const dateA = new Date(paA.request?.request_date || paA.created_at || 0).getTime();
    const dateB = new Date(paB.request?.request_date || paB.created_at || 0).getTime();
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
    const headers = ['PA ID', 'Patient ID', 'Request Date', 'Provider', 'Service', 'Procedure', 'Status', 'Decision'];
    const rows = filtered.map((req) => {
      const pa = req.pa_requests ? req.pa_requests[0] : req;
      return [
        pa.pa_request_id,
        pa.patient?.patient_id || '',
        pa.request?.request_date || '',
        pa.provider?.organization_name || '',
        `"${(pa.service?.service_description || '').replace(/"/g, '""')}"`,
        pa.service?.procedure_code || '',
        pa.status || '',
        pa.decision || '',
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
      {/* Top Title & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Prior Authorization History
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Audit and inspect all prior authorization submissions and policy evaluation decisions
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleExportCSV}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl shadow-2xs transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Export CSV</span>
          </button>
          <Link
            to="/new-request"
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-sky-600 hover:bg-sky-700 rounded-xl shadow-sm transition-all"
          >
            <FilePlus2 className="w-4 h-4" />
            <span>New Request</span>
          </Link>
        </div>
      </div>

      {/* Main Table Card */}
      <div className="healthcare-card overflow-hidden">
        {/* Filter Controls */}
        <div className="p-4 sm:p-5 border-b border-slate-200 bg-white grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          {/* Search */}
          <div className="relative md:col-span-2">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by PA ID, patient ID, procedure, provider..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 bg-slate-50/50"
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
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 bg-slate-50/50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 font-medium"
            >
              <option value="ALL">All Decisions</option>
              <option value="APPROV">Approved</option>
              <option value="PENDING">Pending Review</option>
              <option value="ADDITIONAL">Additional Evidence</option>
              <option value="DENY">Denied</option>
            </select>
          </div>

          {/* Payer Filter */}
          <div>
            <select
              value={payerFilter}
              onChange={(e) => {
                setPayerFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 bg-slate-50/50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 font-medium"
            >
              <option value="ALL">All Payers</option>
              <option value="Medicare">Medicare</option>
              <option value="Advantage">Medicare Advantage</option>
              <option value="Medicaid">Medicaid</option>
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
                  onClick={() => toggleSort('patient')}
                  className="table-header cursor-pointer hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center gap-1">
                    <span>Patient</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th
                  onClick={() => toggleSort('date')}
                  className="table-header cursor-pointer hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center gap-1">
                    <span>Request Date</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th className="table-header">Provider</th>
                <th className="table-header">Service & Procedure</th>
                <th className="table-header">Status</th>
                <th className="table-header">Decision</th>
                <th className="table-header text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {paginated.length === 0 ? (
                <tr>
                  <td colSpan="8" className="py-12 text-center text-slate-400 text-sm">
                    No prior authorization history records match your search criteria.
                  </td>
                </tr>
              ) : (
                paginated.map((item) => {
                  const pa = item.pa_requests ? item.pa_requests[0] : item;
                  const id = pa.pa_request_id;
                  const patientId = pa.patient?.patient_id || 'N/A';
                  const patientState = pa.patient?.state || '';
                  const serviceDesc = pa.service?.service_description || 'Standard Medical Service';
                  const procedureCode = pa.service?.procedure_code;
                  const providerOrg = pa.provider?.organization_name || pa.provider?.provider_id || 'N/A';
                  const requestDate = pa.request?.request_date || pa.created_at;
                  const status = pa.status || 'COMPLETED';
                  const decision = pa.decision || 'PENDING_REVIEW';

                  return (
                    <tr key={id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="table-cell font-mono font-bold text-sky-700">
                        <Link to={`/pa/${id}`} className="hover:underline">
                          {id}
                        </Link>
                      </td>
                      <td className="table-cell">
                        <div className="font-semibold text-slate-800">{patientId}</div>
                        <div className="text-[11px] text-slate-500">
                          {pa.patient?.gender} • Age {pa.patient?.age} • {patientState}
                        </div>
                      </td>
                      <td className="table-cell text-xs text-slate-600">
                        {formatDate(requestDate)}
                      </td>
                      <td
                        className="table-cell text-xs text-slate-600 max-w-[150px] truncate"
                        title={providerOrg}
                      >
                        {providerOrg}
                      </td>
                      <td className="table-cell max-w-xs">
                        <div className="truncate font-medium text-slate-800 text-xs" title={serviceDesc}>
                          {truncateText(serviceDesc, 34)}
                        </div>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          {procedureCode ? (
                            <span className="px-1.5 py-0.2 text-[10px] font-mono font-semibold bg-sky-50 text-sky-700 border border-sky-200 rounded">
                              CPT {procedureCode}
                            </span>
                          ) : (
                            <span className="px-1.5 py-0.2 text-[10px] font-mono bg-amber-50 text-amber-700 border border-amber-200 rounded">
                              Mapping Required
                            </span>
                          )}
                        </div>
                      </td>
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
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-sky-700 bg-sky-50 hover:bg-sky-100 border border-sky-200 rounded-lg transition-colors"
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
