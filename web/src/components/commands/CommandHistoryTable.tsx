import React from 'react';
import { DeviceCommand } from '../../types';
import { Badge } from '../common/Badge';
import { Terminal, CheckCircle2, XCircle, Clock, AlertCircle } from 'lucide-react';

interface CommandHistoryTableProps {
  commands: DeviceCommand[];
}

export const CommandHistoryTable: React.FC<CommandHistoryTableProps> = ({ commands }) => {
  if (commands.length === 0) {
    return (
      <div className="text-center py-10 text-slate-500 text-sm">
        No remote commands have been issued to this device.
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'EXECUTED':
        return <Badge variant="success">EXECUTED</Badge>;
      case 'PENDING':
        return <Badge variant="warning">PENDING</Badge>;
      case 'DELIVERED':
        return <Badge variant="info">DELIVERED</Badge>;
      case 'FAILED':
        return <Badge variant="danger">FAILED</Badge>;
      case 'EXPIRED':
        return <Badge variant="default">EXPIRED</Badge>;
      default:
        return <Badge variant="default">{status}</Badge>;
    }
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs text-slate-300">
        <thead className="text-[11px] uppercase bg-surfaceHover/60 text-slate-400 border-b border-slate-800">
          <tr>
            <th className="px-4 py-3">Command Type</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Issued At</th>
            <th className="px-4 py-3">Execution Result</th>
            <th className="px-4 py-3">Nonce / Security</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60 font-mono">
          {commands.map((cmd) => (
            <tr key={cmd.id} className="hover:bg-surfaceHover/30 transition-colors">
              <td className="px-4 py-3 font-sans font-bold text-slate-200">
                <div className="flex items-center gap-1.5">
                  <Terminal size={14} className="text-primary" />
                  <span>{cmd.command_type}</span>
                </div>
              </td>
              <td className="px-4 py-3">{getStatusBadge(cmd.status)}</td>
              <td className="px-4 py-3 text-slate-400 font-sans">
                {new Date(cmd.created_at).toLocaleString()}
              </td>
              <td className="px-4 py-3 font-sans">
                {cmd.error_message ? (
                  <span className="text-red-400 flex items-center gap-1">
                    <XCircle size={13} /> {cmd.error_message}
                  </span>
                ) : cmd.result_payload && Object.keys(cmd.result_payload).length > 0 ? (
                  <span className="text-emerald-400 font-mono text-[11px]">
                    {JSON.stringify(cmd.result_payload)}
                  </span>
                ) : (
                  <span className="text-slate-500 italic">No output</span>
                )}
              </td>
              <td className="px-4 py-3 text-slate-500 truncate max-w-[150px]" title={cmd.nonce}>
                {cmd.nonce}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
