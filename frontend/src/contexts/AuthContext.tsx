import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User } from '../types';
import api from '../utils/api';
import { API_ENDPOINTS } from '../config/api';
import { message } from 'antd';

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  loading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = async () => {
    try {
      const response = await api.get(API_ENDPOINTS.CHECK_AUTH);
      if (response.data.authenticated) {
        setUser(response.data.user);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const response = await api.post(API_ENDPOINTS.LOGIN, {
        username,
        password,
      });
      
      if (response.data.user) {
        setUser(response.data.user);
        message.success('Login successful');
        return true;
      }
      return false;
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Login failed';
      message.error(errorMessage);
      return false;
    }
  };

  const logout = async () => {
    try {
      await api.post(API_ENDPOINTS.LOGOUT);
      setUser(null);
      message.success('Logged out successfully');
    } catch (error) {
      console.error('Logout failed:', error);
      setUser(null); // Force logout on error
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const value: AuthContextType = {
    user,
    login,
    logout,
    loading,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};