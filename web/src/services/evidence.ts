import { request } from './api';
import { EvidenceMetadata } from '../types';

export const evidenceService = {
  async getDeviceEvidence(deviceId: string): Promise<EvidenceMetadata[]> {
    return request<EvidenceMetadata[]>(`/api/v1/evidence/${deviceId}`);
  },
};
