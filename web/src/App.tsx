import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { Layout } from './components/layout/Layout';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { DeviceDetailPage } from './pages/DeviceDetailPage';
import { StolenRecoveryCenterPage } from './pages/StolenRecoveryCenterPage';
import { EvidenceCenterPage } from './pages/EvidenceCenterPage';
import { CommandsPage } from './pages/CommandsPage';
import { RecoveryPolicyPage } from './pages/RecoveryPolicyPage';
import { SecurityEventsPage } from './pages/SecurityEventsPage';
import { AuditTrailPage } from './pages/AuditTrailPage';
import { Spinner } from './components/common/Spinner';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="devices" element={<DashboardPage />} />
        <Route path="devices/:deviceId" element={<DeviceDetailPage />} />
        <Route path="stolen-center" element={<StolenRecoveryCenterPage />} />
        <Route path="evidence" element={<EvidenceCenterPage />} />
        <Route path="commands" element={<CommandsPage />} />
        <Route path="policies" element={<RecoveryPolicyPage />} />
        <Route path="events" element={<SecurityEventsPage />} />
        <Route path="audit" element={<AuditTrailPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};
