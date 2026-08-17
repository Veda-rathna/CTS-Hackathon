import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { checkHealth } from '../../services/api';
import {
  PlusCircle,
  ShieldCheck,
  User,
  Activity,
  Server,
  Layers,
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
    const interval = setInterval(verifyHealth, 12000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const getPageTitle = (path) => {
    if (path === '/') return 'Prior Authorization Command Center';
    if (path === '/new-request') return 'Prior Authorization Clinical Intake & Evaluation';
    if (path === '/queue') return 'Prior Authorization Work Queue & Batch Orchestration';
    if (path === '/history') return 'Prior Authorization Clinical History & Audit Worklist';
    if (path.startsWith('/pa/')) return 'Prior Authorization Clinical Decision Summary';
    if (path === '/settings') return 'Platform Settings & Environment Health';
    return 'Prior Authorization Intelligence';
  };

  return (
    <header
      className={`fixed top-0 right-0 z-20 h-16 bg-white/95 backdrop-blur-sm border-b border-slate-200/90 flex items-center justify-between px-5 transition-all duration-200 ${
        isCollapsed ? 'left-16' : 'left-64'
      }`}
    >
      {/* Page Title */}
      <div className="flex items-center gap-3">
        <h1 className="text-sm sm:text-base font-bold text-slate-900 tracking-tight">
          {getPageTitle(location.pathname)}
        </h1>
      </div>

      {/* Right Actions & User Profile */}
      <div className="flex items-center gap-3.5">
        {/* Live Backend Status Indicator */}
        <div
          className={`flex items-center gap-2 px-2.5 py-1 rounded-full text-[11px] font-semibold border ${
            apiStatus.online
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
              : 'bg-amber-50 text-amber-800 border-amber-200'
          }`}
          title={
            apiStatus.online
              ? 'FastAPI Backend Active (port 8001)'
              : 'FastAPI Backend Offline'
          }
        >
          <span className="relative flex h-2 w-2">
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                apiStatus.online ? 'bg-emerald-400' : 'bg-amber-400'
              }`}
            />
            <span
              className={`relative inline-flex rounded-full h-2 w-2 ${
                apiStatus.online ? 'bg-emerald-500' : 'bg-amber-500'
              }`}
            />
          </span>
          <span className="hidden sm:inline font-mono font-bold">
            {apiStatus.checking ? 'Connecting...' : apiStatus.online ? 'API Online :8001' : 'Offline'}
          </span>
        </div>

        {/* Quick Batch Queue Link */}
        {location.pathname !== '/queue' && (
          <Link
            to="/queue"
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded-lg shadow-sm transition-all"
          >
            <Layers className="w-3.5 h-3.5 text-sky-700" />
            <span>Work Queue</span>
          </Link>
        )}

        {/* Quick New PA Request Button */}
        {location.pathname !== '/new-request' && (
          <Link
            to="/new-request"
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-white bg-sky-700 hover:bg-sky-800 rounded-lg shadow-sm transition-all"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>New Evaluation</span>
          </Link>
        )}

        {/* User Identity */}
        <div className="flex items-center gap-2.5 pl-3 border-l border-slate-200">
          <div className="w-7 h-7 rounded-lg bg-slate-900 text-white font-bold text-[11px] flex items-center justify-center shadow-sm">
            XYZ
          </div>
          <div className="hidden md:flex flex-col text-left">
            <span className="text-xs font-bold text-slate-800 leading-tight">Dr. XYZ</span>
            <span className="text-[10px] text-slate-500 font-medium leading-tight">Senior Clinical Reviewer</span>
          </div>
        </div>
      </div>
    </header>
  );
}
