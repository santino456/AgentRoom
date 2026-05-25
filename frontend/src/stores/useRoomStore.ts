import { create } from 'zustand'
import { API_BASE } from '../config'
import type { Room, Member, AgentStatus } from '../types'

interface RoomState {
  rooms: Room[]
  currentRoomId: number | null
  members: Member[]
  agentStatus: Record<string, AgentStatus>
  unreadCounts: Record<number, number>
  loadRooms: () => Promise<void>
  selectRoom: (id: number) => void
  loadMembers: (roomId: number) => Promise<void>
  loadAgentStatus: (roomId: number) => Promise<void>
  loadUnreadCount: (roomId: number) => Promise<void>
}

export const useRoomStore = create<RoomState>((set) => ({
  rooms: [],
  currentRoomId: null,
  members: [],
  agentStatus: {},
  unreadCounts: {},

  loadRooms: async () => {
    try {
      const res = await fetch(`${API_BASE}/rooms`, { credentials: 'include' })
      const data = await res.json()
      set({ rooms: data })
    } catch (e) {
      console.error('Failed to load rooms:', e)
    }
  },

  selectRoom: (id) => set({ currentRoomId: id }),

  loadMembers: async (roomId) => {
    try {
      const res = await fetch(`${API_BASE}/rooms/${roomId}/members`, { credentials: 'include' })
      const data = await res.json()
      set({ members: data })
    } catch (e) {
      console.error('Failed to load members:', e)
    }
  },

  loadAgentStatus: async (roomId) => {
    try {
      const res = await fetch(`${API_BASE}/rooms/${roomId}/agent-status`, { credentials: 'include' })
      const data = await res.json()
      const statusMap: Record<string, AgentStatus> = {}
      data.forEach((s: any) => { statusMap[s.name] = s })
      set({ agentStatus: statusMap })
    } catch (e) {
      console.error('Failed to load agent status:', e)
    }
  },

  loadUnreadCount: async (roomId) => {
    try {
      const res = await fetch(`${API_BASE}/rooms/${roomId}/unread-count`, { credentials: 'include' })
      const data = await res.json()
      set((state) => ({ unreadCounts: { ...state.unreadCounts, [roomId]: data.count } }))
    } catch (e) {
      // Silently fail for unread count
    }
  },
}))
