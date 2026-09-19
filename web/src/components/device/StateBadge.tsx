import React from 'react';
import { SecurityState, ConnectivityState, PowerState } from '../../types';
import { Badge } from '../common/Badge';

interface StateBadgeProps {
  type: 'security' | 'connectivity' | 'power';
  value: SecurityState | ConnectivityState | PowerState | string;
  size?: 'sm' | 'md';
}

export const StateBadge: React.FC<StateBadgeProps> = ({ type, value, size = 'sm' }) => {
  if (type === 'security') {
    switch (value) {
      case 'NORMAL':
        return <Badge variant="success" size={size}>NORMAL</Badge>;
      case 'PROTECTED':
        return <Badge variant="info" size={size}>PROTECTED</Badge>;
      case 'STOLEN':
        return <Badge variant="danger" size={size} className="animate-pulse font-bold">STOLEN</Badge>;
      case 'RECOVERY':
        return <Badge variant="warning" size={size}>RECOVERY</Badge>;
      default:
        return <Badge variant="default" size={size}>{value}</Badge>;
    }
  }

  if (type === 'connectivity') {
    switch (value) {
      case 'ONLINE':
        return <Badge variant="success" size={size}>ONLINE</Badge>;
      case 'DEGRADED':
        return <Badge variant="warning" size={size}>DEGRADED</Badge>;
      case 'OFFLINE':
        return <Badge variant="default" size={size}>OFFLINE</Badge>;
      default:
        return <Badge variant="default" size={size}>{value}</Badge>;
    }
  }

  if (type === 'power') {
    switch (value) {
      case 'NORMAL':
        return <Badge variant="success" size={size}>POWER: OK</Badge>;
      case 'LOW':
        return <Badge variant="warning" size={size}>POWER: LOW</Badge>;
      case 'CRITICAL':
        return <Badge variant="danger" size={size}>POWER: CRITICAL</Badge>;
      default:
        return <Badge variant="default" size={size}>{value}</Badge>;
    }
  }

  return <Badge variant="default" size={size}>{value}</Badge>;
};
