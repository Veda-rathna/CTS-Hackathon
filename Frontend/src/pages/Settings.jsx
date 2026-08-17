import React, { useState, useEffect } from 'react';
import { checkHealth, checkDbHealth } from '../services/api';
import { INITIAL_PA_REQUESTS } from '../utils/mockData';
import {
  Server,
  Database,
  RotateCcw,
  RefreshCw,
  Sliders,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import Toast from '../components/common/Toast';

export default function Settings() {
  const [health, setHealth] = useState({ online: false, checking: true, data: null });
  const [dbHealth, setDbHealth] = useState({ online: false, checking: true, data: null });
  const [toast, setToast] = useState(null);

  const checkStatus = async () => {
    setHealth({ online: false, checking: true, data: null });
    setDbHealth({ online: false, checking: true, data: null });

    const h = await checkHealth();
    setHealth({ online: h.online, checking: false, data: h.data });

    const db = await checkDbHealth();
    setDbHealth({ online: db.online, checking: false, data: db.data });
  };

  useEffect(() => {
    checkStatus();
  }, []);

  const handleResetData = () => {
    localStorage.setItem('pa_intelligence_requests_v1', JSON.stringify(INITIAL_PA_REQUESTS));
    localStorage.removeItem('pa_intelligence_form_draft_v1');
    setToast({ message: 'Prior authorization test cases reset to default baseline.', type: 'success' });
  };

  return (
    <div className="space-y-5 max-w-4xl">
      {/* Header */}
      <div className="pb-3 border-b border-slate-200/90">
        <div className="flex items-center gap-2">
          <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
            Platform Settings & Environment
          </h2>
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            System Config
          </span>
        </div>
        <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
          Backend service connectivity, policy database status, and client storage management
        </p>
      </div>

      {/* Backend Connectivity Card */}
      <div className="healthcare-card p-4 sm:p-5 space-y-3.5 bg-white">
        <div className="flex items-center justify-between pb-2.5 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-sky-700" />
            <div>
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">FastAPI Backend Connection</h3>
              <p className="text-[11px] text-slate-500">
                Connected via <code className="font-mono font-bold text-sky-800">VITE_API_BASE_URL</code>
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={checkStatus}
            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold text-sky-700 bg-sky-50 hover:bg-sky-100 rounded-lg border border-sky-200 transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Test Connection</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          {/* API Health */}
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-700">Triage Engine API</span>
              <span
                className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                  health.online
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                    : 'bg-amber-50 text-amber-800 border border-amber-200'
                }`}
              >
                {health.checking ? 'Checking...' : health.online ? 'Online (200 OK)' : 'Offline / Fallback'}
              </span>
            </div>
            <p className="text-slate-500 text-[11px]">Endpoint: /api/v1/health</p>
            {health.data && (
              <pre className="text-[10px] font-mono text-slate-700 bg-white p-2 rounded border border-slate-200 overflow-x-auto">
                {JSON.stringify(health.data, null, 2)}
              </pre>
            )}
          </div>

          {/* Database Health */}
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-700">Policy Knowledge Store</span>
              <span
                className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                  dbHealth.online
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                    : 'bg-amber-50 text-amber-800 border border-amber-200'
                }`}
              >
                {dbHealth.checking ? 'Checking...' : dbHealth.online ? 'Ready' : 'Mock Repositories'}
              </span>
            </div>
            <p className="text-slate-500 text-[11px]">Endpoint: /api/v1/health/db</p>
            {dbHealth.data && (
              <pre className="text-[10px] font-mono text-slate-700 bg-white p-2 rounded border border-slate-200 overflow-x-auto">
                {JSON.stringify(dbHealth.data, null, 2)}
              </pre>
            )}
          </div>
        </div>
      </div>

      {/* Storage & Data Management */}
      <div className="healthcare-card p-4 sm:p-5 space-y-3.5 bg-white">
        <div className="flex items-center gap-2 pb-2.5 border-b border-slate-100">
          <Database className="w-4 h-4 text-sky-700" />
          <div>
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Local Demonstration Storage</h3>
            <p className="text-[11px] text-slate-500">Manage client-side cached PA records and form drafts</p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
          <div>
            <span className="text-xs font-bold text-slate-800 block">Reset Pre-seeded Sample Records</span>
            <span className="text-[11px] text-slate-500">
              Restores baseline sample prior authorization requests (Epidural, Stem Cell, Dental cases).
            </span>
          </div>

          <button
            type="button"
            onClick={handleResetData}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-lg transition-colors self-start sm:self-auto"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Demo Data</span>
          </button>
        </div>
      </div>

      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
}
