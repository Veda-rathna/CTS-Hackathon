import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  PlusCircle,
  ShieldCheck,
  User,
  Layers,
  LogOut,
  ChevronDown,
} from 'lucide-react';

export default function Header({ isCollapsed }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { provider, logout } = useAuth();
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const profileMenuRef = useRef(null);

  // Handle click outside to close profile dropdown
  useEffect(() => {
    function handleClickOutside(event) {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target)) {
        setIsProfileOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    setIsProfileOpen(false);
    logout();
    navigate('/login', { replace: true });
  };

  const getPageTitle = (path) => {
    if (path === '/') return 'Prior Authorization Command Center';
    if (path === '/new-request') return 'Prior Authorization Clinical Intake & Evaluation';
    if (path === '/queue') return 'Prior Authorization Work Queue & Batch Orchestration';
    if (path === '/history') return 'Prior Authorization Clinical History & Audit Worklist';
    if (path.startsWith('/pa/')) return 'Prior Authorization Clinical Decision Summary';
    return 'Prior Authorization Intelligence';
  };

  const providerName = provider?.name || 'Dr. Veda Rathna';
  const providerRole = provider?.role || 'Clinical Reviewer';
  const providerInitials = provider?.initials || 'VR';
  const providerId = provider?.id || 'PROV-001';
  const providerEmail = provider?.username || 'provider1@pa-demo.local';

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

        {/* Authenticated Provider Identity Dropdown */}
        <div className="relative pl-3 border-l border-slate-200" ref={profileMenuRef}>
          <button
            type="button"
            onClick={() => setIsProfileOpen(!isProfileOpen)}
            className="flex items-center gap-2.5 p-1 rounded-xl hover:bg-slate-100/80 transition-all text-left focus:outline-none focus:ring-2 focus:ring-sky-500/20"
            aria-expanded={isProfileOpen}
            aria-haspopup="true"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-slate-900 to-slate-800 text-white font-bold text-xs flex items-center justify-center shadow-sm ring-1 ring-slate-900/10">
              {providerInitials}
            </div>
            <div className="hidden md:flex flex-col text-left">
              <span className="text-xs font-bold text-slate-800 leading-tight flex items-center gap-1">
                {providerName}
                <ChevronDown className={`w-3 h-3 text-slate-400 transition-transform ${isProfileOpen ? 'rotate-180' : ''}`} />
              </span>
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] text-slate-500 font-medium leading-tight">
                  {providerRole}
                </span>
                <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-slate-100 text-slate-600 border border-slate-200">
                  {providerId}
                </span>
              </div>
            </div>
          </button>

          {/* Dropdown Popover */}
          {isProfileOpen && (
            <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-xl border border-slate-200/90 py-2 z-50 animate-fadeIn">
              <div className="px-4 py-2.5 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-md bg-sky-50 text-sky-700 font-bold text-[11px] flex items-center justify-center border border-sky-200/60">
                    {providerInitials}
                  </div>
                  <div className="overflow-hidden">
                    <p className="text-xs font-bold text-slate-900 truncate">{providerName}</p>
                    <p className="text-[11px] text-slate-500 truncate">{providerEmail}</p>
                  </div>
                </div>
                <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px]">
                  <span className="text-slate-500 font-medium">Role: {providerRole}</span>
                  <span className="font-mono font-bold text-sky-700 bg-sky-50 px-1.5 py-0.5 rounded border border-sky-100">
                    {providerId}
                  </span>
                </div>
              </div>

              <div className="p-1.5">
                <button
                  type="button"
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                >
                  <LogOut className="w-4 h-4 text-rose-500" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
