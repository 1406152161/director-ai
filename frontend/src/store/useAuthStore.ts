/**
 * @author zhangzhihao
 */
import { create } from 'zustand';

const TOKEN_KEY = 'director-ai-token';

export interface AuthUser {
  id: string;
  email: string;
  display_name: string;
  tenant_id: string;
  tenant_name: string;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  authEnabled: boolean;
  setSession: (token: string, user: AuthUser) => void;
  clearSession: () => void;
  setAuthEnabled: (enabled: boolean) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem(TOKEN_KEY),
  user: null,
  authEnabled: false,
  setSession: (token, user) => {
    localStorage.setItem(TOKEN_KEY, token);
    set({ token, user });
  },
  clearSession: () => {
    localStorage.removeItem(TOKEN_KEY);
    set({ token: null, user: null });
  },
  setAuthEnabled: (enabled) => set({ authEnabled: enabled }),
}));

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
