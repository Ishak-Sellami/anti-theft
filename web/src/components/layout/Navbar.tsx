import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { ConnectionStatus } from './ConnectionStatus';
import { Shield, LogOut, User as UserIcon, Menu } from 'lucide-react';
import { Badge } from '../common/Badge';

interface NavbarProps {
  onToggleSidebar?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onToggleSidebar }) => {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-4 md:px-6 bg-surface/90 backdrop-blur-md border-b border-slate-800">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="p-2 -ml-2 text-slate-400 hover:text-white rounded-lg md:hidden hover:bg-slate-800"
        >
          <Menu size={20} />
        </button>
        <div className="flex items-center gap-2.5">
          <div className="flex items-center justify-center p-2 rounded-xl bg-primary/10 border border-primary/20 text-primary">
            <Shield size={22} className="stroke-[2.5]" />
          </div>
          <div>
            <span className="text-lg font-black tracking-wider text-slate-100 uppercase">
              Anti<span className="text-primary font-light">-Sarika</span>
            </span>
            <span className="hidden sm:inline-block ml-2 text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
              v0.1 Control Plane
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <ConnectionStatus />

        {user && (
          <div className="flex items-center gap-3 pl-3 border-l border-slate-800">
            <div className="hidden sm:flex flex-col items-end">
              <span className="text-xs font-semibold text-slate-200">{user.full_name || user.email}</span>
              <Badge variant={user.role === 'ADMIN' ? 'purple' : 'info'} size="sm">
                {user.role}
              </Badge>
            </div>
            <button
              onClick={logout}
              title="Logout"
              className="p-2 text-slate-400 hover:text-red-400 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <LogOut size={18} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
