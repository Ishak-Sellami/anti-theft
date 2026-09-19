import { request } from './api';
import { AuditLog } from '../types';

export const auditService = {
  async listSystemAuditLogs(limit: number = 100): Promise<AuditLog[]> {
    return request<AuditLog[]>(`/api/v1/audit?limit=${limit}`);
  },

  async getDeviceAuditLogs(deviceId: string, limit: number = 50): Promise<AuditLog[]> {
    return request<AuditLog[]>(`/api/v1/audit/device/${deviceId}?limit=${limit}`);
  },
};
