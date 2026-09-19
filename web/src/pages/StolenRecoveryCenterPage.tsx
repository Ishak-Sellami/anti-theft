import React, { useEffect, useState, useCallback } from 'react';
import { deviceService } from '../services/devices';
import { telemetryService } from '../services/telemetry';
import { evidenceService } from '../services/evidence';
import { commandService } from '../services/commands';
import { Device, LocationTelemetry, EvidenceMetadata } from '../types';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Spinner } from '../components/common/Spinner';
import { StateBadge } from '../components/device/StateBadge';
import { BatteryIndicator } from '../components/device/BatteryIndicator';
import { LiveMap } from '../components/map/LiveMap';
import { CommandModal } from '../components/commands/CommandModal';
import { EvidenceViewerModal } from '../components/evidence/EvidenceViewerModal';
import { useWebSocket } from '../context/WebSocketContext';
import {
  AlertTriangle,
  ShieldAlert,
  Radio,
  Lock,
  Volume2,
  RefreshCw,
  FileKey,
  ShieldCheck,
  Zap,
} from 'lucide-react';

export const StolenRecoveryCenterPage: React.FC = () => {
  const [stolenDevices, setStolenDevices] = useState<Device[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [telemetry, setTelemetry] = useState<LocationTelemetry[]>([]);
  const [evidence, setEvidence] = useState<EvidenceMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCommandModalOpen, setIsCommandModalOpen] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceMetadata | null>(null);
  const { subscribe } = useWebSocket();

  const loadStolenFleet = useCallback(async () => {
    try {
      const all = await deviceService.listDevices();
      const stolen = all.filter((d) => d.security_state === 'STOLEN');
      setStolenDevices(stolen);

      if (stolen.length > 0) {
        // Select first stolen device or keep selected
        const currentId = selectedDevice?.id || stolen[0].id;
        const target = stolen.find((d) => d.id === currentId) || stolen[0];
        setSelectedDevice(target);

        const [telem, evd] = await Promise.all([
          telemetryService.getTelemetryHistory(target.id, 50).catch(() => []),
          evidenceService.getDeviceEvidence(target.id).catch(() => []),
        ]);
        setTelemetry(telem);
        setEvidence(evd);
      } else {
        setSelectedDevice(null);
        setTelemetry([]);
        setEvidence([]);
      }
    } catch (e) {
      console.error('Failed to load stolen recovery center', e);
    } finally {
      setIsLoading(false);
    }
  }, [selectedDevice?.id]);

  useEffect(() => {
    loadStolenFleet();

    const unsubscribe = subscribe((msg) => {
      if (
        msg.event_type === 'DEVICE_STATE_CHANGED' ||
        msg.event_type === 'TELEMETRY_INGESTED' ||
        msg.event_type === 'SECURITY_EVENT_CREATED' ||
        msg.event_type === 'EVIDENCE_RECORDED'
      ) {
        loadStolenFleet();
      }
    });

    return () => unsubscribe();
  }, [loadStolenFleet, subscribe]);

  const handleQuickCommand = async (type: any) => {
    if (!selectedDevice) return;
    try {
      await commandService.issueCommand(selectedDevice.id, type, {}, 300);
      loadStolenFleet();
    } catch (e) {
      console.error('Quick command failed', e);
    }
  };

  if (isLoading) {
    return (
      <div className="py-24 flex justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (stolenDevices.length === 0) {
    return (
      <Card className="text-center py-20 space-y-4 border-emerald-800/40 bg-emerald-950/10">
        <div className="inline-flex p-4 rounded-2xl bg-emerald-950/60 border border-emerald-800/80 text-emerald-400">
          <ShieldCheck size={40} />
        </div>
        <div className="space-y-1">
          <h2 className="text-xl font-black text-slate-100 uppercase tracking-wide">
            All Devices Secure
          </h2>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            No active theft incidents detected. If a device is stolen, unauthorized power-off, or wiped, it will automatically escalate here.
          </p>
        </div>
      </Card>
    );
  }

  const latestLoc = telemetry.length > 0 ? telemetry[0] : null;

  return (
    <div className="space-y-6">
      {/* Incident Header */}
      <div className="p-4 bg-red-950/90 border-2 border-red-600 rounded-2xl shadow-2xl shadow-red-950/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="p-3 bg-red-600 text-white rounded-xl shadow-lg animate-bounce">
            <ShieldAlert size={28} />
          </div>
          <div>
            <div className="text-lg font-black text-white uppercase tracking-wider flex items-center gap-2">
              <span>ACTIVE THEFT RECOVERY CENTER</span>
              <span className="text-xs px-2 py-0.5 bg-red-800 rounded-full font-mono">
                {stolenDevices.length} ACTIVE INCIDENT{stolenDevices.length > 1 ? 'S' : ''}
              </span>
            </div>
            <p className="text-xs text-red-200">
              Escalated recovery protocols active. Live telemetry and chain-of-custody evidence recording in real-time.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {stolenDevices.map((d) => (
            <button
              key={d.id}
              onClick={() => setSelectedDevice(d)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                selectedDevice?.id === d.id
                  ? 'bg-white text-red-950 shadow-md font-black'
                  : 'bg-red-900/60 text-white hover:bg-red-800'
              }`}
            >
              {d.device_name}
            </button>
          ))}
        </div>
      </div>

      {selectedDevice && (
        <>
          {/* Quick Action Emergency Toolbar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Button
              variant="secondary"
              onClick={() => handleQuickCommand('REQUEST_SNAPSHOT')}
              icon={<RefreshCw size={15} />}
              className="py-3 text-xs"
            >
              Ping GPS Now
            </Button>

            <Button
              variant="warning"
              onClick={() => handleQuickCommand('TRIGGER_ALARM')}
              icon={<Volume2 size={15} />}
              className="py-3 text-xs"
            >
              Sound Siren
            </Button>

            <Button
              variant="secondary"
              onClick={() => handleQuickCommand('LOCK_DEVICE')}
              icon={<Lock size={15} />}
              className="py-3 text-xs"
            >
              Force Lock DPC
            </Button>

            <Button
              variant="danger"
              onClick={() => setIsCommandModalOpen(true)}
              icon={<ShieldAlert size={15} />}
              className="py-3 text-xs"
            >
              Emergency Command
            </Button>
          </div>

          {/* Map and Telemetry Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-3">
              <div className="flex items-center justify-between text-xs text-red-400 font-bold uppercase tracking-wider">
                <span>Real-Time Pursuit Map</span>
                <span className="font-mono text-slate-300">
                  {latestLoc
                    ? `GPS: ${latestLoc.latitude.toFixed(5)}, ${latestLoc.longitude.toFixed(5)}`
                    : 'Awaiting fix'}
                </span>
              </div>
              <LiveMap
                currentLocation={
                  latestLoc
                    ? {
                        latitude: latestLoc.latitude,
                        longitude: latestLoc.longitude,
                        accuracy: latestLoc.accuracy,
                        recordedAt: latestLoc.recorded_at,
                        battery: latestLoc.battery_level,
                      }
                    : null
                }
                history={telemetry}
                isStolen={true}
                className="h-[420px]"
              />
            </div>

            {/* Incident Summary Card */}
            <div className="space-y-4">
              <Card className="space-y-4 border-red-900/60 bg-surface">
                <div className="text-xs font-bold text-slate-200 uppercase tracking-wider border-b border-slate-800 pb-2">
                  Target Device Profile
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Device Name:</span>
                    <span className="font-bold text-slate-100">{selectedDevice.device_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Model:</span>
                    <span className="text-slate-200">{selectedDevice.device_model || 'Android'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Battery Level:</span>
                    <BatteryIndicator level={selectedDevice.battery_level} isCharging={selectedDevice.is_charging} />
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Connectivity:</span>
                    <StateBadge type="connectivity" value={selectedDevice.connectivity_state} />
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Fingerprint:</span>
                    <span className="font-mono text-primary truncate max-w-[120px]">
                      {selectedDevice.public_key_fingerprint.slice(0, 12)}...
                    </span>
                  </div>
                </div>
              </Card>

              {/* Forensic Evidence Feed */}
              <Card className="space-y-3 border-slate-800">
                <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                  <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                    Captured Evidence ({evidence.length})
                  </span>
                </div>

                {evidence.length === 0 ? (
                  <div className="text-center py-6 text-slate-500 text-xs">
                    Background forensic evidence sweep in progress...
                  </div>
                ) : (
                  <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
                    {evidence.map((ev) => (
                      <div
                        key={ev.id}
                        onClick={() => setSelectedEvidence(ev)}
                        className="p-2.5 bg-background border border-slate-800 rounded-lg hover:border-slate-700 cursor-pointer flex items-center justify-between text-xs transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <FileKey size={14} className="text-primary shrink-0" />
                          <div>
                            <div className="font-bold text-slate-200">{ev.capture_type}</div>
                            <div className="text-[10px] text-slate-500 font-mono">
                              {new Date(ev.device_timestamp).toLocaleTimeString()}
                            </div>
                          </div>
                        </div>
                        <span className="text-[10px] font-mono text-emerald-400">
                          {ev.integrity_hash.slice(0, 8)}...
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>
          </div>
        </>
      )}

      {/* Command Modal */}
      {selectedDevice && (
        <CommandModal
          isOpen={isCommandModalOpen}
          onClose={() => setIsCommandModalOpen(false)}
          deviceId={selectedDevice.id}
          deviceName={selectedDevice.device_name}
          onSuccess={loadStolenFleet}
        />
      )}

      {/* Evidence Viewer */}
      <EvidenceViewerModal
        isOpen={!!selectedEvidence}
        onClose={() => setSelectedEvidence(null)}
        evidence={selectedEvidence}
      />
    </div>
  );
};
