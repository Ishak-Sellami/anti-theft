import { request } from './api';
import { CommandType, DeviceCommand } from '../types';

export const commandService = {
  async issueCommand(
    deviceId: string,
    commandType: CommandType,
    payload: Record<string, any> = {},
    ttlSeconds: number = 300
  ): Promise<DeviceCommand> {
    return request<DeviceCommand>('/api/v1/commands', {
      method: 'POST',
      body: JSON.stringify({
        device_id: deviceId,
        command_type: commandType,
        payload,
        ttl_seconds: ttlSeconds,
      }),
    });
  },

  async getPendingCommands(deviceId: string): Promise<DeviceCommand[]> {
    return request<DeviceCommand[]>(`/api/v1/commands/${deviceId}/pending`);
  },

  async getCommandHistory(deviceId: string): Promise<DeviceCommand[]> {
    return request<DeviceCommand[]>(`/api/v1/commands/${deviceId}`);
  },
};
