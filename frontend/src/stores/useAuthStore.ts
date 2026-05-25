import { create } from 'zustand'

interface AuthState {
  memberToken: string
  memberName: string
  setAuth: (token: string, name: string) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  memberToken: '',
  memberName: '',
  setAuth: (token, name) => set({ memberToken: token, memberName: name }),
  clearAuth: () => set({ memberToken: '', memberName: '' }),
}))
