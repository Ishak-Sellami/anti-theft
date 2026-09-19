import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuth } from './AuthContext';
import { realtimeClient } from '../services/websocket';
import { WebSocketMessage } from '../types';

interface WebSocketContextType {
  status: 'CONNECTED' | 'CONNECTING' | 'DISCONNECTED';
  lastMessage: WebSocketMessage | null;
  subscribe: (handler: (msg: WebSocketMessage) => void) => () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, isAuthenticated } = useAuth();
  const [status, setStatus] = useState<'CONNECTED' | 'CONNECTING' | 'DISCONNECTED'>('DISCONNECTED');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  useEffect(() => {
    if (isAuthenticated && token) {
      realtimeClient.connect(token);
    } else {
      realtimeClient.disconnect();
    }

    const unsubStatus = realtimeClient.onStatusChange((newStatus) => {
      setStatus(newStatus);
    });

    const unsubMessage = realtimeClient.onMessage((msg) => {
      setLastMessage(msg);
    });

    return () => {
      unsubStatus();
      unsubMessage();
      realtimeClient.disconnect();
    };
  }, [isAuthenticated, token]);

  const subscribe = (handler: (msg: WebSocketMessage) => void) => {
    return realtimeClient.onMessage(handler);
  };

  return (
    <WebSocketContext.Provider value={{ status, lastMessage, subscribe }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) throw new Error('useWebSocket must be used within a WebSocketProvider');
  return context;
};
