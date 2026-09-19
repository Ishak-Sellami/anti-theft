import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { deviceService } from '../services/devices';
import { telemetryService } from '../services/telemetry';
import { commandService } from '../services/commands';
import { eventService } from '../services/events';
import { evidenceService } from '../services/evidence';
import {
  Device,
  LocationTelemetry,
  DeviceCommand,
  SecurityEvent,
  EvidenceMetadata,
} from '../types';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Spinner } from '../components/common/Spinner';
import { StateBadge } from '../components/device/StateBadge';
import { BatteryIndicator } from '../components/device/BatteryIndicator';
import { LiveMap } from '../components/map/LiveMap';
import { CommandModal } from '../components/commands/CommandModal';
import { CommandHistoryTable } from '../components/commands/CommandHistoryTable';
import { EvidenceTable } from '../components/evidence/EvidenceTable';
import { EvidenceViewerModal } from '../components/evidence/EvidenceViewerModal';
import { useWebSocket } from '../context/WebSocketContext';
import {
  Smartphone,
  MapPin,
  Clock,
  Terminal,
  FileKey,
  Activity,
  Shield,
  RefreshCw,
  AlertTriangle,
  ArrowLeft,
} from 'lucide-react';

export const DeviceDetailPage: React.FC = () => {
  const { deviceId } = useParams<{ deviceId: string }>();
  const navigate = useNavigate();
  const { subscribe } = useWebSocket();

  const [device, setDevice] = useState<Device | null>(null);
  const [telemetry, setTelemetry] = useState<LocationTelemetry[]>([]);
  const [commands, setCommands] = useState<DeviceCommand[]>([]);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [evidence, setEvidence] = useState<EvidenceMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const [activeTab, setActiveTab] = useState<'map' | 'commands' | 'events' | 'evidence'>('map');
  const [isCommandModalOpen, setIsCommandModalOpen] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceMetadata | null>(null);

  const loadData = useCallback(async () => {
    if (!deviceId) return;
    try {
      const [dev, telem, cmds, evts, evd] = await Promise.all([
        deviceService.getDevice(deviceId),
        telemetryService.getTelemetryHistory(deviceId, 50).catch(() => []),
        commandService.getCommandHistory(deviceId).catch(() => []),
        eventService.getDeviceSecurityEvents(deviceId, 50).catch(() => []),
        evidenceService.getDeviceEvidence(deviceId).catch(() => []),
      ]);

      setDevice(dev);
      setTelemetry(telem);
      setCommands(cmds);
      setEvents(evts);
      setEvidence(evd);
    } catch (e) {
      console.error('Error loading device details', e);
    } finally {
      setIsLoading(false);
    }
  }, [deviceId]);

  useEffect(() => {
    loadData();

    // Subscribe to live WebSocket events for this device
    const unsubscribe = subscribe((msg) => {
      if (msg.device_id === deviceId || msg.data?.device_id === deviceId) {
        loadData();
      }
    });

    return () => unsubscribe();
  }, [deviceId, loadData, subscribe]);

  if (isLoading) {
    return (
      <div className="py-24 flex justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!device) {
    return (
      <Card className="text-center py-16 space-y-4">
        <div className="text-red-400 font-bold text-lg">Device Not Found</div>
        <p className="text-xs text-slate-400">
          The requested device does not exist or you do not have permission to view it.
        </p>
        <Button variant="secondary" onClick={() => navigate('/devices')}>
          Back to Devices Fleet
        </Button>
      </Card>
    );
  }

  const isStolen = device.security_state === 'STOLEN';
  const latestLoc = telemetry.length > 0 ? telemetry[0] : null;

  return (
    <div className="space-y-6">
      {/* Back button and title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/devices')}
            className="p-2 bg-surfaceHover text-slate-300 hover:text-white rounded-xl border border-slate-700 transition-colors"
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-black text-slate-100">{device.device_name}</h1>
              <StateBadge type="security" value={device.security_state} size="md" />
            </div>
            <p className="text-xs text-slate-400 font-mono">
              ID: {device.id} • {device.device_model || 'Android'} ({device.os_version || 'API 34'})
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="secondary"
            size="sm"
            onClick={loadData}
            icon={<RefreshCw size={14} />}
          >
            Sync
          </Button>
          <Button
            variant={isStolen ? 'danger' : 'primary'}
            size="sm"
            onClick={() => setIsCommandModalOpen(true)}
            icon={<Terminal size={15} />}
          >
            Remote Command
          </Button>
        </div>
      </div>

      {/* Critical STOLEN mode banner */}
      {isStolen && (
        <div className="p-4 bg-red-950/80 border-2 border-red-600 rounded-2xl flex items-center justify-between gap-4 animate-pulse">
          <div className="flex items-center gap-3">
            <AlertTriangle className="text-red-400" size={24} />
            <div>
              <div className="text-sm font-black text-white uppercase">STOLEN SECURITY STATE ACTIVE</div>
              <div className="text-xs text-red-200">
                Agent is running escalated tracking and background forensic evidence collection.
              </div>
            </div>
          </div>
          <Button
            variant="danger"
            size="sm"
            onClick={() => setIsCommandModalOpen(true)}
          >
            Emergency Controls
          </Button>
        </div>
      )}

      {/* 3D State & Hardware Info Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="space-y-2">
          <div className="text-[11px] font-bold text-slate-400 uppercase">3D Multi-State Model</div>
          <div className="flex flex-wrap gap-2 pt-1">
            <StateBadge type="security" value={device.security_state} />
            <StateBadge type="connectivity" value={device.connectivity_state} />
            <StateBadge type="power" value={device.power_state} />
          </div>
        </Card>

        <Card className="space-y-2">
          <div className="text-[11px] font-bold text-slate-400 uppercase">Power & Battery Status</div>
          <div className="flex items-center justify-between pt-1">
            <BatteryIndicator level={device.battery_level} isCharging={device.is_charging} />
            <span className="text-xs text-slate-400">
              {device.is_charging ? 'Charging (AC)' : 'Discharging'}
            </span>
          </div>
        </Card>

        <Card className="space-y-2">
          <div className="text-[11px] font-bold text-slate-400 uppercase">Cryptographic Identity</div>
          <div className="text-[11px] font-mono text-primary truncate" title={device.public_key_fingerprint}>
            FP: {device.public_key_fingerprint}
          </div>
          <div className="text-[10px] text-slate-500">ECDSA SecP256r1 • Hardware TEE Backed</div>
        </Card>
      </div>

      {/* Tabs Bar */}
      <div className="flex border-b border-slate-800 space-x-2">
        <button
          onClick={() => setActiveTab('map')}
          className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'map'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <MapPin size={15} /> Live Map & Telemetry ({telemetry.length})
        </button>

        <button
          onClick={() => setActiveTab('commands')}
          className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'commands'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Terminal size={15} /> Remote Commands ({commands.length})
        </button>

        <button
          onClick={() => setActiveTab('evidence')}
          className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'evidence'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileKey size={15} /> Evidence Vault ({evidence.length})
        </button>

        <button
          onClick={() => setActiveTab('events')}
          className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'events'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Activity size={15} /> Security Events ({events.length})
        </button>
      </div>

      {/* Tab Contents */}
      {activeTab === 'map' && (
        <div className="space-y-4">
          <LiveMap
            currentLocation={
              latestLoc
                ? {
                    latitude: latestLoc.latitude,
                    longitude: latestLoc.longitude,
                    accuracy: latestLoc.accuracy,
                    recordedAt: latestLoc.recordedAt || latestLoc.recorded_at,
                    battery: latestLoc.battery_level,
                  }
                : device.last_known_latitude && device.last_known_longitude
                ? {
                    latitude: device.last_known_latitude,
                    longitude: device.last_known_longitude,
                    accuracy: device.last_known_accuracy,
                    recordedAt: device.last_known_location_at,
                    battery: device.battery_level,
                  }
                : null
            }
            history={telemetry}
            isStolen={isStolen}
            className="h-[450px]"
          />

          {/* Telemetry Log Feed */}
          <Card className="space-y-3">
            <h3 className="font-bold text-sm text-slate-200 uppercase tracking-wider">
              Chronological Telemetry Stream
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="text-[11px] uppercase bg-surfaceHover/60 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="px-3 py-2">Recorded At (Device Time)</th>
                    <th className="px-3 py-2">Coordinates</th>
                    <th className="px-3 py-2">Accuracy</th>
                    <th className="px-3 py-2">Battery / Power</th>
                    <th className="px-3 py-2">Connectivity</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {telemetry.map((t) => (
                    <tr key={t.id} className="hover:bg-surfaceHover/30">
                      <td className="px-3 py-2 font-sans text-slate-400">
                        {new Date(t.recorded_at).toLocaleString()}
                      </td>
                      <td className="px-3 py-2 font-bold text-slate-200">
                        {t.latitude.toFixed(5)}, {t.longitude.toFixed(5)}
                      </td>
                      <td className="px-3 py-2 text-slate-400">±{t.accuracy?.toFixed(1) || '?'}m</td>
                      <td className="px-3 py-2">
                        <BatteryIndicator level={t.battery_level} />
                      </td>
                      <td className="px-3 py-2">
                        <StateBadge type="connectivity" value={t.connectivity_state || 'ONLINE'} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'commands' && (
        <Card className="p-0 overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-surfaceHover/30">
            <h3 className="font-bold text-sm text-slate-200 uppercase tracking-wider">
              Issued Remote Commands & Execution Receipts
            </h3>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsCommandModalOpen(true)}
              icon={<Terminal size={14} />}
            >
              Issue Command
            </Button>
          </div>
          <CommandHistoryTable commands={commands} />
        </Card>
      )}

      {activeTab === 'evidence' && (
        <Card className="p-0 overflow-hidden">
          <div className="p-4 border-b border-slate-800 bg-surfaceHover/30">
            <h3 className="font-bold text-sm text-slate-200 uppercase tracking-wider">
              Forensic Evidence Vault (Chain of Custody)
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Cryptographically verified incident snapshots and ambient RF beacons signed by the device.
            </p>
          </div>
          <EvidenceTable
            evidenceList={evidence}
            onSelectEvidence={(ev) => setSelectedEvidence(ev)}
          />
        </Card>
      )}

      {activeTab === 'events' && (
        <Card className="p-0 overflow-hidden">
          <div className="p-4 border-b border-slate-800 bg-surfaceHover/30">
            <h3 className="font-bold text-sm text-slate-200 uppercase tracking-wider">
              Immutable Security Events
            </h3>
          </div>
          <div className="divide-y divide-slate-800/60">
            {events.length === 0 ? (
              <div className="text-center py-10 text-slate-500 text-sm">
                No security alerts or tamper events recorded.
              </div>
            ) : (
              events.map((evt) => (
                <div key={evt.id} className="p-4 hover:bg-surfaceHover/20 transition-colors flex items-start gap-4">
                  <div className="p-2 rounded-xl bg-red-950/60 border border-red-800/60 text-red-400 mt-0.5">
                    <Activity size={18} />
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="font-bold text-sm text-slate-100">{evt.event_type}</div>
                      <span className="text-xs text-slate-500 font-mono">
                        {new Date(evt.device_timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400">
                      Severity: <span className="font-bold text-red-400">{evt.severity}</span> • State Transition: {evt.security_state_before} &rarr; {evt.security_state_after}
                    </div>
                    {evt.payload && (
                      <div className="font-mono text-[11px] bg-background p-2 rounded border border-slate-800 text-slate-300">
                        {JSON.stringify(evt.payload)}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      )}

      {/* Command Modal */}
      <CommandModal
        isOpen={isCommandModalOpen}
        onClose={() => setIsCommandModalOpen(false)}
        deviceId={device.id}
        deviceName={device.device_name}
        onSuccess={loadData}
      />

      {/* Evidence Viewer Modal */}
      <EvidenceViewerModal
        isOpen={!!selectedEvidence}
        onClose={() => setSelectedEvidence(null)}
        evidence={selectedEvidence}
      />
    </div>
  );
};
