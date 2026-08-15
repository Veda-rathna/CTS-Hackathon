import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { checkHealth } from '../../services/api';
import {
  PlusCircle,
  ShieldCheck,
  User,
  Activity,
  Server,
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
    if (path === '/') return 'Prior Authorization Triage Command Center';
    if (path === '/new-request') return 'Prior Authorization Intake & Evaluation';
    if (path === '/history') return 'Prior Authorization History & Audit Records';
    if (path.startsWith('/pa/')) return 'Prior Authorization Clinical Evaluation Report';
    if (path === '/settings') return 'Platform Settings & API Status';
    return 'Prior Authorization Intelligence';
  };

  return (
    <header
      className={`fixed top-0 right-0 z-20 h-16 bg-white/90 backdrop-blur-md border-b border-slate-200/80 flex items-center justify-between px-6 transition-all duration-300 ${
        isCollapsed ? 'left-20' : 'left-64'
      }`}
    >
      {/* Page Title */}
      <div className="flex items-center gap-3">
        <h1 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight">
          {getPageTitle(location.pathname)}
        </h1>
      </div>

      {/* Right Actions & User Profile */}
      <div className="flex items-center gap-4">
        {/* Live Backend Status Indicator */}
        <div
          className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold border ${
            apiStatus.online
              ? 'bg-emerald-50/80 text-emerald-800 border-emerald-200'
              : 'bg-amber-50/80 text-amber-800 border-amber-200'
          }`}
          title={
            apiStatus.online
              ? 'FastAPI Backend API Active (port 8001)'
              : 'FastAPI Backend Standby / Offline'
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
          <span className="hidden sm:inline font-mono">
            {apiStatus.checking ? 'Connecting...' : apiStatus.online ? 'API Online :8001' : 'Offline'}
          </span>
        </div>

        {/* Quick New PA Request Button */}
        {location.pathname !== '/new-request' && (
          <Link
            to="/new-request"
            className="hidden sm:inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold text-white bg-sky-600 hover:bg-sky-700 rounded-xl shadow-2xs transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Request</span>
          </Link>
        )}

        {/* User Identity */}
        <div className="flex items-center gap-2.5 pl-3 border-l border-slate-200">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-sky-500 to-indigo-600 text-white font-bold text-xs flex items-center justify-center shadow-2xs">
            VR
          </div>
          <div className="hidden md:flex flex-col text-left">
            <span className="text-xs font-bold text-slate-800 leading-tight">Dr. Vedarathna</span>
            <span className="text-[10px] text-sky-600 font-semibold leading-tight">Senior Clinical Reviewer</span>
          </div>
        </div>
      </div>
    </header>
  );
}
