import React, { useEffect, useState } from 'react';
import { deviceService } from '../services/devices';
import { evidenceService } from '../services/evidence';
import { Device, EvidenceMetadata } from '../types';
import { Card } from '../components/common/Card';
import { Spinner } from '../components/common/Spinner';
import { EvidenceTable } from '../components/evidence/EvidenceTable';
import { EvidenceViewerModal } from '../components/evidence/EvidenceViewerModal';
import { FileKey, ShieldCheck, RefreshCw } from 'lucide-react';
import { Button } from '../components/common/Button';

export const EvidenceCenterPage: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [evidenceList, setEvidenceList] = useState<EvidenceMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceMetadata | null>(null);

  const loadData = async () => {
    try {
      const devList = await deviceService.listDevices();
      setDevices(devList);
      const targetId = selectedDeviceId || (devList.length > 0 ? devList[0].id : '');
      setSelectedDeviceId(targetId);

      if (targetId) {
        const evd = await evidenceService.getDeviceEvidence(targetId);
        setEvidenceList(evd);
      }
    } catch (e) {
      console.error('Failed to load evidence', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedDeviceId]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 uppercase tracking-wide">
            Forensic Evidence Vault
          </h1>
          <p className="text-xs text-slate-400">
            Owner-authorized, cryptographically verified chain-of-custody artifacts
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
          <Button variant="secondary" size="sm" onClick={loadData} icon={<RefreshCw size={14} />}>
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
              <ShieldCheck className="text-emerald-400" size={18} />
              <span className="font-bold text-sm text-slate-200 uppercase tracking-wider">
                Legal Chain of Custody Records ({evidenceList.length})
              </span>
            </div>
            <span className="text-xs text-slate-500 font-mono">
              Access strictly isolated to verified device owner
            </span>
          </div>

          <EvidenceTable
            evidenceList={evidenceList}
            onSelectEvidence={(ev) => setSelectedEvidence(ev)}
          />
        </Card>
      )}

      {/* Evidence Inspector Modal */}
      <EvidenceViewerModal
        isOpen={!!selectedEvidence}
        onClose={() => setSelectedEvidence(null)}
        evidence={selectedEvidence}
      />
    </div>
  );
};
