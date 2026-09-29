import React, { createContext, useContext, useState, useEffect } from 'react';
import { getMe } from '../api';

interface User { id: number; name: string; email: string; role: string; }
interface AuthCtx { user: User | null; token: string | null; login: (token: string) => Promise<void>; logout: () => void; }

const AuthContext = createContext<AuthCtx>({} as AuthCtx);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));

  const loadUser = async (t: string) => {
    localStorage.setItem('token', t);
    setToken(t);
    try { const res = await getMe(); setUser(res.data); } catch { logout(); }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null); setUser(null);
  };

  useEffect(() => { if (token && !user) loadUser(token); }, []);

  return <AuthContext.Provider value={{ user, token, login: loadUser, logout }}>{children}</AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext);
