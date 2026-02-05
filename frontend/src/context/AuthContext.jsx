/**
 * Authentication Context
 * Manages authentication state using cookie-based authentication
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { userApi } from '../utils/api';
import { API_ENDPOINTS } from '../config/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch user profile from backend (uses cookies automatically)
  const fetchUserProfile = async () => {
    try {
      const response = await userApi.get(API_ENDPOINTS.USER_PROFILE);
      return response.data;
    } catch (err) {
      // 401 means not authenticated (cookie invalid/missing)
      if (err.response && err.response.status === 401) {
        return null;
      }
      // For other errors, throw to let caller handle
      console.error('Error fetching profile:', err);
      throw err;
    }
  };

  // Check authentication by trying to fetch profile
  const checkAuth = async () => {
    try {
      const userData = await fetchUserProfile();
      if (userData) {
        setUser({ ...userData, authenticated: true });
      } else {
        setUser(null);
      }
    } catch (err) {
      // Network errors or other issues - assume not authenticated
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Check authentication on mount
    checkAuth();
  }, []);

  const login = async (userData) => {
    // Cookies are set automatically by backend
    // Immediately set user data for instant UI update
    setUser({ ...userData, authenticated: true });

    // Fetch full profile in background to ensure consistency
    try {
      const profileData = await fetchUserProfile();
      if (profileData) {
        setUser({ ...profileData, authenticated: true });
      }
    } catch (err) {
      // If profile fetch fails, keep userData from login
      console.warn('Failed to fetch user profile after login:', err);
    }
  };

  const logout = async () => {
    try {
      // Call logout endpoint to clear cookies on backend
      await userApi.post(API_ENDPOINTS.USER_LOGOUT);
    } catch (err) {
      // Ignore logout errors - clear local state anyway
      console.warn('Logout request failed:', err);
    } finally {
      // Clear local state
      setUser(null);
    }
  };

  const value = {
    user,
    isAuthenticated: !!user?.authenticated,
    isAdmin: !!user?.is_admin,
    login,
    logout,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
