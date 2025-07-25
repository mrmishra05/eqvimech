import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../lib/api';

const AuthContext = createContext();

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
  const [error, setError] = useState(null);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await authApi.getCurrentUser();
      setUser(response.user);
    } catch (error) {
      // User not authenticated
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials) => {
    try {
      setError(null);
      const response = await authApi.login(credentials);
      setUser(response.user);
      return { success: true };
    } catch (error) {
      setError(error.message);
      return { success: false, error: error.message };
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
    }
  };

  const hasRole = (roles) => {
    if (!user) return false;
    if (Array.isArray(roles)) {
      return roles.includes(user.role);
    }
    return user.role === roles;
  };

  const canManageOrders = () => hasRole(['admin', 'operator']);
  const canManageCustomers = () => hasRole(['admin', 'operator']);
  const canManageProducts = () => hasRole(['admin', 'operator']);
  const canManageUsers = () => hasRole(['admin']);
  const canUpdatePayments = () => hasRole(['admin', 'accountant']);
  const canUpdateOrderStatus = () => hasRole(['admin', 'operator']);

  const value = {
    user,
    loading,
    error,
    login,
    logout,
    hasRole,
    canManageOrders,
    canManageCustomers,
    canManageProducts,
    canManageUsers,
    canUpdatePayments,
    canUpdateOrderStatus,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

