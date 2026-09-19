import React from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { EvidenceMetadata } from '../../types';
import { Badge } from '../common/Badge';
import { ShieldCheck, FileKey, Copy, Check, Clock, Database, Hash } from 'lucide-react';

interface EvidenceViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  evidence: EvidenceMetadata | null;
}

export const EvidenceViewerModal: React.FC<EvidenceViewerModalProps> = ({
  isOpen,
  onClose,
  evidence,
}) => {
  const [copiedHash, setCopiedHash] = React.useState(false);

  if (!evidence) return null;

  const copyHash = () => {
    navigator.clipboard.writeText(evidence.integrity_hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Forensic Evidence Record" maxWidth="lg">
      <div className="space-y-4 text-xs">
        {/* Integrity status banner */}
        <div className="p-3.5 bg-emerald-950/40 border border-emerald-800/80 rounded-xl flex items-start gap-3">
          <ShieldCheck size={22} className="text-emerald-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="font-bold text-sm text-emerald-400">Cryptographic Integrity Verified</div>
            <p className="text-slate-300">
              This evidence artifact was captured in STOLEN recovery mode, signed with the hardware-backed device key, and committed to the control plane.
            </p>
          </div>
        </div>

        {/* SHA-256 Hash Card */}
        <div className="p-3.5 bg-background border border-slate-800 rounded-xl space-y-1.5">
          <div className="flex justify-between items-center text-[11px] font-semibold text-slate-400 uppercase">
            <span className="flex items-center gap-1">
              <Hash size={13} className="text-primary" /> SHA-256 Integrity Hash
            </span>
            <button
              type="button"
              onClick={copyHash}
              className="text-primary hover:underline flex items-center gap-1 font-sans text-xs"
            >
              {copiedHash ? <Check size={13} /> : <Copy size={13} />}
              {copiedHash ? 'Copied' : 'Copy'}
            </button>
          </div>
          <div className="font-mono text-xs text-primary break-all bg-surface p-2.5 rounded-lg border border-slate-700/60">
            {evidence.integrity_hash}
          </div>
        </div>

        {/* Metadata Details Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="p-3 bg-surface border border-slate-800 rounded-xl space-y-1">
            <div className="text-slate-500 font-semibold text-[10px] uppercase">Evidence ID</div>
            <div className="font-mono text-slate-200 truncate">{evidence.id}</div>
          </div>
          <div className="p-3 bg-surface border border-slate-800 rounded-xl space-y-1">
            <div className="text-slate-500 font-semibold text-[10px] uppercase">Capture Type</div>
            <div>
              <Badge variant="purple">{evidence.capture_type}</Badge>
            </div>
          </div>
          <div className="p-3 bg-surface border border-slate-800 rounded-xl space-y-1">
            <div className="text-slate-500 font-semibold text-[10px] uppercase">Device Timestamp</div>
            <div className="font-mono text-slate-300">{new Date(evidence.device_timestamp).toLocaleString()}</div>
          </div>
          <div className="p-3 bg-surface border border-slate-800 rounded-xl space-y-1">
            <div className="text-slate-500 font-semibold text-[10px] uppercase">Received at Server</div>
            <div className="font-mono text-slate-300">{new Date(evidence.received_at).toLocaleString()}</div>
          </div>
        </div>

        {/* Storage & Chain of custody */}
        <div className="p-3.5 bg-surface border border-slate-800 rounded-xl space-y-2">
          <div className="flex items-center gap-1.5 font-bold text-slate-200">
            <FileKey size={14} className="text-amber-400" />
            <span>Chain-of-Custody & Storage Reference</span>
          </div>
          <div className="font-mono text-[11px] text-slate-400 break-all bg-background p-2 rounded border border-slate-800">
            {evidence.storage_ref}
          </div>
          {evidence.chain_of_custody_notes && (
            <p className="text-slate-300 italic pt-1 border-t border-slate-800">
              "{evidence.chain_of_custody_notes}"
            </p>
          )}
        </div>

        <div className="flex justify-end pt-3 border-t border-slate-800">
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
};
