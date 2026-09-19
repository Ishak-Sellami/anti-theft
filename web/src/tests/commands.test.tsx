import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { CommandModal } from '../components/commands/CommandModal';
import { CommandHistoryTable } from '../components/commands/CommandHistoryTable';
import { commandService } from '../services/commands';
import { DeviceCommand } from '../types';

const mockCommands: DeviceCommand[] = [
  {
    id: 'cmd_1',
    device_id: 'dev_123',
    issued_by: 'usr_1',
    command_type: 'LOCK_DEVICE',
    nonce: 'cmd_nonce_123',
    status: 'EXECUTED',
    result_payload: { device_locked: 'true' },
    expires_at: new Date(Date.now() + 300000).toISOString(),
    signature: 'fake_sig',
    created_at: new Date().toISOString(),
  },
];

describe('Remote Command Engine Tests', () => {
  it('renders command history table accurately', () => {
    render(<CommandHistoryTable commands={mockCommands} />);
    expect(screen.getByText('LOCK_DEVICE')).toBeInTheDocument();
    expect(screen.getByText('EXECUTED')).toBeInTheDocument();
    expect(screen.getByText(/device_locked/)).toBeInTheDocument();
  });

  it('requires confirmation string when AUTHORIZE_WIPE command is chosen', async () => {
    const issueSpy = vi.spyOn(commandService, 'issueCommand').mockResolvedValue(mockCommands[0]);

    render(
      <CommandModal
        isOpen={true}
        onClose={() => {}}
        deviceId="dev_123"
        deviceName="Pixel 8 Pro"
        onSuccess={() => {}}
      />
    );

    // Select Authorize Remote Wipe
    fireEvent.click(screen.getByText(/Authorize Remote Wipe \(DPC\)/i));

    expect(screen.getByText(/DESTRUCTIVE ACTION WARNING/i)).toBeInTheDocument();

    // Submit without typing confirmation
    fireEvent.click(screen.getByText('Authorize Wipe'));

    expect(
      screen.getByText(/You must type CONFIRM WIPE exactly to authorize a remote factory wipe./i)
    ).toBeInTheDocument();
    expect(issueSpy).not.toHaveBeenCalled();

    // Type confirmation
    fireEvent.change(screen.getByPlaceholderText('CONFIRM WIPE'), {
      target: { value: 'CONFIRM WIPE' },
    });

    fireEvent.click(screen.getByText('Authorize Wipe'));

    await waitFor(() => {
      expect(issueSpy).toHaveBeenCalledWith(
        'dev_123',
        'AUTHORIZE_WIPE',
        {},
        300
      );
    });
  });
});
