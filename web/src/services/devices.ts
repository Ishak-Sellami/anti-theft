import { request } from './api';
import { Device, EnrollmentInitiateResponse } from '../types';

export const deviceService = {
  async listDevices(): Promise<Device[]> {
    return request<Device[]>('/api/v1/devices');
  },

  async getDevice(deviceId: string): Promise<Device> {
    return request<Device>(`/api/v1/devices/${deviceId}`);
  },

  async initiateEnrollment(payload: {
    device_name: string;
    device_model?: string;
    os_version?: string;
  }): Promise<EnrollmentInitiateResponse> {
    return request<EnrollmentInitiateResponse>('/api/v1/devices/enroll/initiate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
