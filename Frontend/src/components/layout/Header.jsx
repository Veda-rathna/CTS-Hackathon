import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { checkHealth } from '../../services/api';
import {
  Activity,
  PlusCircle,
  Bell,
  Search,
  User,
  ExternalLink,
  CheckCircle,
  WifiOff,
} from 'lucide-react';

export default function Header({ isCollapsed }) {
  const location = useLocation();
  const [apiStatus, setApiStatus] = useState({ online: false, checking: true });

  useEffect(() => {
    let mounted = true;
    async function verifyHealth() {
      const res = await checkHealth();
      if (mounted) {
        setApiStatus({ online: res.online, checking: false });
      }
    }
    verifyHealth();
    const interval = setInterval(verifyHealth, 15000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const getPageTitle = (path) => {
    if (path === '/') return 'Clinical Triage Dashboard';
    if (path === '/new-request') return 'Create Prior Authorization Request';
    if (path === '/history') return 'Prior Authorization History';
    if (path === '/policies') return 'CMS Medicare Coverage Policy Explorer';
    if (path === '/audit') return 'Deterministic Audit Trail & Pipeline';
    if (path.startsWith('/pa/')) return 'Prior Authorization Evaluation Result';
    if (path === '/settings') return 'Platform Settings & Environment';
    return 'Prior Authorization Intelligence';
  };

  return (
    <header
      className={`fixed top-0 right-0 z-20 h-16 bg-white/95 backdrop-blur-sm border-b border-slate-200 flex items-center justify-between px-6 transition-all duration-300 ${
        isCollapsed ? 'left-20' : 'left-64'
      }`}
    >
      {/* Page Title & Breadcrumb */}
      <div className="flex items-center gap-3">
        <h1 className="text-base sm:text-lg font-semibold text-slate-800 tracking-tight">
          {getPageTitle(location.pathname)}
        </h1>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        {/* Live Backend Indicator */}
        <div
          className={`flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-medium border ${
            apiStatus.online
              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
              : 'bg-amber-50 text-amber-700 border-amber-200'
          }`}
          title={
            apiStatus.online
              ? 'Connected to FastAPI Backend (port 8000)'
              : 'FastAPI Backend unreachable. Utilizing offline fallback engine.'
          }
        >
          <span className="relative flex h-2 w-2">
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                apiStatus.online ? 'bg-emerald-400' : 'bg-amber-400'
              }`}
            ></span>
            <span
              className={`relative inline-flex rounded-full h-2 w-2 ${
                apiStatus.online ? 'bg-emerald-500' : 'bg-amber-500'
              }`}
            ></span>
          </span>
          <span className="hidden sm:inline">
            {apiStatus.checking ? 'Connecting...' : apiStatus.online ? 'FastAPI Connected' : 'Local Fallback'}
          </span>
        </div>

        {/* Quick New PA Button */}
        {location.pathname !== '/new-request' && (
          <Link
            to="/new-request"
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-sky-600 hover:bg-sky-700 rounded-lg shadow-sm transition-colors"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New PA</span>
          </Link>
        )}

        {/* User Identity */}
        <div className="flex items-center gap-3 pl-3 border-l border-slate-200">
          <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-300 flex items-center justify-center text-slate-600 font-semibold text-xs">
            DR
          </div>
          <div className="hidden md:flex flex-col text-left">
            <span className="text-xs font-semibold text-slate-800 leading-tight">Dr. Vedarathna</span>
            <span className="text-[10px] text-slate-500 leading-tight">Clinical Reviewer</span>
          </div>
        </div>
      </div>
    </header>
  );
}
