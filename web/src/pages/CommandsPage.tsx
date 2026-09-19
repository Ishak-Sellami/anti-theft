import React, { useEffect, useState } from 'react';
import { deviceService } from '../services/devices';
import { commandService } from '../services/commands';
import { Device, DeviceCommand } from '../types';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Spinner } from '../components/common/Spinner';
import { CommandModal } from '../components/commands/CommandModal';
import { CommandHistoryTable } from '../components/commands/CommandHistoryTable';
import { Terminal, Plus, RefreshCw } from 'lucide-react';

export const CommandsPage: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [commands, setCommands] = useState<DeviceCommand[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadData = async () => {
    try {
      const devList = await deviceService.listDevices();
      setDevices(devList);
      const targetId = selectedDeviceId || (devList.length > 0 ? devList[0].id : '');
      setSelectedDeviceId(targetId);

      if (targetId) {
        const list = await commandService.getCommandHistory(targetId);
        setCommands(list);
      }
    } catch (e) {
      console.error('Failed to load commands', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedDeviceId]);

  const selectedDevice = devices.find((d) => d.id === selectedDeviceId);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 uppercase tracking-wide">
            Remote Commands Console
          </h1>
          <p className="text-xs text-slate-400">
            Issue cryptographically backend-signed remote instructions with execution verification
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

          {selectedDevice && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsModalOpen(true)}
              icon={<Plus size={16} />}
            >
              Issue Command
            </Button>
          )}
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
              <Terminal className="text-primary" size={18} />
              <span className="font-bold text-sm text-slate-200 uppercase tracking-wider">
                Command Execution Ledger ({commands.length})
              </span>
            </div>
            <span className="text-xs text-slate-500 font-mono">
              Signed by Master Backend Key • Verified by Device
            </span>
          </div>

          <CommandHistoryTable commands={commands} />
        </Card>
      )}

      {selectedDevice && (
        <CommandModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          deviceId={selectedDevice.id}
          deviceName={selectedDevice.device_name}
          onSuccess={loadData}
        />
      )}
    </div>
  );
};
