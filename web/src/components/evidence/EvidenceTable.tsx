import React from 'react';
import { EvidenceMetadata } from '../../types';
import { Badge } from '../common/Badge';
import { FileKey, ShieldCheck, Eye } from 'lucide-react';

interface EvidenceTableProps {
  evidenceList: EvidenceMetadata[];
  onSelectEvidence: (evidence: EvidenceMetadata) => void;
}

export const EvidenceTable: React.FC<EvidenceTableProps> = ({
  evidenceList,
  onSelectEvidence,
}) => {
  if (evidenceList.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500 text-sm">
        No forensic evidence artifacts captured yet. Evidence capture activates in STOLEN/RECOVERY modes.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs text-slate-300">
        <thead className="text-[11px] uppercase bg-surfaceHover/60 text-slate-400 border-b border-slate-800">
          <tr>
            <th className="px-4 py-3">Capture Type</th>
            <th className="px-4 py-3">Captured At</th>
            <th className="px-4 py-3">Integrity (SHA-256)</th>
            <th className="px-4 py-3">Size / Format</th>
            <th className="px-4 py-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60 font-mono">
          {evidenceList.map((ev) => (
            <tr key={ev.id} className="hover:bg-surfaceHover/30 transition-colors">
              <td className="px-4 py-3 font-sans font-semibold text-slate-200">
                <div className="flex items-center gap-2">
                  <FileKey size={15} className="text-primary shrink-0" />
                  <Badge variant="purple">{ev.capture_type}</Badge>
                </div>
              </td>
              <td className="px-4 py-3 font-sans text-slate-300">
                {new Date(ev.device_timestamp).toLocaleString()}
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-1.5 font-mono text-emerald-400">
                  <ShieldCheck size={13} className="text-emerald-500 shrink-0" />
                  <span className="truncate max-w-[180px]" title={ev.integrity_hash}>
                    {ev.integrity_hash.slice(0, 16)}...
                  </span>
                </div>
              </td>
              <td className="px-4 py-3 text-slate-400 font-sans">
                {ev.mime_type} {ev.file_size_bytes ? `(${ev.file_size_bytes} B)` : ''}
              </td>
              <td className="px-4 py-3 text-right font-sans">
                <button
                  onClick={() => onSelectEvidence(ev)}
                  className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-primary bg-primary/10 hover:bg-primary/20 rounded-lg border border-primary/20 transition-colors"
                >
                  <Eye size={13} /> View Audit
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
