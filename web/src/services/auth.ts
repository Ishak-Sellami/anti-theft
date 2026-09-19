import { request } from './api';
import { AuthResponse, User } from '../types';

export const authService = {
  async login(email: string, password: string):Promise<AuthResponse> {
    const data = await request<AuthResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem('anti_sarika_token', data.access_token);
    localStorage.setItem('anti_sarika_user', JSON.stringify(data.user));
    return data;
  },

  async register(email: string, password: string, full_name: string, role: string = 'OWNER'): Promise<User> {
    return request<User>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name, role }),
    });
  },

  async getMe(): Promise<User> {
    return request<User>('/api/v1/auth/me');
  },

  logout() {
    localStorage.removeItem('anti_sarika_token');
    localStorage.removeItem('anti_sarika_user');
  },

  getCurrentUser(): User | null {
    const raw = localStorage.getItem('anti_sarika_user');
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  },

  getToken(): string | null {
    return localStorage.getItem('anti_sarika_token');
  }
};
