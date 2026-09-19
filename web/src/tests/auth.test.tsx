import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { LoginPage } from '../pages/LoginPage';
import { authService } from '../services/auth';

const TestAuthConsumer = () => {
  const { user, isAuthenticated, logout } = useAuth();
  return (
    <div>
      <div data-testid="auth-status">{isAuthenticated ? 'LOGGED_IN' : 'LOGGED_OUT'}</div>
      <div data-testid="user-email">{user?.email || 'NONE'}</div>
      <button onClick={logout} data-testid="logout-btn">
        Logout
      </button>
    </div>
  );
};

describe('Authentication & Session Tests', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('renders login page correctly with email and password inputs', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByText(/Owner Authentication/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('owner@example.com')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('••••••••••••')).toBeInTheDocument();
  });

  it('handles login and updates auth context reactive state', async () => {
    vi.spyOn(authService, 'login').mockResolvedValue({
      access_token: 'fake_jwt_token_123',
      token_type: 'bearer',
      user: {
        id: 'usr_1',
        email: 'owner@example.com',
        full_name: 'Test Owner',
        role: 'OWNER',
        is_active: true,
        created_at: new Date().toISOString(),
      },
    });

    render(
      <BrowserRouter>
        <AuthProvider>
          <LoginPage />
          <TestAuthConsumer />
        </AuthProvider>
      </BrowserRouter>
    );

    fireEvent.change(screen.getByPlaceholderText('owner@example.com'), {
      target: { value: 'owner@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText('••••••••••••'), {
      target: { value: 'SecretPassword123!' },
    });

    fireEvent.click(screen.getByText(/Sign In to Control Plane/i));

    await waitFor(() => {
      expect(screen.getByTestId('auth-status').textContent).toBe('LOGGED_IN');
      expect(screen.getByTestId('user-email').textContent).toBe('owner@example.com');
    });

    // Test logout
    fireEvent.click(screen.getByTestId('logout-btn'));
    expect(screen.getByTestId('auth-status').textContent).toBe('LOGGED_OUT');
  });
});
