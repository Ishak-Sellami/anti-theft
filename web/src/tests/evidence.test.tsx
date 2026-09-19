import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { EvidenceTable } from '../components/evidence/EvidenceTable';
import { EvidenceViewerModal } from '../components/evidence/EvidenceViewerModal';
import { EvidenceMetadata } from '../types';

const mockEvidence: EvidenceMetadata = {
  id: 'ev_001',
  device_id: 'dev_123',
  capture_type: 'AMBIENT_RF',
  integrity_hash: '3f786850e387550fdab836ed7e6dc881de23001b70e8707e7ef8d27ecb8fcf6b',
  storage_ref: 'local:///stolen_evidence_vault/ev_001.json',
  mime_type: 'application/json',
  file_size_bytes: '512',
  chain_of_custody_notes: 'Automated STOLEN periodic sweep',
  device_timestamp: new Date().toISOString(),
  received_at: new Date().toISOString(),
};

describe('Evidence Center & Integrity Tests', () => {
  it('renders evidence table with SHA-256 integrity hash snippets', () => {
    render(<EvidenceTable evidenceList={[mockEvidence]} onSelectEvidence={() => {}} />);

    expect(screen.getByText('AMBIENT_RF')).toBeInTheDocument();
    expect(screen.getByText(/3f786850e387550f/)).toBeInTheDocument();
    expect(screen.getByText(/View Audit/i)).toBeInTheDocument();
  });

  it('renders EvidenceViewerModal with full hash and chain of custody details', () => {
    render(<EvidenceViewerModal isOpen={true} onClose={() => {}} evidence={mockEvidence} />);

    expect(screen.getByText(/Cryptographic Integrity Verified/i)).toBeInTheDocument();
    expect(screen.getByText(mockEvidence.integrity_hash)).toBeInTheDocument();
    expect(screen.getByText(/local:\/\/\/stolen_evidence_vault\/ev_001\.json/)).toBeInTheDocument();
    expect(screen.getByText(/"Automated STOLEN periodic sweep"/)).toBeInTheDocument();
  });
});
