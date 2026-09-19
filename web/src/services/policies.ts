import { request } from './api';
import { RecoveryPolicy, RecoveryPolicyConfig } from '../types';

export const policyService = {
  async listPolicies(): Promise<RecoveryPolicy[]> {
    return request<RecoveryPolicy[]>('/api/v1/policies');
  },

  async getPolicy(policyId: string): Promise<RecoveryPolicy> {
    return request<RecoveryPolicy>(`/api/v1/policies/${policyId}`);
  },

  async createPolicy(policy: {
    policy_id: string;
    name: string;
    security_state: string;
    config: RecoveryPolicyConfig;
  }): Promise<RecoveryPolicy> {
    return request<RecoveryPolicy>('/api/v1/policies', {
      method: 'POST',
      body: JSON.stringify(policy),
    });
  },

  async updatePolicy(policyId: string, payload: {
    name?: string;
    config: RecoveryPolicyConfig;
  }): Promise<RecoveryPolicy> {
    return request<RecoveryPolicy>(`/api/v1/policies/${policyId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },
};
