import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Smartphone,
  AlertTriangle,
  FileKey,
  Terminal,
  Sliders,
  Activity,
  History,
} from 'lucide-react';
import { clsx } from 'clsx';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const navItems = [
    { label: 'Dashboard Overview', path: '/', icon: LayoutDashboard },
    { label: 'Devices Fleet', path: '/devices', icon: Smartphone },
    {
      label: 'STOLEN Incident Center',
      path: '/stolen-center',
      icon: AlertTriangle,
      highlight: true,
    },
    { label: 'Evidence Vault', path: '/evidence', icon: FileKey },
    { label: 'Remote Commands', path: '/commands', icon: Terminal },
    { label: 'Recovery Policies', path: '/policies', icon: Sliders },
    { label: 'Security Events', path: '/events', icon: Activity },
    { label: 'Audit Log Trail', path: '/audit', icon: History },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={clsx(
          'fixed md:static inset-y-0 left-0 z-40 flex flex-col w-64 bg-surface border-r border-slate-800 transition-transform duration-200 ease-in-out md:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
            Control Center
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all',
                    isActive
                      ? item.highlight
                        ? 'bg-red-950/60 text-red-400 border border-red-800/80 shadow-md shadow-red-950/50 font-bold'
                        : 'bg-primary/10 text-primary border border-primary/20 shadow-md shadow-primary/5 font-bold'
                      : item.highlight
                      ? 'text-red-400/90 hover:bg-red-950/30 hover:text-red-300'
                      : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                  )
                }
              >
                <Icon size={18} className="shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </div>

        <div className="p-4 border-t border-slate-800 bg-background/30">
          <div className="p-3 rounded-xl border border-slate-800 bg-surface/50 text-[11px] text-slate-400 space-y-1">
            <div className="font-semibold text-slate-300">Security Architecture</div>
            <div>• Zero-Trust Asymmetric ECDSA</div>
            <div>• Tamper-Evident Hash Chaining</div>
            <div>• Isolated Owner Controls</div>
          </div>
        </div>
      </aside>
    </>
  );
};
