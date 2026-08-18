import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import MainLayout from './components/layout/MainLayout';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import NewPARequest from './pages/NewPARequest';
import BatchQueue from './pages/BatchQueue';
import PAHistory from './pages/PAHistory';
import PAResult from './pages/PAResult';

/**
 * Public-only route wrapper: if provider is already logged in, redirect to Dashboard.
 */
function PublicLoginRoute() {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return null;
  return isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public Authentication Route */}
        <Route path="/login" element={<PublicLoginRoute />} />

        {/* Protected Enterprise Clinical Workspace */}
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="new-request" element={<NewPARequest />} />
            <Route path="queue" element={<BatchQueue />} />
            <Route path="history" element={<PAHistory />} />
            <Route path="pa/:id" element={<PAResult />} />
          </Route>
        </Route>

        {/* Catch-all route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
