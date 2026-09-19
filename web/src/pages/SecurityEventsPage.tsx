import React, { useEffect, useState } from 'react';
import { deviceService } from '../services/devices';
import { eventService } from '../services/events';
import { Device, SecurityEvent } from '../types';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Spinner } from '../components/common/Spinner';
import { Badge } from '../components/common/Badge';
import { Activity, ShieldAlert, RefreshCw } from 'lucide-react';

export const SecurityEventsPage: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadEvents = async () => {
    try {
      const devList = await deviceService.listDevices();
      setDevices(devList);
      const targetId = selectedDeviceId || (devList.length > 0 ? devList[0].id : '');
      setSelectedDeviceId(targetId);

      if (targetId) {
        const list = await eventService.getDeviceSecurityEvents(targetId, 100);
        setEvents(list);
      }
    } catch (e) {
      console.error('Failed to load security events', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, [selectedDeviceId]);

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return <Badge variant="danger">CRITICAL</Badge>;
      case 'HIGH':
        return <Badge variant="warning">HIGH</Badge>;
      case 'MEDIUM':
        return <Badge variant="info">MEDIUM</Badge>;
      default:
        return <Badge variant="default">LOW</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 uppercase tracking-wide">
            Security & Tamper Events
          </h1>
          <p className="text-xs text-slate-400">
            Immutable device security events (Power-off attempts, Factory reset blocks, SIM swaps)
          </p>
        </div>

        <div className="flex items-center gap-3">
          {devices.length > 0 && (
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
          <Button variant="secondary" size="sm" onClick={loadEvents} icon={<RefreshCw size={14} />}>
            Refresh
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
              <Activity className="text-red-400" size={18} />
              <span className="font-bold text-sm text-slate-200 uppercase tracking-wider">
                Event Log Ledger ({events.length})
              </span>
            </div>
            <span className="text-xs text-slate-500 font-mono">
              Signed by Hardware Keystore • Tamper Protected
            </span>
          </div>

          <div className="divide-y divide-slate-800/60">
            {events.length === 0 ? (
              <div className="text-center py-12 text-slate-500 text-sm">
                No security alerts or threat triggers recorded for this device.
              </div>
            ) : (
              events.map((evt) => (
                <div key={evt.id} className="p-4 hover:bg-surfaceHover/20 transition-colors flex items-start gap-4">
                  <div className="p-2.5 rounded-xl bg-red-950/60 border border-red-800/80 text-red-400 mt-0.5">
                    <ShieldAlert size={20} />
                  </div>
                  <div className="flex-1 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-slate-100">{evt.event_type}</span>
                        {getSeverityBadge(evt.severity)}
                      </div>
                      <span className="text-xs text-slate-500 font-mono">
                        {new Date(evt.device_timestamp).toLocaleString()}
                      </span>
                    </div>

                    <div className="text-xs text-slate-400">
                      State Transition: <span className="text-slate-300 font-bold">{evt.security_state_before}</span> &rarr;{' '}
                      <span className="text-red-400 font-bold">{evt.security_state_after}</span>
                    </div>

                    {evt.payload && Object.keys(evt.payload).length > 0 && (
                      <div className="font-mono text-xs bg-background p-2.5 rounded-lg border border-slate-800 text-slate-300">
                        {JSON.stringify(evt.payload, null, 2)}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      )}
    </div>
  );
};
