import { create } from 'zustand'

interface UIState {
  showSidebar: boolean
  showMembers: boolean
  wsStatus: 'connecting' | 'open' | 'closed'
  toast: { message: string; type: 'error' | 'success' } | null
  theme: string
  isSending: boolean
  isUploading: boolean
  uploadProgress: string
  setShowSidebar: (v: boolean) => void
  setShowMembers: (v: boolean) => void
  setWsStatus: (s: UIState['wsStatus']) => void
  showToast: (message: string, type: 'error' | 'success') => void
  hideToast: () => void
  setTheme: (t: string) => void
  setIsSending: (v: boolean) => void
  setIsUploading: (v: boolean) => void
  setUploadProgress: (v: string) => void
}

export const useUIStore = create<UIState>((set) => ({
  showSidebar: false,
  showMembers: false,
  wsStatus: 'closed',
  toast: null,
  theme: 'dark',
  isSending: false,
  isUploading: false,
  uploadProgress: '',
  setShowSidebar: (v) => set({ showSidebar: v }),
  setShowMembers: (v) => set({ showMembers: v }),
  setWsStatus: (s) => set({ wsStatus: s }),
  showToast: (message, type) => set({ toast: { message, type } }),
  hideToast: () => set({ toast: null }),
  setTheme: (t) => set({ theme: t }),
  setIsSending: (v) => set({ isSending: v }),
  setIsUploading: (v) => set({ isUploading: v }),
  setUploadProgress: (v) => set({ uploadProgress: v }),
}))
