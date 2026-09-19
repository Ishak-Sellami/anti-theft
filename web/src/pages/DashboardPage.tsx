import React, { useEffect, useState, useCallback } from 'react';
import { deviceService } from '../services/devices';
import { Device } from '../types';
import { DeviceCard } from '../components/device/DeviceCard';
import { EnrollModal } from '../components/device/EnrollModal';
import { Button } from '../components/common/Button';
import { Spinner } from '../components/common/Spinner';
import { Card } from '../components/common/Card';
import { LiveMap } from '../components/map/LiveMap';
import { useWebSocket } from '../context/WebSocketContext';
import {
  Smartphone,
  AlertTriangle,
  Radio,
  Plus,
  RefreshCw,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const DashboardPage: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isEnrollModalOpen, setIsEnrollModalOpen] = useState(false);
  const { subscribe } = useWebSocket();

  const fetchDevices = useCallback(async () => {
    try {
      const list = await deviceService.listDevices();
      setDevices(list);
    } catch (e) {
      console.error('Failed to fetch devices', e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDevices();

    // Subscribe to live WebSocket events for reactive updates
    const unsubscribe = subscribe((msg) => {
      if (
        msg.event_type === 'DEVICE_STATE_CHANGED' ||
        msg.event_type === 'TELEMETRY_INGESTED' ||
        msg.event_type === 'SECURITY_EVENT_CREATED' ||
        msg.event_type === 'DEVICE_ENROLLED'
      ) {
        fetchDevices();
      }
    });

    return () => unsubscribe();
  }, [fetchDevices, subscribe]);

  const stolenDevices = devices.filter((d) => d.security_state === 'STOLEN');
  const onlineDevices = devices.filter((d) => d.connectivity_state === 'ONLINE');
  const protectedDevices = devices.filter(
    (d) => d.security_state === 'PROTECTED' || d.security_state === 'NORMAL'
  );

  // Find most recent device with coordinates for preview map
  const activeDeviceWithLocation = devices.find(
    (d) => d.last_known_latitude && d.last_known_longitude
  );

  return (
    <div className="space-y-6">
      {/* Header with Title and Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 uppercase tracking-wide">
            Fleet Overview
          </h1>
          <p className="text-xs text-slate-400">
            Real-time multi-dimensional security monitoring & control plane
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={fetchDevices}
            icon={<RefreshCw size={14} />}
          >
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsEnrollModalOpen(true)}
            icon={<Plus size={16} />}
          >
            Enroll New Device
          </Button>
        </div>
      </div>

      {/* Critical STOLEN Incident Alert Banner */}
      {stolenDevices.length > 0 && (
        <div className="p-4 bg-red-950/80 border-2 border-red-600 rounded-2xl shadow-xl shadow-red-950/60 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-pulse">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-red-600 text-white rounded-xl">
              <AlertTriangle size={24} />
            </div>
            <div>
              <div className="text-base font-black text-white uppercase tracking-wider">
                {stolenDevices.length} ACTIVE THEFT INCIDENT{stolenDevices.length > 1 ? 'S' : ''} IN PROGRESS
              </div>
              <div className="text-xs text-red-200">
                Stolen security protocol active. Escalated GPS tracking and evidence capture engaged.
              </div>
            </div>
          </div>
          <Link to="/stolen-center">
            <Button variant="danger" size="sm" className="whitespace-nowrap shadow-lg">
              Open STOLEN Recovery Center &rarr;
            </Button>
          </Link>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="flex items-center gap-4">
          <div className="p-3 bg-primary/10 border border-primary/20 rounded-xl text-primary">
            <Smartphone size={22} />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-100">{devices.length}</div>
            <div className="text-xs text-slate-400 font-semibold uppercase">Total Devices</div>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="p-3 bg-red-950/50 border border-red-800/80 rounded-xl text-red-400">
            <AlertTriangle size={22} />
          </div>
          <div>
            <div className="text-2xl font-black text-red-400">{stolenDevices.length}</div>
            <div className="text-xs text-slate-400 font-semibold uppercase">Stolen / Incidents</div>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="p-3 bg-emerald-950/50 border border-emerald-800/80 rounded-xl text-emerald-400">
            <Radio size={22} />
          </div>
          <div>
            <div className="text-2xl font-black text-emerald-400">{onlineDevices.length}</div>
            <div className="text-xs text-slate-400 font-semibold uppercase">Live Online</div>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="p-3 bg-sky-950/50 border border-sky-800/80 rounded-xl text-sky-400">
            <ShieldCheck size={22} />
          </div>
          <div>
            <div className="text-2xl font-black text-sky-400">{protectedDevices.length}</div>
            <div className="text-xs text-slate-400 font-semibold uppercase">Protected</div>
          </div>
        </Card>
      </div>

      {/* Fleet Map Preview & Device Grid */}
      {isLoading ? (
        <div className="py-20 flex justify-center">
          <Spinner size="lg" />
        </div>
      ) : devices.length === 0 ? (
        <Card className="text-center py-16 space-y-4">
          <div className="inline-flex p-4 rounded-full bg-slate-800 text-slate-400">
            <Smartphone size={36} />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-slate-200">No Devices Enrolled</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Get started by enrolling your first Android device into the Anti-Sarika security control plane.
            </p>
          </div>
          <Button
            variant="primary"
            onClick={() => setIsEnrollModalOpen(true)}
            icon={<Plus size={16} />}
          >
            Enroll Device Now
          </Button>
        </Card>
      ) : (
        <div className="space-y-6">
          {activeDeviceWithLocation && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-400 font-bold uppercase tracking-wider">
                <span>Fleet Live Location Map</span>
                <span className="text-primary">
                  Showing latest: {activeDeviceWithLocation.device_name}
                </span>
              </div>
              <LiveMap
                currentLocation={{
                  latitude: activeDeviceWithLocation.last_known_latitude!,
                  longitude: activeDeviceWithLocation.last_known_longitude!,
                  accuracy: activeDeviceWithLocation.last_known_accuracy,
                  recordedAt: activeDeviceWithLocation.last_known_location_at,
                  battery: activeDeviceWithLocation.battery_level,
                }}
                isStolen={activeDeviceWithLocation.security_state === 'STOLEN'}
                className="h-[320px]"
              />
            </div>
          )}

          <div className="space-y-3">
            <div className="text-xs text-slate-400 font-bold uppercase tracking-wider">
              Enrolled Devices Fleet ({devices.length})
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {devices.map((dev) => (
                <DeviceCard key={dev.id} device={dev} />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Enroll Modal */}
      <EnrollModal
        isOpen={isEnrollModalOpen}
        onClose={() => {
          setIsEnrollModalOpen(false);
          fetchDevices();
        }}
      />
    </div>
  );
};
