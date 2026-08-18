import React, { createContext, useContext, useState, useEffect } from 'react';
import { AUTH_STORAGE_KEY, authenticateProvider } from '../utils/authConfig';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [provider, setProvider] = useState(null);
  const [loading, setLoading] = useState(true);

  // Initialize session on mount from storage
  useEffect(() => {
    try {
      const storedSession = localStorage.getItem(AUTH_STORAGE_KEY);
      if (storedSession) {
        const parsed = JSON.parse(storedSession);
        if (parsed && parsed.id && parsed.name) {
          setProvider(parsed);
        }
      }
    } catch (err) {
      console.warn('Failed to restore auth session:', err);
      localStorage.removeItem(AUTH_STORAGE_KEY);
    } finally {
      setLoading(false);
    }
  }, []);

  const login = async (username, password) => {
    const res = await authenticateProvider(username, password);
    if (res.success && res.provider) {
      setProvider(res.provider);
      try {
        localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(res.provider));
      } catch (err) {
        console.error('Failed to persist session to localStorage:', err);
      }
      return { success: true };
    }
    return { success: false, error: res.error };
  };

  const logout = () => {
    setProvider(null);
    try {
      localStorage.removeItem(AUTH_STORAGE_KEY);
    } catch (err) {
      console.error('Failed to remove auth session:', err);
    }
  };

  const value = {
    provider,
    isAuthenticated: !!provider,
    loading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
