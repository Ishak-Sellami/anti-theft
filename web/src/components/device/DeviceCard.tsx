import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Device } from '../../types';
import { Card } from '../common/Card';
import { StateBadge } from './StateBadge';
import { BatteryIndicator } from './BatteryIndicator';
import { Smartphone, MapPin, Clock, ShieldAlert, ArrowRight } from 'lucide-react';
import { clsx } from 'clsx';

interface DeviceCardProps {
  device: Device;
}

export const DeviceCard: React.FC<DeviceCardProps> = ({ device }) => {
  const navigate = useNavigate();
  const isStolen = device.security_state === 'STOLEN';

  const formatLastSeen = (timestamp?: string) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' ' + date.toLocaleDateString();
  };

  return (
    <Card
      hoverable
      onClick={() => navigate(`/devices/${device.id}`)}
      className={clsx(
        'relative overflow-hidden transition-all border',
        isStolen
          ? 'border-red-600/80 bg-red-950/20 shadow-red-950/40'
          : 'hover:border-primary/50'
      )}
    >
      {isStolen && (
        <div className="absolute top-0 right-0 left-0 bg-red-600 text-white text-[11px] font-black uppercase text-center py-0.5 tracking-wider flex items-center justify-center gap-1.5 animate-pulse">
          <ShieldAlert size={14} /> ACTIVE THEFT INCIDENT DETECTED
        </div>
      )}

      <div className={clsx('space-y-4', isStolen && 'pt-3')}>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div
              className={clsx(
                'p-2.5 rounded-xl border',
                isStolen
                  ? 'bg-red-950 border-red-800 text-red-400'
                  : 'bg-surfaceHover border-slate-700 text-primary'
              )}
            >
              <Smartphone size={22} />
            </div>
            <div>
              <h3 className="font-bold text-base text-slate-100">{device.device_name}</h3>
              <p className="text-xs text-slate-400 font-mono">
                {device.device_model || 'Unknown Model'} • {device.os_version || 'Android'}
              </p>
            </div>
          </div>
          <StateBadge type="security" value={device.security_state} />
        </div>

        {/* 3D State Dimensions */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/80">
          <StateBadge type="connectivity" value={device.connectivity_state} />
          <StateBadge type="power" value={device.power_state} />
          <div className="ml-auto">
            <BatteryIndicator level={device.battery_level} isCharging={device.is_charging} />
          </div>
        </div>

        {/* Telemetry snippet */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-400 bg-background/50 p-2.5 rounded-lg border border-slate-800">
          <div className="flex items-center gap-1.5 truncate">
            <MapPin size={14} className="text-slate-500 shrink-0" />
            {device.last_known_latitude && device.last_known_longitude ? (
              <span className="font-mono text-slate-300">
                {device.last_known_latitude.toFixed(4)}, {device.last_known_longitude.toFixed(4)}
              </span>
            ) : (
              <span className="text-slate-500 italic">No GPS Fix yet</span>
            )}
          </div>
          <div className="flex items-center gap-1.5 truncate">
            <Clock size={14} className="text-slate-500 shrink-0" />
            <span>Last contact: {formatLastSeen(device.last_heartbeat_at || device.last_known_location_at)}</span>
          </div>
        </div>

        <div className="flex items-center justify-between pt-1">
          <span className="text-[11px] font-mono text-slate-500 truncate max-w-[200px]" title={device.public_key_fingerprint}>
            FP: {device.public_key_fingerprint.slice(0, 16)}...
          </span>
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-primary group-hover:translate-x-1 transition-transform">
            View Details <ArrowRight size={14} />
          </span>
        </div>
      </div>
    </Card>
  );
};
