import { request } from './api';
import { SecurityEvent } from '../types';

export const eventService = {
  async getDeviceSecurityEvents(deviceId: string, limit: number = 50): Promise<SecurityEvent[]> {
    return request<SecurityEvent[]>(`/api/v1/events/${deviceId}?limit=${limit}`);
  },
};
