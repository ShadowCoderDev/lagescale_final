import React, { createContext, useContext, useState, useEffect } from "react";
import { userApi } from "../utils/api";
import { API_ENDPOINTS } from "../config/api";

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchUserProfile = async () => {
    try {
      const response = await userApi.get(API_ENDPOINTS.USER_PROFILE);
      return response.data;
    } catch (err) {
      if (err.response && err.response.status === 401) {
        return null;
      }
      console.error("Error fetching profile:", err);
      throw err;
    }
  };

  const checkAuth = async () => {
    try {
      const userData = await fetchUserProfile();
      if (userData) {
        setUser({ ...userData, authenticated: true });
      } else {
        setUser(null);
      }
    } catch (err) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const login = async (userData) => {
    setUser({ ...userData, authenticated: true });

    try {
      const profileData = await fetchUserProfile();
      if (profileData) {
        setUser({ ...profileData, authenticated: true });
      }
    } catch (err) {
      console.warn("Failed to fetch user profile after login:", err);
    }
  };

  const logout = async () => {
    try {
      await userApi.post(API_ENDPOINTS.USER_LOGOUT);
    } catch (err) {
      console.warn("Logout request failed:", err);
    } finally {
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
