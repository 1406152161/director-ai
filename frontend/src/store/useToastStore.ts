/**
 * @author zhangzhihao
 */
import { create } from 'zustand';

export type ToastType = 'error' | 'success' | 'warning' | 'info';

export interface ToastItem {
  id: string;
  type: ToastType;
  message: string;
  leaving?: boolean;
}

interface ToastStore {
  toasts: ToastItem[];
  showToast: (type: ToastType, message: string) => void;
  dismissToast: (id: string) => void;
}

let toastSeq = 0;
const TOAST_DURATION_MS = 3000;
const TOAST_FADE_MS = 200;

function scheduleDismiss(
  set: (fn: (state: ToastStore) => Partial<ToastStore>) => void,
  id: string,
  delayMs: number,
) {
  window.setTimeout(() => {
    set((state) => ({
      toasts: state.toasts.map((t) => (t.id === id ? { ...t, leaving: true } : t)),
    }));
    window.setTimeout(() => {
      set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
    }, TOAST_FADE_MS);
  }, delayMs);
}

/** 全局 Toast：3 秒自动消失，关闭时 fade-out。 */
export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  showToast: (type, message) => {
    const id = `toast-${++toastSeq}-${Date.now()}`;
    set((state) => ({ toasts: [...state.toasts, { id, type, message }] }));
    scheduleDismiss(set, id, TOAST_DURATION_MS);
  },
  dismissToast: (id) => scheduleDismiss(set, id, 0),
}));
