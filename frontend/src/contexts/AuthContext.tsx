import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import apiClient from '../services/api';

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    const username = localStorage.getItem('username');
    if (token && username) {
      setUser({ username, role: 'admin', token });
    }
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const data = await apiClient.login(username, password);
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('username', username);
      setUser({ username, role: data.role || 'admin', token: data.access_token });
    } catch (error) {
      throw new Error('Login failed');
    }
  };

  const logout = () => {
    apiClient.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
