import React from 'react';
import { useWebSocket } from '../../context/WebSocketContext';
import { clsx } from 'clsx';
import { Radio } from 'lucide-react';

export const ConnectionStatus: React.FC = () => {
  const { status } = useWebSocket();

  const statusConfig = {
    CONNECTED: {
      text: 'LIVE CONTROL PLANE',
      color: 'text-emerald-400',
      dot: 'bg-emerald-500 shadow-emerald-500/50',
      border: 'border-emerald-900/40 bg-emerald-950/20',
    },
    CONNECTING: {
      text: 'CONNECTING...',
      color: 'text-amber-400',
      dot: 'bg-amber-500 animate-ping',
      border: 'border-amber-900/40 bg-amber-950/20',
    },
    DISCONNECTED: {
      text: 'OFFLINE SYNC',
      color: 'text-slate-400',
      dot: 'bg-slate-500',
      border: 'border-slate-800 bg-slate-900/50',
    },
  };

  const config = statusConfig[status];

  return (
    <div
      className={clsx(
        'inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono border shadow-sm',
        config.border,
        config.color
      )}
    >
      <span className={clsx('h-2 w-2 rounded-full shadow-sm', config.dot)} />
      <Radio size={13} className="opacity-80" />
      <span>{config.text}</span>
    </div>
  );
};
