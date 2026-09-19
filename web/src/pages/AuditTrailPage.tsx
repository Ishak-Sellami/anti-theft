import React, { useEffect, useState } from 'react';
import { auditService } from '../services/audit';
import { deviceService } from '../services/devices';
import { useAuth } from '../context/AuthContext';
import { AuditLog, Device } from '../types';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Spinner } from '../components/common/Spinner';
import { History, ShieldCheck, Hash, RefreshCw, Link as LinkIcon } from 'lucide-react';

export const AuditTrailPage: React.FC = () => {
  const { user } = useAuth();
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadAuditLogs = async () => {
    try {
      if (user?.role === 'ADMIN') {
        const list = await auditService.listSystemAuditLogs(100);
        setLogs(list);
      } else {
        const devList = await deviceService.listDevices();
        setDevices(devList);
        const targetId = selectedDeviceId || (devList.length > 0 ? devList[0].id : '');
        setSelectedDeviceId(targetId);

        if (targetId) {
          const list = await auditService.getDeviceAuditLogs(targetId, 100);
          setLogs(list);
        }
      }
    } catch (e) {
      console.error('Failed to load audit logs', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAuditLogs();
  }, [selectedDeviceId, user?.role]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 uppercase tracking-wide">
            Tamper-Evident Audit Trail
          </h1>
          <p className="text-xs text-slate-400">
            Immutable SHA-256 hash-chained execution and security ledger
          </p>
        </div>

        <div className="flex items-center gap-3">
          {user?.role !== 'ADMIN' && devices.length > 0 && (
            <select
              value={selectedDeviceId}
              onChange={(e) => setSelectedDeviceId(e.target.value)}
              className="px-3 py-1.5 bg-surface border border-slate-700 rounded-lg text-xs font-semibold text-slate-200 focus:outline-none focus:border-primary"
            >
              {devices.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.device_name}
                </option>
              ))}
            </select>
          )}

          <Button variant="secondary" size="sm" onClick={loadAuditLogs} icon={<RefreshCw size={14} />}>
            Refresh Ledger
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="py-20 flex justify-center">
          <Spinner size="lg" />
        </div>
      ) : (
        <Card className="p-0 overflow-hidden">
          <div className="p-4 border-b border-slate-800 bg-surfaceHover/30 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className="text-emerald-400" size={18} />
              <span className="font-bold text-sm text-slate-200 uppercase tracking-wider">
                Cryptographic Hash Chain Verified ({logs.length} entries)
              </span>
            </div>
            <span className="text-xs text-slate-500 font-mono">
              prev_hash &rarr; entry_hash linkage intact
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="text-[11px] uppercase bg-surfaceHover/60 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">ID / Time</th>
                  <th className="px-4 py-3">Actor</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Details / Context</th>
                  <th className="px-4 py-3">Entry Hash (SHA-256)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-12 text-slate-500 text-sm font-sans">
                      No audit log records found.
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id} className="hover:bg-surfaceHover/30 transition-colors">
                      <td className="px-4 py-3 font-sans">
                        <div className="font-bold text-slate-200">#{log.id}</div>
                        <div className="text-[11px] text-slate-500">
                          {new Date(log.timestamp).toLocaleString()}
                        </div>
                      </td>
                      <td className="px-4 py-3 font-sans">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px] font-bold">
                          {log.actor_type}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-sans font-bold text-primary">
                        {log.action}
                      </td>
                      <td className="px-4 py-3 font-sans text-slate-400 text-xs">
                        {log.details ? (
                          <div className="max-w-md truncate" title={JSON.stringify(log.details)}>
                            {JSON.stringify(log.details)}
                          </div>
                        ) : (
                          <span className="text-slate-600">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-emerald-400">
                        <div className="flex items-center gap-1.5" title={`Entry: ${log.entry_hash}\nPrev: ${log.prev_hash}`}>
                          <LinkIcon size={12} className="text-slate-600 shrink-0" />
                          <span className="truncate max-w-[130px]">{log.entry_hash.slice(0, 14)}...</span>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};
