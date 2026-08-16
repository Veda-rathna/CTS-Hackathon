import React, { useState, useEffect } from 'react';
import { checkHealth, checkDbHealth } from '../services/api';
import { INITIAL_PA_REQUESTS } from '../utils/mockData';
import {
  Settings as SettingsIcon,
  Server,
  Database,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Cpu,
  Shield,
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
    setToast({ message: 'Prior authorization test cases reset to default.', type: 'success' });
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="pb-2 border-b border-slate-200">
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
          Platform Settings & Environment
        </h2>
        <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
          Backend service connectivity, policy database status, and client storage management
        </p>
      </div>

      {/* Backend Connectivity Card */}
      <div className="healthcare-card p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <Server className="w-5 h-5 text-sky-600" />
            <div>
              <h3 className="text-sm font-bold text-slate-800">FastAPI Backend Connection</h3>
              <p className="text-xs text-slate-500">
                Connected via <code className="font-mono text-sky-700">VITE_API_BASE_URL</code>
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={checkStatus}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-sky-700 bg-sky-50 hover:bg-sky-100 rounded-lg border border-sky-200 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Test Connection</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          {/* API Health */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-700">Triage Engine API</span>
              <span
                className={`px-2 py-0.5 rounded-full font-semibold text-[11px] ${
                  health.online
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-amber-50 text-amber-700 border border-amber-200'
                }`}
              >
                {health.checking ? 'Checking...' : health.online ? 'Online (200 OK)' : 'Offline / Fallback'}
              </span>
            </div>
            <p className="text-slate-500 text-[11px]">Endpoint: /api/v1/health</p>
            {health.data && (
              <pre className="text-[10px] font-mono text-slate-600 bg-white p-2 rounded border border-slate-100">
                {JSON.stringify(health.data, null, 2)}
              </pre>
            )}
          </div>

          {/* Database Health */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-700">Policy Knowledge Store</span>
              <span
                className={`px-2 py-0.5 rounded-full font-semibold text-[11px] ${
                  dbHealth.online
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-amber-50 text-amber-700 border border-amber-200'
                }`}
              >
                {dbHealth.checking ? 'Checking...' : dbHealth.online ? 'Ready' : 'Mock Repositories'}
              </span>
            </div>
            <p className="text-slate-500 text-[11px]">Endpoint: /api/v1/health/db</p>
            {dbHealth.data && (
              <pre className="text-[10px] font-mono text-slate-600 bg-white p-2 rounded border border-slate-100">
                {JSON.stringify(dbHealth.data, null, 2)}
              </pre>
            )}
          </div>
        </div>
      </div>

      {/* Storage & Data Reset */}
      <div className="healthcare-card p-6 space-y-4">
        <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
          <Database className="w-5 h-5 text-sky-600" />
          <div>
            <h3 className="text-sm font-bold text-slate-800">Local Demonstration Storage</h3>
            <p className="text-xs text-slate-500">Manage client-side cached PA records and form drafts</p>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2">
          <div>
            <span className="text-xs font-semibold text-slate-800 block">Reset Pre-seeded Sample Records</span>
            <span className="text-[11px] text-slate-500">
              Restores baseline sample prior authorization requests (Epidural, Stem Cell, Dental cases).
            </span>
          </div>

          <button
            type="button"
            onClick={handleResetData}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-xl transition-colors"
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
