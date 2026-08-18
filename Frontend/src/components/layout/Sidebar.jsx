import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FilePlus2,
  Layers,
  History,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

export default function Sidebar({ isCollapsed, setIsCollapsed }) {
  const navSections = [
    {
      group: 'Overview',
      items: [
        {
          name: 'Dashboard',
          path: '/',
          icon: LayoutDashboard,
          description: 'Executive Metrics & Worklist',
        },
      ],
    },
    {
      group: 'Adjudication Workflow',
      items: [
        {
          name: 'New PA Request',
          path: '/new-request',
          icon: FilePlus2,
          badge: 'Single',
          badgeColor: 'bg-slate-800 text-slate-300 border-slate-700',
        },
        {
          name: 'Batch Work Queue',
          path: '/queue',
          icon: Layers,
          badge: 'Queue',
          badgeColor: 'bg-sky-500/20 text-sky-300 border-sky-500/30',
        },
      ],
    },
    {
      group: 'Records & Audit',
      items: [
        {
          name: 'PA History',
          path: '/history',
          icon: History,
          description: 'Historical Determinations',
        },
      ],
    },
  ];

  return (
    <aside
      className={`fixed top-0 bottom-0 left-0 z-30 flex flex-col bg-[#0b1329] text-slate-300 border-r border-slate-800/90 shadow-xl transition-all duration-200 select-none ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-3.5 border-b border-slate-800/90 bg-[#080e1e]">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-600 to-blue-500 flex items-center justify-center text-white shadow-md shadow-sky-900/30 ring-1 ring-white/15">
            <ShieldCheck className="w-5 h-5" />
          </div>
          {!isCollapsed && (
            <div className="flex flex-col truncate">
              <span className="text-[13px] font-extrabold text-white tracking-tight flex items-center gap-1.5">
                <span>PA Intelligence</span>
                <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-sky-500/20 text-sky-300 border border-sky-400/25">
                  v2.0
                </span>
              </span>
              <span className="text-[10px] text-slate-400 font-semibold tracking-wider uppercase">
                Enterprise UM Companion
              </span>
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors"
          title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          aria-label={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Nav List with Visual Grouping */}
      <nav className="flex-1 py-4 px-2.5 space-y-4 overflow-y-auto custom-scrollbar">
        {navSections.map((section, sIdx) => (
          <div key={sIdx} className="space-y-1">
            {!isCollapsed && section.group && (
              <div className="px-2.5 pb-1 pt-0.5 text-[10px] font-bold tracking-wider text-slate-500 uppercase">
                {section.group}
              </div>
            )}

            <div className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all group relative ${
                        isActive
                          ? 'bg-gradient-to-r from-sky-500/20 via-sky-500/10 to-transparent text-white font-bold border-l-[3px] border-sky-400 shadow-sm'
                          : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/50'
                      }`
                    }
                    title={isCollapsed ? item.name : undefined}
                  >
                    <Icon className="w-4 h-4 flex-shrink-0 transition-transform group-hover:scale-105" />
                    {!isCollapsed && (
                      <div className="flex-1 flex items-center justify-between truncate">
                        <span className="truncate">{item.name}</span>
                        {item.badge && (
                          <span
                            className={`px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded-md border ${
                              item.badgeColor || 'bg-slate-800 text-slate-300 border-slate-700'
                            }`}
                          >
                            {item.badge}
                          </span>
                        )}
                      </div>
                    )}
                  </NavLink>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
}
