import { create } from 'zustand'
import { API_BASE } from '../config'
import type { Message } from '../types'

interface MessageState {
  messages: Message[]
  editingId: number | null
  searchQuery: string
  searchResults: Message[]
  isSearching: boolean
  setEditingId: (id: number | null) => void
  setSearchQuery: (q: string) => void
  loadMessages: (roomId: number, token?: string) => Promise<void>
  sendMessage: (roomId: number, content: string, token?: string) => Promise<void>
}

export const useMessageStore = create<MessageState>((set) => ({
  messages: [],
  editingId: null,
  searchQuery: '',
  searchResults: [],
  isSearching: false,

  setEditingId: (id) => set({ editingId: id }),
  setSearchQuery: (q) => set({ searchQuery: q }),

  loadMessages: async (roomId, token) => {
    try {
      const headers: Record<string, string> = {}
      if (token) headers['X-Member-Token'] = token
      const res = await fetch(`${API_BASE}/rooms/${roomId}/messages?limit=200`, {
        headers,
        credentials: 'include',
      })
      const data = await res.json()
      set({ messages: data })
    } catch (e) {
      console.error('Failed to load messages:', e)
    }
  },

  sendMessage: async (roomId, content, token) => {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (token) headers['X-Member-Token'] = token
    const res = await fetch(`${API_BASE}/rooms/${roomId}/messages`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ content }),
      credentials: 'include',
    })
    if (!res.ok) throw new Error(`Send failed: ${res.status}`)
  },
}))
