import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import MainLayout from './components/Layout/MainLayout';
import Login from './components/Login';
import Dashboard from './components/Dashboard/Dashboard';
import ProviderList from './components/Providers/ProviderList';
import ContentGeneration from './components/ContentGeneration/ContentGeneration';
import WordPressSync from './components/Sync/WordPressSync';
import AddProviders from './components/AddProviders/AddProviders';
import Settings from './components/Settings/Settings';
import DataQuality from './components/DataQuality/DataQuality';
import ActivityLog from './components/ActivityLog/ActivityLog';
import LoginTest from './components/LoginTest';
import './App.css';

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// Main App Routes
const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/test" element={<LoginTest />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="providers" element={<ProviderList />} />
        <Route path="add-providers" element={<AddProviders />} />
        <Route path="content" element={<ContentGeneration />} />
        <Route path="sync" element={<WordPressSync />} />
        <Route path="data-quality" element={<DataQuality />} />
        <Route path="activity-log" element={<ActivityLog />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

function App() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 6,
        },
      }}
    >
      <Router>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </Router>
    </ConfigProvider>
  );
}

export default App;
