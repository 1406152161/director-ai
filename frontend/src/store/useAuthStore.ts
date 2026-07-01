/**
 * @author zhangzhihao
 */
import { create } from 'zustand';

const TOKEN_KEY = 'director-ai-token';

/**
 * SECURITY NOTE:
 * JWT token 当前存储在 localStorage，存在 XSS 窃取风险。
 * 当前阶段（本地/演示）可接受，上线前需迁移至：
 * - 后端 /auth/login 返回 Set-Cookie（httpOnly + Secure + SameSite=Strict）
 * - 前端不再手动管理 token，改为 withCredentials: true 自动携带 cookie
 * - 添加 CSRF token 保护
 * TODO: 上线前完成 cookie 迁移
 */
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
