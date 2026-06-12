/**
 * @author zhangzhihao
 */
import { create } from 'zustand';

interface CreationDraft {
  story: string;
  style: string;
  duration: number;
  aspectRatio: string;
}

interface AppState {
  draft: CreationDraft;
  setDraft: (partial: Partial<CreationDraft>) => void;
  resetDraft: () => void;
}

const defaultDraft: CreationDraft = {
  story: '',
  style: 'cinematic',
  duration: 30,
  aspectRatio: '16:9',
};

export const useAppStore = create<AppState>((set) => ({
  draft: defaultDraft,
  setDraft: (partial) => set((state) => ({ draft: { ...state.draft, ...partial } })),
  resetDraft: () => set({ draft: defaultDraft }),
}));
