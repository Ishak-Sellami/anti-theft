import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { DeviceCard } from '../components/device/DeviceCard';
import { StateBadge } from '../components/device/StateBadge';
import { Device } from '../types';

const mockDevice: Device = {
  id: 'dev_12345',
  owner_id: 'usr_1',
  device_name: 'Pixel 8 Pro Test',
  device_model: 'GPJ41',
  os_version: 'Android 14 (API 34)',
  agent_version: '0.1.0',
  public_key_pem: '-----BEGIN PUBLIC KEY-----\nMIIB...==\n-----END PUBLIC KEY-----\n',
  public_key_fingerprint: 'a1b2c3d4e5f6789012345678abcdef0123456789abcdef0123456789abcdef01',
  security_state: 'STOLEN',
  connectivity_state: 'ONLINE',
  power_state: 'NORMAL',
  battery_level: 85,
  is_charging: false,
  last_known_latitude: 52.52,
  last_known_longitude: 13.405,
  last_known_accuracy: 5.0,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

describe('Device Components & State Tests', () => {
  it('renders 3D state badges accurately', () => {
    const { rerender } = render(<StateBadge type="security" value="NORMAL" />);
    expect(screen.getByText('NORMAL')).toBeInTheDocument();

    rerender(<StateBadge type="security" value="STOLEN" />);
    expect(screen.getByText('STOLEN')).toBeInTheDocument();

    rerender(<StateBadge type="connectivity" value="ONLINE" />);
    expect(screen.getByText('ONLINE')).toBeInTheDocument();

    rerender(<StateBadge type="power" value="CRITICAL" />);
    expect(screen.getByText('POWER: CRITICAL')).toBeInTheDocument();
  });

  it('renders device card with stolen indicator when in STOLEN mode', () => {
    render(
      <BrowserRouter>
        <DeviceCard device={mockDevice} />
      </BrowserRouter>
    );

    expect(screen.getByText('Pixel 8 Pro Test')).toBeInTheDocument();
    expect(screen.getByText(/ACTIVE THEFT INCIDENT DETECTED/i)).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByText(/52.5200, 13.4050/)).toBeInTheDocument();
  });
});
