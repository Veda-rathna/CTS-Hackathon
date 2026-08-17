import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import Dashboard from './pages/Dashboard';
import NewPARequest from './pages/NewPARequest';
import BatchQueue from './pages/BatchQueue';
import PAHistory from './pages/PAHistory';
import PAResult from './pages/PAResult';
import Settings from './pages/Settings';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="new-request" element={<NewPARequest />} />
        <Route path="queue" element={<BatchQueue />} />
        <Route path="history" element={<PAHistory />} />
        <Route path="pa/:id" element={<PAResult />} />
        <Route path="settings" element={<Settings />} />
        {/* Catch-all redirect to Dashboard */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
