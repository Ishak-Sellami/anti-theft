import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { commandService } from '../../services/commands';
import { CommandType, SecurityState } from '../../types';
import { Terminal, AlertTriangle, ShieldCheck, Lock, Volume2, VolumeX, RefreshCw, Trash2 } from 'lucide-react';

interface CommandModalProps {
  isOpen: boolean;
  onClose: () => void;
  deviceId: string;
  deviceName: string;
  onSuccess: () => void;
}

export const CommandModal: React.FC<CommandModalProps> = ({
  isOpen,
  onClose,
  deviceId,
  deviceName,
  onSuccess,
}) => {
  const [commandType, setCommandType] = useState<CommandType>('REQUEST_SNAPSHOT');
  const [targetSecurityState, setTargetSecurityState] = useState<SecurityState>('STOLEN');
  const [ttlSeconds, setTtlSeconds] = useState<number>(300);
  const [confirmWipe, setConfirmWipe] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isDestructive = commandType === 'AUTHORIZE_WIPE';
  const isSecurityShift = commandType === 'SET_SECURITY_STATE';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isDestructive && confirmWipe !== 'CONFIRM WIPE') {
      setError('You must type CONFIRM WIPE exactly to authorize a remote factory wipe.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const payload: Record<string, any> = {};
      if (isSecurityShift) {
        payload['target_security_state'] = targetSecurityState;
      }

      await commandService.issueCommand(deviceId, commandType, payload, ttlSeconds);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to dispatch command');
    } finally {
      setIsLoading(false);
    }
  };

  const commandOptions: { type: CommandType; label: string; desc: string; icon: any; danger?: boolean }[] = [
    {
      type: 'REQUEST_SNAPSHOT',
      label: 'Request Immediate Telemetry',
      desc: 'Instructs agent to immediately capture and forward high-accuracy GPS & battery snapshot.',
      icon: RefreshCw,
    },
    {
      type: 'SET_SECURITY_STATE',
      label: 'Shift Security State',
      desc: 'Manually transition device state between NORMAL, PROTECTED, STOLEN, or RECOVERY.',
      icon: ShieldCheck,
    },
    {
      type: 'LOCK_DEVICE',
      label: 'Remote Lock Screen',
      desc: 'Invokes DPC lockNow() to immediately lock device screen and require PIN/biometrics.',
      icon: Lock,
    },
    {
      type: 'TRIGGER_ALARM',
      label: 'Trigger Siren Alarm',
      desc: 'Sounds maximum-volume audible alarm tone to assist immediate physical recovery.',
      icon: Volume2,
    },
    {
      type: 'STOP_ALARM',
      label: 'Stop Siren Alarm',
      desc: 'Silences any active recovery audio alarm.',
      icon: VolumeX,
    },
    {
      type: 'AUTHORIZE_WIPE',
      label: 'Authorize Remote Wipe (DPC)',
      desc: 'Erases all user data via Device Policy Manager wipeData(0). IRREVERSIBLE.',
      icon: Trash2,
      danger: true,
    },
  ];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Issue Remote Command — ${deviceName}`} maxWidth="lg">
      <form onSubmit={handleSubmit} className="space-y-5">
        {error && (
          <div className="p-3 bg-red-950/60 border border-red-800 text-red-300 text-xs rounded-xl flex items-start gap-2">
            <AlertTriangle size={16} className="shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <div className="space-y-2">
          <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider">
            Select Command
          </label>
          <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
            {commandOptions.map((opt) => {
              const Icon = opt.icon;
              const isSelected = commandType === opt.type;
              return (
                <div
                  key={opt.type}
                  onClick={() => setCommandType(opt.type)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all flex items-start gap-3 ${
                    isSelected
                      ? opt.danger
                        ? 'bg-red-950/40 border-red-600 text-red-200'
                        : 'bg-primary/10 border-primary text-primary'
                      : 'bg-background border-slate-800 hover:border-slate-700 text-slate-300'
                  }`}
                >
                  <Icon size={18} className="shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <div className="text-sm font-bold">{opt.label}</div>
                    <div className="text-xs text-slate-400 mt-0.5">{opt.desc}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {isSecurityShift && (
          <div className="p-3.5 bg-background border border-slate-800 rounded-xl space-y-2">
            <label className="block text-xs font-semibold text-slate-300 uppercase">
              Target Security State
            </label>
            <select
              value={targetSecurityState}
              onChange={(e) => setTargetSecurityState(e.target.value as SecurityState)}
              className="w-full px-3 py-2 bg-surface border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-primary"
            >
              <option value="NORMAL">NORMAL (Standard operation)</option>
              <option value="PROTECTED">PROTECTED (Enhanced defense)</option>
              <option value="STOLEN">STOLEN (Escalated tracking & forensic evidence)</option>
              <option value="RECOVERY">RECOVERY (Post-theft device reclamation)</option>
            </select>
          </div>
        )}

        {isDestructive && (
          <div className="p-4 bg-red-950/40 border border-red-700/80 rounded-xl space-y-3">
            <div className="flex items-center gap-2 text-red-400 font-bold text-sm">
              <AlertTriangle size={18} /> DESTRUCTIVE ACTION WARNING
            </div>
            <p className="text-xs text-red-200">
              This will execute a factory reset wipe through the Device Policy Controller. All photos, apps, and credentials will be deleted.
            </p>
            <div>
              <label className="block text-xs font-mono text-slate-300 mb-1">
                Type <span className="text-red-400 font-bold">CONFIRM WIPE</span> below to authorize:
              </label>
              <input
                type="text"
                value={confirmWipe}
                onChange={(e) => setConfirmWipe(e.target.value)}
                placeholder="CONFIRM WIPE"
                className="w-full px-3 py-2 bg-background border border-red-800 rounded-lg text-sm text-white font-mono focus:outline-none focus:border-red-500"
              />
            </div>
          </div>
        )}

        <div className="flex items-center justify-between pt-3 border-t border-slate-800">
          <div className="text-xs text-slate-500">
            TTL: {ttlSeconds}s • Signed by Control Plane
          </div>
          <div className="flex gap-3">
            <Button variant="ghost" type="button" onClick={onClose}>
              Cancel
            </Button>
            <Button
              variant={isDestructive ? 'danger' : 'primary'}
              type="submit"
              isLoading={isLoading}
            >
              {isDestructive ? 'Authorize Wipe' : 'Dispatch Command'}
            </Button>
          </div>
        </div>
      </form>
    </Modal>
  );
};
