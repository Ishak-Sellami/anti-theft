import { request } from './api';
import { LocationTelemetry } from '../types';

export const telemetryService = {
  async getTelemetryHistory(deviceId: string, limit: number = 100): Promise<LocationTelemetry[]> {
    return request<LocationTelemetry[]>(`/api/v1/telemetry/${deviceId}/history?limit=${limit}`);
  },
};
