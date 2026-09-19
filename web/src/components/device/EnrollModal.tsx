import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { deviceService } from '../../services/devices';
import { EnrollmentInitiateResponse } from '../../types';
import { QrCode, Copy, Check, ShieldCheck, Key } from 'lucide-react';

interface EnrollModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const EnrollModal: React.FC<EnrollModalProps> = ({ isOpen, onClose }) => {
  const [deviceName, setDeviceName] = useState('');
  const [deviceModel, setDeviceModel] = useState('Android Device');
  const [osVersion, setOsVersion] = useState('Android 14 (API 34)');
  const [isLoading, setIsLoading] = useState(false);
  const [enrollData, setEnrollData] = useState<EnrollmentInitiateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copiedToken, setCopiedToken] = useState(false);
  const [copiedKey, setCopiedKey] = useState(false);

  const handleInitiate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deviceName.trim()) return;

    setIsLoading(true);
    setError(null);
    try {
      const res = await deviceService.initiateEnrollment({
        device_name: deviceName.trim(),
        device_model: deviceModel.trim(),
        os_version: osVersion.trim(),
      });
      setEnrollData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to initiate device enrollment');
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text: string, isToken: boolean) => {
    navigator.clipboard.writeText(text);
    if (isToken) {
      setCopiedToken(true);
      setTimeout(() => setCopiedToken(false), 2000);
    } else {
      setCopiedKey(true);
      setTimeout(() => setCopiedKey(false), 2000);
    }
  };

  const resetAndClose = () => {
    setEnrollData(null);
    setDeviceName('');
    setError(null);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={resetAndClose} title="Enroll New Device" maxWidth="lg">
      {!enrollData ? (
        <form onSubmit={handleInitiate} className="space-y-4">
          <p className="text-sm text-slate-300">
            Generate an asymmetric pairing session token for your Anti-Sarika Android Agent.
          </p>

          {error && (
            <div className="p-3 text-xs bg-red-950/60 border border-red-800 text-red-300 rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
              Device Display Name *
            </label>
            <input
              type="text"
              required
              value={deviceName}
              onChange={(e) => setDeviceName(e.target.value)}
              placeholder="e.g. My Pixel 8 Pro"
              className="w-full px-3 py-2 bg-background border border-slate-700 rounded-lg text-slate-100 text-sm focus:outline-none focus:border-primary"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Device Model
              </label>
              <input
                type="text"
                value={deviceModel}
                onChange={(e) => setDeviceModel(e.target.value)}
                className="w-full px-3 py-2 bg-background border border-slate-700 rounded-lg text-slate-100 text-sm focus:outline-none focus:border-primary"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                OS Version
              </label>
              <input
                type="text"
                value={osVersion}
                onChange={(e) => setOsVersion(e.target.value)}
                className="w-full px-3 py-2 bg-background border border-slate-700 rounded-lg text-slate-100 text-sm focus:outline-none focus:border-primary"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="ghost" type="button" onClick={resetAndClose}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" isLoading={isLoading}>
              Generate Pairing Token
            </Button>
          </div>
        </form>
      ) : (
        <div className="space-y-5">
          <div className="p-4 bg-emerald-950/30 border border-emerald-800/60 rounded-xl flex items-start gap-3">
            <ShieldCheck className="text-emerald-400 shrink-0 mt-0.5" size={20} />
            <div className="text-xs text-slate-300 space-y-1">
              <div className="font-bold text-emerald-400 text-sm">Pairing Session Active</div>
              <div>Enter this token in the Android app to complete cryptographic device registration.</div>
            </div>
          </div>

          {/* Token Box */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-xs font-semibold text-slate-300">
              <span>ENROLLMENT TOKEN (Expires in 15 mins)</span>
              <button
                type="button"
                onClick={() => copyToClipboard(enrollData.enrollment_token, true)}
                className="flex items-center gap-1 text-primary hover:underline text-xs"
              >
                {copiedToken ? <Check size={13} /> : <Copy size={13} />}
                {copiedToken ? 'Copied!' : 'Copy Token'}
              </button>
            </div>
            <div className="p-3 bg-background border border-slate-800 rounded-lg font-mono text-xs text-primary break-all">
              {enrollData.enrollment_token}
            </div>
          </div>

          {/* Backend Public Key PEM */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-xs font-semibold text-slate-300">
              <span>BACKEND MASTER PUBLIC KEY PEM</span>
              <button
                type="button"
                onClick={() => copyToClipboard(enrollData.backend_public_key_pem, false)}
                className="flex items-center gap-1 text-primary hover:underline text-xs"
              >
                {copiedKey ? <Check size={13} /> : <Copy size={13} />}
                {copiedKey ? 'Copied!' : 'Copy PEM'}
              </button>
            </div>
            <textarea
              readOnly
              rows={4}
              value={enrollData.backend_public_key_pem}
              className="w-full p-2.5 bg-background border border-slate-800 rounded-lg font-mono text-[11px] text-slate-400 select-all"
            />
          </div>

          <div className="flex justify-end pt-3 border-t border-slate-800">
            <Button variant="secondary" onClick={resetAndClose}>
              Done
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
};
